# main.py
import streamlit as st
from utils.db_connection import test_connection

def main():
    st.set_page_config(
        page_title="Cricbuzz LiveStats",
        page_icon="🏏",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Test database connection on startup
    db_status = test_connection()
    
    # Sidebar navigation
    st.sidebar.title("🏏 Cricbuzz LiveStats")
    st.sidebar.markdown("### Navigation")
    
    # Display database status in sidebar
    if db_status['connected']:
        st.sidebar.success("✅ Database Connected")
        st.sidebar.info(f"📊 {db_status['player_copy_count']} sample players loaded")
    else:
        st.sidebar.error("❌ Database Connection Failed")
        st.sidebar.warning("Please check your database configuration in .env file")
    
    # Page selection in sidebar
    page = st.sidebar.radio(
        "Go to:",
        ["Home", "Live Matches", "Player Stats", "SQL Queries", "CRUD Operations"],
        index=0
    )
    
    # Navigate to selected page
    if page == "Home":
        st.switch_page("pages/1_🏠_Home.py")
    elif page == "Live Matches":
        st.switch_page("pages/2_🏏_Live_Matches.py")
    elif page == "Player Stats":
        st.switch_page("pages/3_📊_Player_Stats.py")
    elif page == "SQL Queries":
        st.switch_page("pages/4_🧮_SQL_Analytics.py")
    elif page == "CRUD Operations":
        st.switch_page("pages/5_🛠️_CRUD_Operations.py")

if __name__ == "__main__":
    main()

    

# Footer
st.markdown("---")
st.caption("© 2024 Cricbuzz LiveStats - Sports Analytics Platform | Built with Python & Streamlit")