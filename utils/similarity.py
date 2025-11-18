"""Module for checking text similarity with improved semantic accuracy using Transformers."""

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import nltk
import pandas as pd
import re
# from difflib import SequenceMatcher
# from sklearn.feature_extraction.text import TfidfVectorizer

from utils import webcrawler

# Download NLTK data only once
# nltk.download("stopwords")
# nltk.download("punkt")
stop_words = set(nltk.corpus.stopwords.words("english"))

# "all-mpnet-base-v2" (alternate model)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def purify_text(string: str) -> str:
    """Clean text by removing stopwords and normalizing case, but keep sentence delimiters."""
    string = string.lower()
    string = re.sub(r"[^a-z\s\.\?\!]", "", string)
    words = nltk.word_tokenize(string)
    return " ".join([word for word in words if word not in stop_words])


def web_verify(text: str, results_per_sentence: int = 2, chunk_size: int = 5, max_urls: int = 25) -> list:
    """Fetch potential matching websites for the given text.
    If the text is long, chunk sentences together (chunk_size) instead of searching one sentence at a time.
    """
    sentences = nltk.sent_tokenize(text)
    matching_sites = set()

    # Search for the entire text first
    for url in webcrawler.search(query=text, num=results_per_sentence):
        matching_sites.add(url)
    if len(matching_sites) >= max_urls:
        print(f"Total unique URLs found: {len(matching_sites)}")
        return list(matching_sites)[:max_urls]

    #if the text is short, search sentence-by-sentence
    if len(sentences) <= chunk_size:
        iterable = sentences
    else:
        #creating non-overlapping chunks of sentences
        iterable = []
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i : i + chunk_size])
            iterable.append(chunk)

    for piece in iterable:
        for url in webcrawler.search(query=piece, num=results_per_sentence):
            matching_sites.add(url)
        if len(matching_sites) >= max_urls:
            break

    print(f"Total unique URLs found: {len(matching_sites)}")
    return list(matching_sites)[:max_urls]

# def tfidf_similarity(text1: str, text2: str) -> float:
#     """Compute semantic similarity between two texts using TF-IDF cosine similarity."""
#     if not text1.strip() or not text2.strip():
#         return 0.0

#     vectorizer = TfidfVectorizer().fit([text1, text2])
#     vectors = vectorizer.transform([text1, text2])
#     score = cosine_similarity(vectors[0], vectors[1])[0][0]
#     return round(score * 100, 2)

def transformer_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity between two texts using transformer embeddings."""
    if not text1.strip() or not text2.strip():
        return 0.0

    embeddings = model.encode([text1, text2], convert_to_tensor=False)
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score) * 100, 2)


def report(text: str) -> dict:
    """Generate a semantic similarity report comparing text against online sources."""
    purified_text = purify_text(text)
    matching_sites = web_verify(purified_text, results_per_sentence=3)
    matches = {}

    for url in matching_sites:
        try:
            site_text = webcrawler.extract_text(url)
            site_text = purify_text(site_text)
            score = transformer_similarity(purified_text, site_text)
            if score > 0:
                matches[url] = score
        except Exception as e:
            print(f"[!] Error processing {url}: {e}")
            continue

    # Sort by similarity descending
    return dict(sorted(matches.items(), key=lambda item: item[1], reverse=True))


def return_table(dictionary: dict) -> str:
    """Convert results to an HTML table for display with clickable URLs."""
    if not dictionary:
        return "<p>No matching sites found or insufficient similarity.</p>"

    df = pd.DataFrame(list(dictionary.items()), columns=["URL", "Similarity (%)"])
    df["URL"] = df["URL"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
    return df.to_html(index=False, justify="center", border=1, escape=False)
