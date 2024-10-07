import math


class Efficient:
    def __init__(self, search_results, k:int):
        """
        Initialize the Efficient class.
        Args:
            search_results (list): The list of search results with relevance scores (e.g. TF-IDF scores).
            k (int): The number of top results to consider for evaluation (default is 10).
        """
        self.search_results = search_results
        self.k_value = k

    def calculate_precision(self):
        """
        Calculate the precision of the search results.
        Returns:
            float: The precision value.
        """
        retrel = sum(1 for result in self.search_results[:self.k_value] if result.get('relevant', False))
        retnrel = self.k_value - retrel  # Total retrieved minus relevant retrieved
        
        # Avoid division by zero
        if (retrel + retnrel) == 0:
            return 0.0
        precision = retrel / (retrel + retnrel)
        return precision

    def calculate_r_precision(self, r):
        """
        Calculate R-Precision (Precision@r) for the search results.
        R-Precision = (Number of relevant documents in top-r) / (r)
        Args:
            r (int): The number of documents to consider for R-Precision.
        Returns:
            float: The R-Precision value.
        """
        relevant_docs = [res for res in self.search_results[:r] if res['tf_idf_score'] > 0]
        r_precision = len(relevant_docs) / r
        return r_precision

    def calculate_ndcg(self):
        """
        Calculate nDCG (Normalized Discounted Cumulative Gain) for the top-k search results.
        nDCG = DCG / IDCG
        Returns:
            float: The nDCG value.
        """
        def dcg(results):
            return sum([(2 ** res['tf_idf_score'] - 1) / math.log2(idx + 2) for idx, res in enumerate(results)])

        # DCG for actual results
        dcg_value = dcg(self.search_results[:self.k_value])

        # Ideal results sorted by highest relevance (assuming ideal ranking is the same as tf_idf_score)
        ideal_results = sorted(self.search_results[:self.k_value], key=lambda x: x['tf_idf_score'], reverse=True)
        idcg_value = dcg(ideal_results)

        # nDCG = DCG / IDCG
        if idcg_value == 0:
            return 0
        return dcg_value / idcg_value

    def evaluate(self):
        """
        Evaluate the search results by calculating Precision, R-Precision, and nDCG.
        Returns:
            dict: A dictionary containing Precision, R-Precision, and nDCG values.
        """
        precision = self.calculate_precision()
        r_precision = self.calculate_r_precision(self.k_value)
        ndcg = self.calculate_ndcg()
        
        return {
            "precision": precision,
            "r_precision": r_precision,
            "nDCG": ndcg
        }
