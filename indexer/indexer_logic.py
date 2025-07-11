from bs4 import BeautifulSoup
from bs4.element import Tag
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.logger import logger
from tqdm import tqdm

"""
this function take the entry from the unprocessed pages in the database ( url, html_content )
"""
def process_batch_with_tfidf(html_batch):
    # Phase 1: Extract text and maintain URL mapping
    all_texts = []
    url_mapping = {}
    vectorizer = TfidfVectorizer(stop_words='english')

    # get all words from each document, mapping the words to their specific url
    for i, entry in enumerate(html_batch):
        soup = BeautifulSoup(entry["html_content"], 'html.parser')
        text = soup.get_text(separator=" ")
        all_texts.append(text)
        url_mapping[i] = entry["url"]
    
    # calculate TF-IDF across all documents
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    feature_names = vectorizer.get_feature_names_out()
    
    # process each document with URL tracking
    all_word_scores = []
    
    for doc_index in tqdm(range(len(html_batch)), desc="Ranking Documents", bar_format="{l_bar}{bar} [time elapsed: {elapsed}]"):
        url = url_mapping[doc_index]
        scores = tfidf_matrix.toarray()[doc_index] #type: ignore
        
        # collect words for this specific URL
        word_scores = []
        for word, score in zip(feature_names, scores):
            if score > 0:
                word_scores.append({
                    "word": word, 
                    "url": url,
                    "weight": float(score)
                })
        
        # sort by weight and store
        word_scores.sort(key=lambda x: x["weight"], reverse=True)
        all_word_scores.extend(word_scores)
    
    return all_word_scores

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