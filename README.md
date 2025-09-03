Cricbuzz LiveStats - Cricket Analytics Platform
https://img.shields.io/badge/Cricket-Analytics-blue
https://img.shields.io/badge/Python-3.10%252B-green
https://img.shields.io/badge/Streamlit-1.28.1-red
https://img.shields.io/badge/MySQL-8.0%252B-orange

A comprehensive cricket analytics platform that combines real-time match data with powerful SQL-based analytics, providing cricket enthusiasts, analysts, and learners with valuable insights into the game.

🚀 Features
🏠 Home Dashboard
Project overview and technology stack

Database connection status

Quick navigation to all sections

Getting started guide

🏏 Live Matches
Real-time match scores and updates

Detailed scorecards with batting and bowling statistics

Match status and commentary

Venue information and match details

Interactive visualizations for performance analysis

📊 Player Statistics
Comprehensive player search functionality

Detailed player profiles and career statistics

Performance metrics across different formats (Test, ODI, T20)

Comparative analysis tools and visualizations

Direct links to Cricbuzz profiles

🧮 SQL Analytics
25+ predefined analytical queries covering:

Player performance analysis

Team statistics and head-to-head records

Venue-based performance metrics

Partnership analysis

Trend analysis and performance tracking

Beginner to advanced level questions

Real-time query execution with visualization

🛠️ CRUD Operations
Complete database management interface

Create, Read, Update, Delete functionality for player data

User-friendly forms for data manipulation

Learning tool for SQL operations

🛠️ Technology Stack
Frontend
Streamlit - Web application framework

Plotly - Interactive visualizations and charts

Backend
Python 3.10+ - Core programming language

MySQL/PostgreSQL - Database management

REST API - Data integration

Libraries
Pandas - Data manipulation and analysis

Requests - HTTP API calls

MySQL Connector - Database connectivity

python-dotenv - Environment management

Tools
Git - Version control

VS Code - Development environment

MySQL Workbench - Database management

📦 Installation
Prerequisites
Python 3.8 or higher

MySQL or PostgreSQL database

Cricbuzz API key from RapidAPI

Setup Steps
Clone the repository

bash
git clone <repository-url>
cd cricbuzz-livestats
Install dependencies

bash
pip install -r requirements.txt
Configure environment variables
Create a .env file with the following variables:

text
DB_HOST=your_database_host
DB_PORT=your_database_port
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
RAPIDAPI_KEY=your_rapidapi_key
RAPIDAPI_HOST=cricbuzz-cricket.p.rapidapi.com
Initialize the application

bash
streamlit run main.py
🗂️ Project Structure
text
cricbuzz-livestats/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── utils/                 # Utility modules
│   ├── api_client.py      # API client for Cricbuzz integration
│   └── db_connection.py   # Database connection management
└── pages/                 # Streamlit page modules
    ├── 1_🏠_Home.py              # Home dashboard
    ├── 2_🏏_Live_Matches.py      # Live matches section
    ├── 3_📊_Player_Stats.py      # Player statistics
    ├── 4_🧮_SQL_Analytics.py     # SQL analytics queries
    └── 5_🛠️_CRUD_Operations.py   # CRUD operations interface
📊 API Integration
The application integrates with the Cricbuzz API via RapidAPI to fetch:

Live match data and scores

Player profiles and statistics

Team information

Series and tournament data

Rate Limiting
The application includes built-in rate limiting to handle API constraints:

Automatic request throttling

Caching mechanisms for frequently accessed data

Error handling for API failures

🗄️ Database Schema
The application uses a comprehensive database schema with tables for:

Teams and players information

Match details and results

Batting and bowling statistics

Fielding records and partnerships

Series and venue information

🎯 Usage Guide
For Cricket Enthusiasts
Start with the Live Matches section to view current games

Use Player Stats to explore individual player performances

Try SQL Analytics to run interesting queries about player and team performance

For Data Analysts
Explore the 25+ predefined analytical queries

Modify queries in the SQL Analytics section for custom analysis

Use visualizations to identify patterns and trends

For Learners
Use CRUD Operations to understand database operations

Study the SQL queries to learn analytical techniques

Experiment with different data visualization approaches

🔧 Configuration Options
Database Settings
Modify the .env file to configure your database connection:

Support for both MySQL and PostgreSQL

Connection pooling for better performance

SSL configuration options for secure connections

API Configuration
Adjust rate limiting settings in api_client.py

Modify cache expiration times for different data types

Configure retry logic for failed API calls

📈 Performance Features
Caching: Intelligent caching of API responses to minimize calls

Lazy Loading: Data is loaded on-demand to improve initial load times

Connection Pooling: Efficient database connection management

Error Handling: Comprehensive error handling with user-friendly messages

Streamlit team for the excellent web framework

MySQL and PostgreSQL communities for database support
