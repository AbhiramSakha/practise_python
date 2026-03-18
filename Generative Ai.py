from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
import pandas as pd
import pickle

app = Flask(__name__)

# Load the dataset
df = pd.read_csv("C:\Users\91939\Downloads\Desktop\abhi\emails.csv")

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(df['Email'], df['Label'], test_size=0.2, random_state=42)

# Create a TfidfVectorizer object
vectorizer = TfidfVectorizer()

# Fit the vectorizer to the training data and transform both the training and testing data
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train a Multinomial Naive Bayes classifier on the training data
clf = MultinomialNB()
clf.fit(X_train_tfidf, y_train)

# Make predictions on the testing data
y_pred = clf.predict(X_test_tfidf)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f'Model Accuracy: {accuracy:.2f}')

# Save the trained model and vectorizer to disk
with open('spam_model.pkl', 'wb') as f:
    pickle.dump(clf, f)

with open('vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

# Define a function to classify new emails
def classify_email(email):
    email_tfidf = vectorizer.transform([email])
    prediction = clf.predict(email_tfidf)
    return prediction[0]

# Define a Flask API endpoint to classify new emails
@app.route('/classify', methods=['POST'])
def classify():
    email = request.json['email']
    prediction = classify_email(email)
    return jsonify({'prediction': prediction})

if __name__ == '__main__':
    app.run(debug=True)