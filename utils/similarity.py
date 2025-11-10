"""Module for checking text similarity with improved accuracy."""

# from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import nltk
import pandas as pd
import re

from utils import webcrawler

# Download NLTK data only once
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
stop_words = set(nltk.corpus.stopwords.words("english"))

def purify_text(string: str) -> str:
    """Clean text by removing stopwords and normalizing case, but keep sentence delimiters."""
    string = string.lower()
    # Remove everything except letters, spaces, and sentence delimiters (.?!)
    string = re.sub(r"[^a-z\s\.\?\!]", "", string)
    words = nltk.word_tokenize(string)
    return " ".join([word for word in words if word not in stop_words])

def web_verify(text: str, results_per_sentence: int = 2) -> list:
    """Fetch potential matching websites for the given text."""
    sentences = nltk.sent_tokenize(text)
    matching_sites = set()

    # Search for entire text
    for url in webcrawler.search(query=text, num=results_per_sentence):
        matching_sites.add(url)

    # Search sentence-wise for better coverage
    for sentence in sentences:
        print(sentence)
        print("\n")
        for url in webcrawler.search(query=sentence, num=results_per_sentence):
            print(url)
            matching_sites.add(url)

    print(f"Total unique URLs found: {len(matching_sites)}")
    return list(matching_sites)


def tfidf_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity between two texts using TF-IDF cosine similarity."""
    if not text1.strip() or not text2.strip():
        return 0.0

    vectorizer = TfidfVectorizer().fit([text1, text2])
    vectors = vectorizer.transform([text1, text2])
    score = cosine_similarity(vectors[0], vectors[1])[0][0]
    return round(score * 100, 2)


def report(text: str) -> dict:
    """Generate a similarity report comparing text against online sources."""
    purified_text = purify_text(text)
    matching_sites = web_verify(purified_text, results_per_sentence=3)
    matches = {}

    for url in matching_sites:
        try:
            site_text = webcrawler.extract_text(url)
            site_text = purify_text(site_text)
            score = tfidf_similarity(purified_text, site_text)
            if score > 0:
                matches[url] = score
        except Exception as e:
            print(f"[!] Error processing {url}: {e}")
            continue

    # Sort matches by similarity (descending)
    return dict(sorted(matches.items(), key=lambda item: item[1], reverse=True))

def return_table(dictionary: dict) -> str:
    """Convert results to an HTML table for display with clickable URLs."""
    if not dictionary:
        return "<p>No matching sites found or insufficient similarity.</p>"
    df = pd.DataFrame(list(dictionary.items()), columns=["URL", "Similarity (%)"])
    df["URL"] = df["URL"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
    return df.to_html(index=False, justify="center", border=1, escape=False)
