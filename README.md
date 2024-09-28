# Thesis Search System

This Senior project is a theses search system for Computer Science students. It provides functionalities like document indexing, TF-IDF-based search, and user account management. 

## System Scope

### 1. Searching
- **Simple Search**: String Matching.
- **Advanced Search**: TF-IDF (Term Frequency-Inverse Document Frequency) based search.

### 2. Indexing
- **Parsing**: Extracts text from document files.
- **Tokenization**: Splits text into tokens (words/phrases).
- **Stop Word Removal**: Removes unnecessary words and whitespace.

### 3. Scoring
- **Term Frequency (TF)**: Measures word frequency within a document.
- **Inverse Document Frequency (IDF)**: Measures word importance across all documents.
- **TF-IDF**: Calculates word importance for search.

### 4. Ranking
Results are ranked based on their TF-IDF scores to provide the most relevant results to the user.

### 5. User Account Management
- Sign-up
- Log-in/Log-out
- Edit Profile
- Change Password
- Reset Password

## Tech Stack - Backend 
[![Frontend](https://skillicons.dev/icons?i=fastapi,mysql)](https://github.com/mskerz/thesis_search_backend)



## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mskerz/thesis_search_backend.git
   cd thesis_search_backend

2. Create and activate a virtual environment (isolating dependencies within the project):
   - For Window
     ```bash
     python -m venv venv
     venv\Scripts\activate
     
   - For Linux/MacOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
3. Install dependencies (these will be installed in the virtual environment):
   ```bash
   pip install -r requirements.txt

4. Run the server: 
   ```bash
   uvicorn main:app --reload
   




