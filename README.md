# Cricbuzz-LiveStats-Real-Time-Cricket-Insights-SQL-Based-Analytics
Cricbuzz LiveStats is a full-stack cricket analytics app that merges live data from the Cricbuzz API with a SQL backend. It offers dashboards for fans, fantasy players, and analysts, featuring live updates and SQL-driven insights. The project showcases a full pipeline: API ingestion, database storage, and interactive web visualization.
🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics
A comprehensive cricket analytics dashboard that integrates live data from the Cricbuzz API with a SQL database to create an interactive web application. The platform delivers real-time match updates, detailed player statistics, SQL-driven analytics, and full CRUD operations for data management.

https://img.shields.io/badge/Python-3.8%252B-blue
https://img.shields.io/badge/Streamlit-1.22.0-red
https://img.shields.io/badge/SQL-Database-orange
https://img.shields.io/badge/REST-API-green

📋 Table of Contents
Features

Domain Applications

Technology Stack

Installation

Configuration

Project Structure

Usage



✨ Features
🌐 Live Match Updates: Real-time cricket scores and match details

📊 Player Statistics: Comprehensive player performance metrics

🔍 SQL Analytics: 25+ pre-built SQL queries for cricket data analysis

🛠️ CRUD Operations: Full Create, Read, Update, Delete functionality

📈 Data Visualization: Interactive charts and graphs for performance metrics

⚡ Real-time Updates: Automatic refresh of live match data

🎯 Domain Applications
📺 Sports Media & Broadcasting: Real-time updates for commentary and analysis

🎮 Fantasy Cricket Platforms: Player performance tracking and statistics

📈 Cricket Analytics Firms: Advanced statistical modeling and player evaluation

🎓 Educational Institutions: Teaching database operations with real-world data

🎲 Sports Betting & Prediction: Historical performance analysis for odds calculation

🛠️ Technology Stack
Backend: Python 3.8+

Web Framework: Streamlit

Database: PostgreSQL/MySQL/SQLite (Database-agnostic design)

API Integration: Requests library for Cricbuzz API

Data Processing: Pandas, NumPy

Visualization: Plotly, Matplotlib

📦 Installation
Clone the repository:

bash
git clone https://github.com/yourusername/cricbuzz-livestats.git
cd cricbuzz-livestats
Create a virtual environment:

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
pip install -r requirements.txt
Set up your database (PostgreSQL recommended):

bash
# For PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb cricket_db
⚙️ Configuration
Rename config.example.py to config.py

Update the configuration with your settings:

python
# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'cricket_db',
    'user': 'your_username',
    'password': 'your_password',
    'port': 5432
}

# API Configuration
API_BASE_URL = 'https://api.cricbuzz.com/'
API_KEY = 'your_api_key_here'  # If required

# App Configuration
REFRESH_INTERVAL = 60  # Seconds between data refreshes
Initialize the database:


python init_db.py
📁 Project Structure
text
cricbuzz-livestats/
├── main.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── utils/
│   ├── db_connection.py   # Database connection handler
│   ├── api_client.py      # Cricbuzz API client
├── pages/
│   ├── 1_🏠_Home.py          # Home page
│   ├── 2_⚡_Live_Matches.py  # Live matches page
│   ├── 3_📊_Player_Stats.py  # Player statistics page
│   ├── 4_🔍_SQL_Analytics.py # SQL analytics page
│   └── 5_🛠️_CRUD_Operations.py # CRUD operations page
└── README.md

🚀 Usage
Start the application:

bash
streamlit run main.py
Navigate through the different pages:

Home: Project overview and instructions

Live Matches: Real-time match updates and scores

Player Stats: Player performance statistics and visualizations

SQL Analytics: Pre-built SQL queries with interactive results

CRUD Operations: Database management interface

Use the sidebar to:

Select different matches (Live Matches page)

Choose player statistics categories (Player Stats page)

Execute different SQL queries (SQL Analytics page)

Perform database operations (CRUD Operations page)



Push to the branch (git push origin feature/amazing-feature)

Open a Pull Request
