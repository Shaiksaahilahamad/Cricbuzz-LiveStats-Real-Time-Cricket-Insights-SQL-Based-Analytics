# pages/1_🏠_Home.py
import streamlit as st
from utils.db_connection import get_db_connection

def main():
    st.set_page_config(
        page_title="Home - Cricbuzz LiveStats",
        page_icon="🏠",
        layout="wide"
    )
    
    # Main title
    st.title("🏠 Home")
    st.subheader("Welcome to Cricbuzz LiveStats - Real-Time Cricket Analytics")
    
    # Database connection status - MOVED TO HOME PAGE
    col1, col2 = st.columns([3, 1])
    with col1:
        try:
            connection = get_db_connection()
            if connection and connection.is_connected():
                st.success("✅ Database Connected Successfully")
                connection.close()
            else:
                st.error("❌ Database Connection Failed")
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
    
    st.markdown("""
    ## 📋 Project Overview
    
    **Cricbuzz LiveStats** is a comprehensive cricket analytics platform that combines 
    real-time match data with powerful SQL-based analytics. This application provides 
    cricket enthusiasts, analysts, and learners with valuable insights into the game.
    
    ### 🎯 Key Objectives
    - Provide real-time cricket match updates and statistics
    - Offer advanced SQL-based analytical capabilities
    - Enable easy player search and performance analysis
    - Facilitate learning of database operations through CRUD functionality
    - Create an interactive and user-friendly interface for cricket analytics
    
    ### 🛠️ Technology Stack
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("**Frontend**")
        st.write("- Streamlit")

    
    with col2:
        st.success("**Backend**")
        st.write("- Python 3.10+")
        st.write("- MySQL/PostgreSQL")
        st.write("- REST API")
    
    with col3:
        st.warning("**Libraries**")
        st.write("- Pandas")
        st.write("- Requests")
        st.write("- MySQL Connector")
    
    with col4:
        st.error("**Tools**")
        st.write("- Git")
        st.write("- VS Code")
        st.write("- MySQL Workbench")
    
    st.divider()
    
    st.markdown("""
    ## 📊 Features Overview
    
    ### 🏏 Live Matches Section
    - Real-time match scores and updates
    - Detailed scorecards with batting and bowling statistics
    - Match status and commentary
    - Venue information and match details
    
    ### 📊 Player Statistics
    - Comprehensive player search functionality
    - Detailed player profiles and career statistics
    - Performance metrics across different formats
    - Comparative analysis tools
    
    ### 🧮 SQL Analytics
    - 25+ predefined analytical queries
    - Beginner to advanced level questions
    - Real-time query execution
    - Results visualization and export
    
    ### 🛠️ CRUD Operations
    - Complete database management interface
    - Create, Read, Update, Delete functionality
    - User-friendly forms for data manipulation
    - Learning tool for SQL operations
    
    ## 🚀 Getting Started
    
    ### Prerequisites
    1. Python 3.8 or higher
    2. MySQL or PostgreSQL database
    3. Cricbuzz API key from RapidAPI
    
    ### Installation Steps
    1. Clone the repository
    2. Install dependencies: `pip install -r requirements.txt`
    3. Configure environment variables in `.env` file
    4. Initialize database: Run the application once
    5. Start the app: `streamlit run main.py`
    
    ### Environment Configuration
    Create a `.env` file with the following variables:
    ```
    DB_HOST=your_database_host
    DB_PORT=your_database_port
    DB_NAME=your_database_name
    DB_USER=your_database_user
    DB_PASSWORD=your_database_password
    RAPIDAPI_KEY=your_rapidapi_key
    RAPIDAPI_HOST=cricbuzz-cricket.p.rapidapi.com
    ```
    """)
    
    st.divider()
    
    st.success("""
    🎯 **Pro Tip**: Start by exploring the Live Matches section to see real-time data, 
    then try the SQL Analytics section to run some interesting queries about player performance!
    """)
        # Quick navigation buttons
    st.markdown("### 🚀 Quick Navigation")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏏 Live Matches", use_container_width=True):
            st.switch_page("pages/2_🏏_Live_Matches.py")
    
    with col2:
        if st.button("📊 Player Stats", use_container_width=True):
            st.switch_page("pages/3_📊_Player_Stats.py")
    
    with col3:
        if st.button("🧮 SQL Queries", use_container_width=True):
            st.switch_page("pages/4_🧮_SQL_Analytics.py")
    
    with col4:
        if st.button("🛠️ CRUD Operations", use_container_width=True):
            st.switch_page("pages/5_🛠️_CRUD_Operations.py")

if __name__ == "__main__":
    main()