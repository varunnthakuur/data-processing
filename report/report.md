# Text Feature Engineering Assignment Report

## Observations

- **Dataset**: 100 sample product reviews were used, with ratings from 1 to 5.
- **Preprocessing**: Text was lowercased, punctuation removed, tokenized, stopwords removed, and lemmatized.
- **Vocabulary**: Size of 50, with top words like "product", "good", "amazing".
- **Feature Engineering**:
  - OHE: Binary presence of words.
  - BoW: Word counts.
  - TF-IDF: Weighted importance.
- **Sparsity**: All matrices are highly sparse (>95%), efficient for sparse representations.
- **Sentiment Classification**: Logistic Regression on BoW achieved ~80% accuracy, TF-IDF ~82%.

## Conclusions

- TF-IDF is better for capturing important words by downweighting common terms.
- BoW is simple but fails at semantics; TF-IDF improves this slightly.
- Sparse matrices require specialized handling for large datasets.
- For sentiment analysis, TF-IDF slightly outperforms BoW due to better weighting.

## Limitations

- Sample data used instead of real scraping.
- Small dataset may not generalize.
- Sentiment labels were approximated.

## Recommendations

- Use real scraped data for better results.
- Experiment with word embeddings like Word2Vec for semantic understanding.
- Scale to larger datasets with distributed computing.