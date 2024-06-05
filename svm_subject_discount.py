import pandas as pd
import nltk
import emoji
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score
from sklearn.metrics import confusion_matrix
import joblib


# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')

# Preprocessing function
def preprocess(text):
    text = str(text).lower().replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    text = ' '.join([lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words])
    return text

# Load your dataset
emails = pd.read_csv('invoice.csv', encoding='ISO-8859-1').drop_duplicates()
emails['text'] = emails['text'].replace({'\r\n': ' ', '\n': ' ', '\r': ' '}, regex=True)
emails['text'] = emails['text'].apply(preprocess)

# Function to count emojis
def count_emojis(text):
    return emoji.emoji_count(text)

invoice_indicative_keywords = [
    'invoice #', 'order number', 'order #', 'invoice', 'purchase', 'hsn code', 'bill to', 'total invoice value','ship to','address',
    'tax invoice','order id','receipt', 'billing', 'payment', 'transaction', 'due date', 'amount due',
    'credit', 'debit', 'account statement', 'balance', 'invoice date',
    'payment due', 'total amount', 'payable', 'purchase order', 'confirmation',
    'shipping', 'tracking', 'shipment', 'dispatch', 'delivery', 'order confirmation',
    'receipt number', 'payment details', 'invoice total', 'itemized bill',
    "Delivered","Total paid", "Items ordered", "order"
]

emails['exclamation_mark_count'] = emails['text'].apply(lambda text: text.count('!'))
emails['has_invoice_keyword'] = emails['text'].apply(lambda text: any(keyword in text for keyword in invoice_indicative_keywords))
emails['numeric_count'] = emails['text'].apply(lambda text: sum(c.isdigit() for c in text))
emails['percentage_sign_count'] = emails['text'].apply(lambda text: text.count('%'))
emails['dollar_symbol_count'] = emails['text'].apply(lambda text: text.count('$'))
emails['rupee_symbol_count'] = emails['text'].apply(lambda text: text.count('₹'))
emails['emoji_count'] = emails['text'].apply(count_emojis)

# Feature Extraction with TF-IDF
tfidf_vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), max_df=0.95, min_df=2)
X_tfidf = tfidf_vectorizer.fit_transform(emails['text'])
X_extra = emails[['exclamation_mark_count', 'has_invoice_keyword', 'numeric_count',
                  'percentage_sign_count', 'dollar_symbol_count', 'rupee_symbol_count', 'emoji_count']].values
X_combined = pd.concat([pd.DataFrame(X_tfidf.toarray()), pd.DataFrame(X_extra)], axis=1)

y = emails['label']

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X_combined, y, test_size = 0.2, random_state=42)

# Model Training (SVM)
svm_classifier = SVC(kernel='linear', probability=True)  
svm_classifier.fit(X_train, y_train)

# Predictions
predictions_svm = svm_classifier.predict(X_test)

joblib.dump(svm_classifier, 'svm_model_subject_discount.joblib')
joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer_subject_discount.joblib')

# Evaluation
print("SVM Classifier Results:")
print(classification_report(y_test, predictions_svm))
print(f'Accuracy: {accuracy_score(y_test, predictions_svm)}')
print()


conf_matrix = confusion_matrix(y_test, predictions_svm, labels=['invoice', 'spam','promotion', 'discount'])  # noqa
print("Confusion Matrix on Testing dataset:")
print(pd.DataFrame(conf_matrix, index=['Actual invoice', 'Actual spam','Actual promotion', 'Actual discount'],  # noqa
                   columns=['Predicted invoice', 'Predicted spam','Predicted promotion', 'Predicted discount']))  # noqa