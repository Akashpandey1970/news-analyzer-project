# app.py
# This is the main application file for the combined News Analyzer project.
# It includes user authentication, profile management, and serves both the
# interactive SPA dashboard and the backend API for NLP analysis.

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import nltk
import spacy
from transformers import pipeline
import re

# --- Configuration ---

# Initialize Flask App
app = Flask(__name__)

# Secret key for session management
app.config['SECRET_KEY'] = 'your_super_secret_key_change_this'

# Database configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- NLP Model Initialization ---

# Download necessary NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

# Load spaCy model for Named Entity Recognition (NER)
try:
    nlp_ner = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model 'en_core_web_sm' not found.")
    print("Please run: python -m spacy download en_core_web_sm")
    nlp_ner = None

# Load Hugging Face pipeline for Sentiment Analysis
print("Loading Sentiment Analysis model...")
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Sentiment Analysis model loaded.")

# --- Database and Login Manager Setup ---

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect here if not logged in

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), default='English')
    interests = db.Column(db.String(200), default='Technology,Economy')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Routes for User Authentication and Profile ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('interactive_dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('interactive_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('interactive_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'warning')
            return redirect(url_for('register'))
        new_user = User(email=email)
        new_user.set_password(request.form.get('password'))
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.language = request.form.get('language')
        current_user.interests = ','.join(request.form.getlist('interests'))
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user)

# --- Route for the Interactive Dashboard ---

@app.route('/dashboard')
@login_required
def interactive_dashboard():
    """Serves the main single-page application dashboard."""
    return render_template('interactive_dashboard.html')


# --- API Endpoint for NLP Analysis ---

def perform_nlp_analysis(text):
    """Helper function to perform sentiment and NER analysis."""
    try:
        sentiment_result = sentiment_pipeline(text[:512])[0]
        if sentiment_result['score'] < 0.95:
            sentiment_result['label'] = 'NEUTRAL'
    except Exception:
        sentiment_result = {'label': 'UNKNOWN', 'score': 0.0}

    entities = {"PERSON": [], "ORG": [], "GPE": []}
    if nlp_ner:
        doc = nlp_ner(text)
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)
        for key in entities:
            entities[key] = list(set(entities[key]))
            
    return {'sentiment': sentiment_result, 'entities': entities}

def process_news_data(news_data):
    """Helper to process a list of articles and add NLP analysis."""
    analyzed_articles = []
    for i, article_data in enumerate(news_data):
        content = article_data.get('content') or article_data.get('description') or ""
        if not content: continue
        analysis_results = perform_nlp_analysis(content)
        analyzed_articles.append({
            'id': i,
            'title': article_data.get('title'),
            'content': content,
            # *** NEW: Added publication timestamp ***
            'published_at': article_data.get('publishedAt'),
            'sentiment': analysis_results['sentiment'],
            'entities': analysis_results['entities']
        })
    return analyzed_articles

@app.route('/api/analyze', methods=['GET'])
@login_required
def analyze_topic():
    """API endpoint to fetch and analyze news for a given keyword."""
    keyword = request.args.get('keyword', 'default topic')
    
    api_key = "Enter Your API Here"
    lang_code = 'hi' if current_user.language == 'Hindi' else 'en'
    api_url = f"https://newsapi.org/v2/everything?apiKey={api_key}&q={keyword}&language={lang_code}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('status') != 'ok':
            error_message = response_data.get('message', 'Unknown API error')
            return jsonify({"error": f"News API Error: {error_message}"}), 400
        
        news_data = response_data.get('articles', [])
        analyzed_articles = process_news_data(news_data)
        return jsonify(analyzed_articles)
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to the news service: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500

@app.route('/api/latest', methods=['GET'])
@login_required
def latest_news():
    """API endpoint to fetch and analyze the latest published news."""
    
    api_key = "Enter Your API Here"
    api_url = f"https://newsapi.org/v2/everything?apiKey={api_key}&q=news&language=en&sortBy=publishedAt"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('status') != 'ok':
            error_message = response_data.get('message', 'Unknown API error')
            return jsonify({"error": f"News API Error: {error_message}"}), 400

        news_data = response_data.get('articles', [])
        analyzed_articles = process_news_data(news_data)
        return jsonify(analyzed_articles)
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to the news service: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

