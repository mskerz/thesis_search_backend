from collections import Counter
import time
from decimal import Decimal
import math
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, or_
from config.db_connect import Session, get_db
from model.advisor import AdvisorForm, Advisors, Advisor
from middleware.authentication import get_current_user
from model.user import User
from model.thesis import Term, ThesisDocument
from pythainlp.tokenize import word_tokenize
from math import log
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.preprocess import perform_removal,get_customDict

search_router = APIRouter()


def calculate_tf(term_freq: int, total_terms: int) -> float:
    return Decimal(term_freq / total_terms)


def calculate_idf(doc_count: int, doc_freq: int) -> float:

    return Decimal(log((doc_count) / (doc_freq)))




@search_router.get('/simple-search/{field}/{keyword}', tags=['Search'])
async def simple_search(field: str, keyword: str, db: Session = Depends(get_db)):
    """
    Search thesis documents by field and query.

    Args:
        field (str): The field to search (title_th, author_name, advisor_name, year).
        query (str): The query string to match.
        current_user (User): The current authenticated user. Automatically provided by the dependency.
        db (Session): The database session. Automatically provided by the dependency.

    Returns:
        List[ThesisList]: The list of matching thesis documents.

    Raises:
        HTTPException: If the field is not valid or no results are found.
    """
    # Base query for rechecked documents
    base_query = db.query(ThesisDocument).filter(
        ThesisDocument.recheck_status == 1)
    # Search logic
    if field == 'title_th':
        results = base_query.filter(
            ThesisDocument.title_th.ilike(f"%{keyword}%")).all()
    elif field == 'title_en':
        results = base_query.filter(
            ThesisDocument.title_en.ilike(f"%{keyword}%")).all()
    elif field == 'author_name':
        results = base_query.join(User, User.user_id == ThesisDocument.user_id).filter(
            or_(User.firstname.like(f"%{keyword}%"),
                User.lastname.ilike(f"%{keyword}%"))
        ).all()
    elif field == 'advisor_name':
        results = base_query.join(Advisor, Advisor.advisor_id == ThesisDocument.advisor_id).filter(
            Advisor.advisor_name.ilike(f"%{keyword}%")).all()
    elif field == 'year':
        results = base_query.filter(
            ThesisDocument.year.ilike(f"%{keyword}%")).all()
    if not results:
        return {"message": "No matching thesis documents found", "status": 404}

    search_result = []
    for doc in results:
        user = db.query(User).filter(User.user_id == doc.user_id).first()
        if not user:
            continue
        advisor = db.query(Advisor).filter(
            Advisor.advisor_id == doc.advisor_id).first()

        search_result.append({
            "doc_id": doc.doc_id,
            "title_th": doc.title_th,
            "title_en": doc.title_en,
            "author_name": f"{user.firstname} {user.lastname}",
            "advisor_name": advisor.advisor_name,
            "year": doc.year
        }
        )

    return {"message": "OK", "status": 200, "results": search_result}


@search_router.get('/advanced-search', tags=['Search'])
async def advanced_search(query: str, db: Session = Depends(get_db)):
    """
    Advanced search for thesis documents using TF-IDF.

    Args:
        query (str): The search query.
        current_user (User): The current authenticated user. Automatically provided by the dependency.
        db (Session): The database session. Automatically provided by the dependency.

    Returns:
        List[ThesisList]: The list of matching thesis documents with TF-IDF scores.

    Raises:
        HTTPException: If no results are found.
    """

    start_time = time.time()
    # Tokenize the query
    custom_dicts = get_customDict()

    # Tokenize the query and remove stop words
    query_seg = word_tokenize(query, custom_dict=custom_dicts, keep_whitespace=False, engine='newmm')
    query_seg = list(map(perform_removal, query_seg))  # Remove unwanted terms (stop words, etc.)
    filtered_query_terms = list(filter(lambda word: word != '', query_seg))  # Filter out empty strings

    # Remove duplicate terms and sort based on the original query order
    query_terms = list(set(filtered_query_terms))  # Remove duplicate terms

    # For sorting query terms based on their first occurrence in the original tokenized list
    query_terms = sorted(query_terms, key=lambda x: query_seg.index(x) if x in query_seg else float('inf'))

    # Get all thesis documents that have been rechecked (recheck_status = 1)
    documents = db.query(ThesisDocument).filter(
        ThesisDocument.recheck_status == 1).all()

    if not documents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No matching thesis documents found")

    # Calculate IDF for each query term
    total_docs = len(documents)
    idf = {}
    for term in query_terms:
        doc_count = db.query(Term).filter(Term.term == term).distinct(Term.doc_id).count()
        idf[term] = math.log((total_docs + 1) / (doc_count + 1)) + 1

    search_results = []

    for doc in documents:
        # Get the term frequencies for the current document
        terms = db.query(Term).filter(Term.doc_id == doc.doc_id).all()
        term_freq = {term.term: term.frequency for term in terms}

        # Calculate TF-IDF score for the current document
        tf_idf_score = 0.0
        for term in query_terms:
            tf = term_freq.get(term, 0) / sum(term_freq.values())
            tf_idf_score += tf * idf.get(term, 0)

        if tf_idf_score > 0:
            user = db.query(User).filter(User.user_id == doc.user_id).first()
            advisor = db.query(Advisor).filter(
                Advisor.advisor_id == doc.advisor_id).first()
            search_results.append({
                "doc_id": doc.doc_id,
                "title_th": doc.title_th,
                "author_name": f"{user.firstname} {user.lastname}",
                "advisor_name": advisor.advisor_name if advisor else "N/A",
                "year": doc.year,
                "tf_idf_score": tf_idf_score
            })

    # Sort results by TF-IDF score in descending order
    search_results.sort(key=lambda x: x.get('tf_idf_score', 0), reverse=True)

    if not search_results:
        return {"message": "Search Not Found ", "status": 404,"results": search_results}

    elapsed_time = time.time() - start_time

    return {"message": "OK", "status": 200,"time_used":elapsed_time,"query_terms": query_terms, "results": search_results}


# ยังไม่เสร็จ
@search_router.get('/user/advanced_search_v1', tags=['Search'])
async def advanced_search_v1(search_query: str, db: Session = Depends(get_db)):
    """
    Advanced search for thesis documents using TF-IDF and cosine similarity.

    Args:
        search_query (str): The search query.
        current_user (User): The current authenticated user. Automatically provided by the dependency.
        db (Session): The database session. Automatically provided by the dependency.

    Returns:
        List[ThesisList]: The list of matching thesis documents with TF-IDF scores.

    Raises:
        HTTPException: If no results are found.
    """

    start_time = time.time()

    # Get all thesis documents that have been rechecked (recheck_status = 1)
    documents = db.query(ThesisDocument).filter(
        ThesisDocument.recheck_status == 1).all()

    if not documents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No matching thesis documents found")

    # Prepare data for TF-IDF vectorizer
    doc_texts = []
    doc_metadata = []
    for doc in documents:
        terms = db.query(Term).filter(Term.doc_id == doc.doc_id).all()
        text = ' '.join([term.term for term in terms])
        doc_texts.append(text)
        user = db.query(User).filter(User.user_id == doc.user_id).first()
        advisor = db.query(Advisor).filter(
            Advisor.advisor_id == doc.advisor_id).first()
        doc_metadata.append({
            "doc_id": doc.doc_id,
            "title_th": doc.title_th,
            "author_name": f"{user.firstname} {user.lastname}",
            "advisor_name": advisor.advisor_name if advisor else "N/A",
            "year": doc.year
        })

    # Vectorize the document texts
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_vector = tfidf_vectorizer.fit_transform(doc_texts)

    # Tokenize the query
    query_seg = word_tokenize(search_query, keep_whitespace=False)
    query_text = ' '.join(query_seg)
    query_vector = tfidf_vectorizer.transform([query_text])

    # Calculate cosine similarity
    similarities = cosine_similarity(tfidf_vector, query_vector).flatten()

    # Combine metadata with similarities
    for i, meta in enumerate(doc_metadata):
        meta['tf_idf_score'] = similarities[i]

    # Filter and sort results by TF-IDF score
    search_results = [
        meta for meta in doc_metadata if meta['tf_idf_score'] > 0]
    search_results.sort(key=lambda x: x['tf_idf_score'], reverse=True)

    if not search_results:
        return {"message": "Search Not Found ", "status": 404,"results": search_results}

    elapsed_time = time.time() - start_time

    return {"message": "OK", "status": 200,"time_used":elapsed_time , "results": search_results}
