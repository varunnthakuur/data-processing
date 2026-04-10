import streamlit as st
import pandas as pd
from src.preprocessor import preprocess
from src.features import build_features
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
st.title("Text Feature Engineering Dashboard")

if "df" not in st.session_state:
    st.session_state.df = None
if "sentiment_model" not in st.session_state:
    st.session_state.sentiment_model = None
if "sentiment_vectorizer" not in st.session_state:
    st.session_state.sentiment_vectorizer = None
if "review_count" not in st.session_state:
    st.session_state.review_count = 0
if "product_name_fetched" not in st.session_state:
    st.session_state.product_name_fetched = ""

positive_words = [
    "amazing", "love", "good", "excellent", "fantastic", "great", "satisfied", "worth", "recommend", "awesome", "best", "nice"
]
negative_words = [
    "terrible", "worst", "broke", "disappointed", "poor", "bad", "awful", "hate", "worse", "problem", "disappointing"
]

def build_sentiment_model(df):
    if "rating" not in df.columns:
        return None, None
    df_model = df.copy()
    df_model = df_model[df_model["rating"] != 3]
    if df_model.empty:
        return None, None
    df_model["label"] = (df_model["rating"] >= 4).astype(int)
    vectorizer = TfidfVectorizer(max_features=5000)
    X = vectorizer.fit_transform(df_model["cleaned_text"])
    model = LogisticRegression(max_iter=1000)
    model.fit(X, df_model["label"])
    return model, vectorizer

def predict_sentiment_rule(text):
    cleaned = preprocess(text)
    tokens = set(cleaned.split())
    pos_score = sum(1 for word in positive_words if word in tokens)
    neg_score = sum(1 for word in negative_words if word in tokens)
    if pos_score > neg_score:
        return "Positive"
    if neg_score > pos_score:
        return "Negative"
    return "Neutral"

with st.expander("Data Input"):
    st.subheader("Data Input")
    input_method = st.radio("Choose data input method:", ["Search Amazon", "Upload Excel/CSV"])
    
    if input_method == "Search Amazon":
        product_name = st.text_input("Enter product name to search on Amazon:")
        if st.button("Search and Scrape Reviews"):
            if product_name:
                with st.spinner("Searching Amazon and collecting reviews..."):
                    from src.scraper import search_amazon_reviews
                    st.session_state.df = search_amazon_reviews(product_name, num_reviews=100)
                    if st.session_state.df is not None and len(st.session_state.df) > 0:
                        st.session_state.review_count = len(st.session_state.df)
                        st.session_state.product_name_fetched = product_name
                        
                        # Display metrics in a visually prominent way
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Reviews Fetched", st.session_state.review_count)
                        with col2:
                            st.metric("Product", product_name)
                        
                        st.success(f"Successfully scraped {st.session_state.review_count} reviews for '{product_name}'!")
                        st.write(st.session_state.df.head())
                    else:
                        st.session_state.review_count = 0
                        st.session_state.product_name_fetched = ""
                        st.error("Could not fetch reviews. Please try another product.")
            else:
                st.warning("Please enter a product name.")
    
    else:
        uploaded_file = st.file_uploader("Upload reviews CSV or Excel file", type=["csv", "xlsx", "xls"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.df = pd.read_csv(uploaded_file)
                else:
                    st.session_state.df = pd.read_excel(uploaded_file)
                st.session_state.review_count = len(st.session_state.df)
                st.session_state.product_name_fetched = uploaded_file.name
                
                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Reviews Loaded", st.session_state.review_count)
                with col2:
                    st.metric("File", uploaded_file.name)
                
                st.success(f"Successfully loaded {st.session_state.review_count} rows from {uploaded_file.name}")
                st.write(st.session_state.df.head())
            except Exception as e:
                st.error(f"Error reading file: {e}")

with st.expander("Preprocessing"):
    if st.session_state.df is not None:
        st.subheader("Preprocessing")
        if "cleaned_text" not in st.session_state.df.columns:
            st.session_state.df["cleaned_text"] = st.session_state.df["review_text"].apply(preprocess)
        st.write("Before and After:")
        st.write(st.session_state.df[["review_text", "cleaned_text"]].head())
    else:
        st.info("Upload a CSV in the Upload section first.")

with st.expander("Features"):
    if st.session_state.df is not None and "cleaned_text" in st.session_state.df.columns:
        st.subheader("Feature Engineering")
        X_ohe, X_bow, X_tfidf, ohe_vectorizer, bow_vectorizer, tfidf_vectorizer = build_features(st.session_state.df)
        option = st.selectbox("Choose feature type", ["OHE", "BoW", "TF-IDF"])

        def highlight_cells(val):
            color = "#bdd7ee" if val > 1 else "#c6efce" if val == 1 else "white"

            return f"background-color: {color}"
        
         
        if option == "OHE":
            st.write("OHE Matrix shape:", X_ohe.shape)
            st.write("OHE stores binary presence/absence of words.")
            st.write("Example rows:")
            ohe_cols = ohe_vectorizer.get_feature_names_out()
            #st.write(pd.DataFrame(X_ohe.toarray()[:5], columns=ohe_cols))
            ohe_df = pd.DataFrame(X_ohe.toarray()[:5], columns=ohe_cols)
            st.dataframe(ohe_df.style.map(highlight_cells))  # Highlight presence with colors

        elif option == "BoW":
            st.write("BoW Matrix shape:", X_bow.shape)
            st.write("BoW stores word counts.")
            st.write("Example rows:")
            bow_cols = bow_vectorizer.get_feature_names_out()
            #st.write(pd.DataFrame(X_bow.toarray()[:5], columns=bow_cols))
            bow_df = pd.DataFrame(X_bow.toarray()[:5], columns=bow_cols)
            st.dataframe(bow_df.style.map(highlight_cells))  # Highlight presence with colors

        else:
            st.write("TF-IDF Matrix shape:", X_tfidf.shape)
            st.write("TF-IDF stores importance weights.")
            text = " ".join(st.session_state.df["cleaned_text"])
            wordcloud = WordCloud(width=600, height=300, background_color="white").generate(text)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
    else:
        st.info("Upload and preprocess the dataset before viewing features.")

with st.expander("Comparison"):
    st.subheader("Feature Comparison")
    if st.session_state.df is not None and "cleaned_text" in st.session_state.df.columns:
        X_ohe, X_bow, X_tfidf, ohe_vectorizer, bow_vectorizer, tfidf_vectorizer = build_features(st.session_state.df)
        import numpy as np
        sparsity_ohe = round((1 - X_ohe.nnz / (X_ohe.shape[0] * X_ohe.shape[1])) * 100, 2)
        sparsity_bow = round((1 - X_bow.nnz / (X_bow.shape[0] * X_bow.shape[1])) * 100, 2)
        sparsity_tfidf = round((1 - X_tfidf.nnz / (X_tfidf.shape[0] * X_tfidf.shape[1])) * 100, 2)

        comparison = pd.DataFrame({
            "Method": ["OHE", "BoW", "TF-IDF"],
            "Shape": [
                f"{X_ohe.shape[0]} x {X_ohe.shape[1]}",
                f"{X_bow.shape[0]} x {X_bow.shape[1]}",
                f"{X_tfidf.shape[0]} x {X_tfidf.shape[1]}"
            ],
            "Sparsity (%)": [
                sparsity_ohe,
                sparsity_bow,
                sparsity_tfidf
            ],  
            "Non0zerocells": [
                X_ohe.nnz,
                X_bow.nnz,
                X_tfidf.nnz
            ],  
            "Mean non-zero per row": [
                round(X_ohe.nnz / X_ohe.shape[0], 2),
                round(X_bow.nnz / X_bow.shape[0], 2),
                round(X_tfidf.nnz / X_tfidf.shape[0], 2)
            ],
            "Max value": [
                int(X_ohe.max()),
                int(X_bow.max()),
                int(X_tfidf.max())
            ],  
            "Value type": [
                "Binary (0/1)", "Count (0,1,2,...)", "Weight (0.0 - 1.0)"
            ],
            "Represents": [
                "Word presence in a review",
                "Word frequency per review",
                "Importance of words across reviews"
            ]
        })
        st.dataframe(comparison)
        st.markdown("**Sparsity comparison**")
        st.bar_chart(comparison.set_index("Method")["Sparsity (%)"])
        st.markdown("**Why this matters**")
        st.write(
            "- OHE is sparse and binary, so it shows only whether a word appears."
            " - BoW stores counts and is still sparse when vocabulary is large."
            " - TF-IDF adds importance weighting, which helps downweight common words."
        )
    else:
        st.info("Upload and preprocess the dataset to see the comparison chart.")

with st.expander("Predict Sentiment"):
    st.subheader("Predict Sentiment")
    review = st.text_input("Enter a review")
    if review:
        if st.session_state.df is not None and "rating" in st.session_state.df.columns:
            if st.session_state.sentiment_model is None or st.session_state.sentiment_vectorizer is None:
                st.session_state.sentiment_model, st.session_state.sentiment_vectorizer = build_sentiment_model(st.session_state.df)

            if st.session_state.sentiment_model is not None:
                cleaned = preprocess(review)
                X_review = st.session_state.sentiment_vectorizer.transform([cleaned])
                label = st.session_state.sentiment_model.predict(X_review)[0]
                sentiment = "Positive" if label == 1 else "Negative"
                st.write(f"Predicted sentiment: {sentiment} (trained model)")
            else:
                sentiment = predict_sentiment_rule(review)
                st.write(f"Predicted sentiment: {sentiment} (rule-based fallback)")
                st.info("No valid rating labels were found in the data, so a rule-based prediction is used.")
        else:
            sentiment = predict_sentiment_rule(review)
            st.write(f"Predicted sentiment: {sentiment} (rule-based)")
            st.info("Upload a CSV with a 'rating' column for trained model predictions.")