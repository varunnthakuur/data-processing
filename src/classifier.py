from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

def train_classifiers(X_bow, X_tfidf, y):
    for name, X in [("BoW", X_bow), ("TF-IDF", X_tfidf)]:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        for model_name, model in [("Logistic Regression", LogisticRegression()),
                                   ("Naive Bayes", MultinomialNB())]:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            print(f"\n{model_name} on {name}:")
            print(classification_report(y_test, y_pred))

if __name__ == "__main__":
    from features import build_features
    df = pd.read_csv("data/reviews_cleaned.csv")
    df_binary = df[df["rating"] != 3].copy()
    df_binary["label"] = (df_binary["rating"] >= 4).astype(int)
    X_ohe, X_bow, X_tfidf = build_features(df_binary)
    train_classifiers(X_bow, X_tfidf, df_binary["label"])