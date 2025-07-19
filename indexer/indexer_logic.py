from bs4 import BeautifulSoup
from bs4.element import Tag
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from utils.logger import logger
from tqdm import tqdm
from database.db import get_global_document_frequency, get_total_documents_count
import math
import numpy as np

def process_batch_with_tfidf(html_batch):
    """
    Processes a batch of HTML documents to compute global TF-IDF scores for each word in each document.

    This function is designed to update the TF-IDF (Term Frequency-Inverse Document Frequency) representation
    of a batch of HTML pages, taking into account both the current batch and all previously indexed documents.
    It does this by:
      1. Retrieving the global document frequency (DF) for each word from the database, and the total number of
         documents already indexed.
      2. Extracting plain text from each HTML document in the batch.
      3. Using scikit-learn's TfidfVectorizer to compute the term frequencies (TF) and vocabulary for the batch.
      4. For each word in the batch, calculating a custom global IDF value using the sum of its DF in the global
         index and in the current batch, and the total number of documents (existing + batch).
      5. Overriding the vectorizer's IDF values with these custom global IDFs.
      6. Recomputing the TF-IDF matrix for the batch using the custom global IDFs.
      7. For each document, extracting the nonzero TF-IDF scores for each word, and returning a list of dictionaries
         containing the word, the document's URL, and the TF-IDF weight.

    Args:
        html_batch (list): List of dicts, each with keys "html_content" (str) and "url" (str).

    Returns:
        list: List of dicts, each with keys "word", "url", and "weight" (float), sorted by weight per document.
    """
    
    global_doc_freq = get_global_document_frequency()
    total_existing_docs = get_total_documents_count()
    
    all_texts = []
    url_mapping = {}
    
    # Get the text from each url and map it to the corresponding url 
    for i, entry in enumerate(html_batch):
        soup = BeautifulSoup(entry["html_content"], 'html.parser')
        page_text = soup.get_text(separator=" ")
        all_texts.append(page_text)
        url_mapping[i] = entry["url"]
    
    vectorizer = TfidfVectorizer(stop_words='english', min_df=1)
    
    # Fit on current batch to get vocabulary
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    unique_words_in_current_batch = vectorizer.get_feature_names_out()
    
    # Override IDF with global values
    current_batch_size = len(html_batch)
    total_docs = total_existing_docs + current_batch_size
    
    # Calculate custom IDF values using global document frequency
    custom_idf = []
    for word in tqdm(unique_words_in_current_batch, desc="Calculating custom IDF", bar_format="{l_bar}{bar} [time elapsed: {elapsed}]"):
        global_df = global_doc_freq.get(word, 0)

        # doc freq in current batch
        batch_df = sum(
            1 for doc_idx in range(current_batch_size)
            if tfidf_matrix[doc_idx, vectorizer.vocabulary_[word]] > 0  # type: ignore
        )

        total_df = global_df + batch_df
        
        if total_df > 0:
            idf = math.log(total_docs / total_df)
        else:
            idf = 0
        custom_idf.append(idf)
    
    # Apply custom IDF to the vectorizer
    vectorizer.idf_ = np.array(custom_idf, dtype=np.float64)
    
    # Transform again with custom IDF
    tfidf_matrix = vectorizer.transform(all_texts)
    
    # Extract scores
    all_word_scores = []
    for doc_index in tqdm(range(len(html_batch)), desc="Calculating Global TF-IDF", bar_format="{l_bar}{bar} [time elapsed: {elapsed}]"):
        url = url_mapping[doc_index]
        scores = tfidf_matrix.toarray()[doc_index]  # type: ignore
        
        word_scores = []
        for word, score in zip(unique_words_in_current_batch, scores):
            if score > 0:
                word_scores.append({
                    "word": word, 
                    "url": url,
                    "weight": float(score)
                })
        
        word_scores.sort(key=lambda x: x["weight"], reverse=True)
        all_word_scores.extend(word_scores)
    
    logger.info(f"Generated {len(all_word_scores)} word scores using global document frequency")
    return all_word_scores

#TODO: implement an images service that will be used to crawl the visited_urls and gather the imgs
#      and these imgs can be linked to the url, so when returning the proper urls in the client, we can 
#      also display the proper imgs
def extract_page_images(html_content: str) -> list:
    image_src = []
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img')

    for image in images:
        if isinstance(image, Tag):
            src = image.get('src')
            if src:
                image_src.append(src)
    
    return image_src