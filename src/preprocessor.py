import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    tokens = nltk.word_tokenize(text)
    tokens = [t for t in tokens if t not in stop_words]
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/reviews.csv")
    df["cleaned_text"] = df["review_text"].apply(preprocess)
    df.to_csv("data/reviews_cleaned.csv", index=False)
    print("Preprocessed data saved to ../data/reviews_cleaned.csv")