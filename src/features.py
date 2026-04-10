from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import pandas as pd
import matplotlib.pyplot as plt

def build_features(df):
    # Vocabulary
    vectorizer = CountVectorizer(max_features=5000)
    X = vectorizer.fit_transform(df["cleaned_text"])
    vocab = vectorizer.get_feature_names_out()
    print(f"Vocabulary size: {len(vocab)}")

    # Top 20 words
    word_freq = X.sum(axis=0).A1
    top_idx = word_freq.argsort()[-20:][::-1]
    plt.barh([vocab[i] for i in top_idx], word_freq[top_idx])
    plt.title("Top 20 frequent words")
    plt.show()

    # Feature matrices
    ohe_vectorizer = CountVectorizer(binary=True, max_features=5000)
    X_ohe = ohe_vectorizer.fit_transform(df["cleaned_text"])

    bow_vectorizer = CountVectorizer(max_features=5000)
    X_bow = bow_vectorizer.fit_transform(df["cleaned_text"])

    tfidf_vectorizer = TfidfVectorizer(max_features=5000)
    X_tfidf = tfidf_vectorizer.fit_transform(df["cleaned_text"])

    return X_ohe, X_bow, X_tfidf, ohe_vectorizer, bow_vectorizer, tfidf_vectorizer

if __name__ == "__main__":
    df = pd.read_csv("data/reviews_cleaned.csv")
    X_ohe, X_bow, X_tfidf = build_features(df)
    print("Features built")