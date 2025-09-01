AI-Powered News Analysis Dashboard
An intelligent web app to fetch and analyze real-time news articles using NLP, providing instant insights on public sentiment and key entities.

✨ Key Features
Real-Time News: Fetches latest news or searches by topic.

AI-Powered Analysis: Performs Sentiment Analysis (Positive, Negative, Neutral) and Named Entity Recognition (People, Orgs, Places).

Interactive UI: Visualizes data with dynamic charts.

User System: Secure user registration, login, and profile management.

🛠️ Tech Stack
Backend: Python, Flask, SQLAlchemy

Frontend: JavaScript, Tailwind CSS, Chart.js

NLP: Hugging Face Transformers, spaCy

Database: SQLite

🚀 Quick Start
Clone the Repository:

git clone https://github.com/your-username/news-analyzer-project.git
cd news-analyzer-project

Setup Environment & Dependencies:

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Use `.\venv\Scripts\activate` on Windows

# Install packages
pip install -r requirements.txt

Download NLP Model:

python -m spacy download en_core_web_sm

Add API Key:

Get a free API key from newsapi.org.

Add the key to the api_key variables in app.py.

Run the App:

python app.py

Access the dashboard at http://127.0.0.1:5000.

📖 Usage
Register & Login to access the dashboard.

The dashboard loads with the latest news automatically.

Search for any topic to get specific, analyzed articles.

Click on an article to view detailed analysis.

🔮 Future Enhancements
Topic Modeling

Historical Sentiment Tracking

Automatic Summarization

Cloud Deployment

📄 License
This project is licensed under the MIT License.
