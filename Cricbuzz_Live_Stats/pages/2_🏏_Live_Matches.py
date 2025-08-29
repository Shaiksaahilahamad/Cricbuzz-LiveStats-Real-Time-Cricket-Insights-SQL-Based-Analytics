# pages/2_🏏_Live_Matches.py
import streamlit as st
import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Track API calls to avoid rate limiting
last_api_call = None
min_call_interval = 2  # seconds between calls

def check_rate_limit():
    """Check if we need to wait before making another API call"""
    global last_api_call
    
    if last_api_call is not None:
        elapsed = (datetime.now() - last_api_call).total_seconds()
        if elapsed < min_call_interval:
            wait_time = min_call_interval - elapsed
            time.sleep(wait_time)
    
    last_api_call = datetime.now()

def get_api_headers():
    """Get API headers with authentication"""
    api_key = os.getenv('RAPIDAPI_KEY')
    api_host = os.getenv('RAPIDAPI_HOST')
    
    if not api_key or not api_host:
        st.error("API configuration missing. Please check your .env file")
        return None
        
    return {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': api_host
    }

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_matches(match_type="live"):
    """Get matches from Cricbuzz API with caching"""
    headers = get_api_headers()
    if not headers:
        return None
        
    url = f"https://{os.getenv('RAPIDAPI_HOST')}/matches/v1/{match_type}"
    
    try:
        check_rate_limit()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching matches: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_detailed_scorecard(match_id):
    """Get detailed scorecard for a specific match with rate limiting and caching"""
    headers = get_api_headers()
    if not headers:
        return None
        
    url = f"https://{os.getenv('RAPIDAPI_HOST')}/mcenter/v1/{match_id}/scard"
    
    try:
        check_rate_limit()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response.status_code == 429:
            st.error("⚠️ API rate limit exceeded. Please wait a moment before trying again.")
            st.info("Free RapidAPI plans have strict rate limits. Consider upgrading or waiting.")
        else:
            st.error(f"Error fetching detailed scorecard: {e}")
        return None
    except Exception as e:
        st.error(f"Error fetching detailed scorecard: {e}")
        return None

def convert_timestamp(timestamp_ms):
    """Convert milliseconds timestamp to readable date"""
    try:
        return datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime('%Y-%m-%d %H:%M')
    except:
        return "N/A"

def display_slightly_larger_innings_score(innings_key, innings_data):
    """Display slightly larger innings score card"""
    runs = innings_data.get('runs', 0)
    wickets = innings_data.get('wickets', 0)
    overs = innings_data.get('overs', 0)
    
    innings_num = innings_key.replace('inngs', 'Innings ')
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 12px; border-radius: 10px; margin: 8px 0;
                text-align: center; border: 2px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.2);">
        <p style="margin: 0; font-size: 12px; color: #FFD700; font-weight: bold;">{innings_num}</p>
        <h3 style="margin: 5px 0; color: white; font-size: 20px;">{runs}/{wickets}</h3>
        <p style="margin: 0; font-size: 11px; color: white;">({overs} overs)</p>
    </div>
    """, unsafe_allow_html=True)

def display_detailed_scorecard_data(detailed_data):
    """Display detailed scorecard data with the correct structure parsing"""
    
    # Check if we have valid data
    if not detailed_data or not isinstance(detailed_data, dict):
        st.error("No detailed scorecard data available")
        return
    
    # Different API responses have different structures
    if 'scorecard' in detailed_data:
        scorecards = detailed_data['scorecard']
    elif 'matchScoreDetails' in detailed_data:
        scorecards = detailed_data['matchScoreDetails'].get('inningsScoreList', [])
    else:
        st.error("Unexpected API response format")
        return
        
    if not scorecards:
        st.info("No innings data available in scorecard")
        return
    
    # Display match status
    if 'status' in detailed_data:
        st.success(f"**Match Status:** {detailed_data['status']}")
    
    # Process each innings
    for i, innings in enumerate(scorecards):
        if not isinstance(innings, dict):
            continue
        
        st.markdown("---")
        innings_title = innings.get('batTeamName', f'Innings {i+1}')
        st.subheader(f"📊 {innings_title}")
        
        # Display basic innings info
        col1, col2, col3 = st.columns(3)
        with col1:
            score = f"{innings.get('score', 0)}/{innings.get('wickets', 0)}"
            st.metric("Score", score)
        with col2:
            st.metric("Overs", innings.get('overs', 0))
        with col3:
            st.metric("Run Rate", round(float(innings.get('runRate', 0)), 2))
        
        # BATTING DATA - from 'batsman' list
        if 'batsman' in innings and isinstance(innings['batsman'], list) and innings['batsman']:
            st.markdown("**🧍 Batting**")
            batting_table = []
            
            for batsman in innings['batsman']:
                if isinstance(batsman, dict):
                    batting_table.append({
                        "Batsman": batsman.get('name', batsman.get('batName', 'N/A')),
                        "Runs": batsman.get('runs', batsman.get('score', 0)),
                        "Balls": batsman.get('balls', batsman.get('ballsFaced', 0)),
                        "4s": batsman.get('fours', batsman.get('four', 0)),
                        "6s": batsman.get('sixes', batsman.get('six', 0)),
                        #"SR": round(batsman.get('strikeRate', 0), 2),
                        #"Status": batsman.get('outDesc', batsman.get('dismissal', 'not out'))
                    })
            
            if batting_table:
                st.dataframe(batting_table, use_container_width=True, hide_index=True)
            else:
                st.info("No valid batting data found")
        else:
            st.info("No batting data available")
        
        # BOWLING DATA - from 'bowler' list
        if 'bowler' in innings and isinstance(innings['bowler'], list) and innings['bowler']:
            st.markdown("**🎯 Bowling**")
            bowling_table = []
            
            for bowler in innings['bowler']:
                if isinstance(bowler, dict):
                    bowling_table.append({
                        "Bowler": bowler.get('name', bowler.get('bowlName', 'N/A')),
                        "Overs": bowler.get('overs', bowler.get('oversBowled', 0)),
                        "Maidens": bowler.get('maidens', bowler.get('maidenOvers', 0)),
                        "Runs": bowler.get('runs', bowler.get('runsConceded', 0)),
                        "Wickets": bowler.get('wickets', bowler.get('wicketsTaken', 0)),
                        "Economy": round(float(bowler.get('economy', bowler.get('economyRate', 0))), 2),
                        "Wides": bowler.get('wides', bowler.get('wide', 0))
                    })
            
            if bowling_table:
                st.dataframe(bowling_table, use_container_width=True, hide_index=True)
            else:
                st.info("No valid bowling data found")
        else:
            st.info("No bowling data available")

def display_match_details(match, match_index):
    """Display detailed information for the selected match with detailed scorecard"""
    match_info = match['match_info']
    match_score = match['match_score']
    match_id = match_info.get('matchId')
    
    team1 = match_info.get('team1', {})
    team2 = match_info.get('team2', {})
    venue_info = match_info.get('venueInfo', {})
    
    # Main match header
    st.markdown("---")
    
    # Team vs Team header
    col_header1, col_header2, col_header3 = st.columns([3, 1, 3])
    
    with col_header1:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    color: white; border-radius: 15px; margin: 10px 0; border: 2px solid #FFD700;">
            <h3 style="margin: 0; color: white; font-size: 20px;">{team1.get('teamName', 'TBA')}</h3>
            <p style="margin: 4px 0; color: #FFD700; font-size: 14px;">{team1.get('teamSName', '')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_header2:
        st.markdown("""
        <div style="text-align: center; padding: 12px;">
            <div style="background: #ff4b4b; color: white; border-radius: 50%; width: 50px; height: 50px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto;
                        font-weight: bold; font-size: 18px; border: 2px solid white;">
                VS
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_header3:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    color: white; border-radius: 15px; margin: 10px 0; border: 2px solid #FFD700;">
            <h3 style="margin: 0; color: white; font-size: 20px;">{team2.get('teamName', 'TBA')}</h3>
            <p style="margin: 4px 0; color: #FFD700; font-size: 14px;">{team2.get('teamSName', '')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Series and match info
    st.markdown(f"""
    <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 12px; border-radius: 12px; margin: 12px 0; border: 2px solid #FFD700;">
        <h4 style="margin: 0; color: white; font-size: 16px;">🎯 {match['series_name']}</h4>
        <p style="margin: 3px 0; color: #FFD700; font-size: 13px;">{match_info.get('matchDesc', '')} • {match_info.get('matchFormat', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current match status
    status = match_info.get('status', 'Match in Progress')
    status_color = "#28a745" if "won" in status.lower() else "#ff6b6b"
    status_icon = "⚡" if "progress" in status.lower() else "📅"
    
    st.markdown(f"""
    <div style="text-align: center; background: {status_color}; padding: 12px; border-radius: 10px; margin: 15px 0;
                border: 2px solid white;">
        <p style="margin: 2px 0; color: white; font-size: 16px; font-weight: bold;">
            {status_icon} {status}
        </p>
        <p style="margin: 2px 0; color: white; font-size: 15px;">{match_info.get('stateTitle', 'Live')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Match overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Series:** {match['series_name']}")
        st.write(f"**Match:** {match_info.get('matchDesc', 'N/A')}")
        st.write(f"**Format:** {match_info.get('matchFormat', 'N/A')}")
    
    with col2:
        st.write(f"**Ground:** {venue_info.get('ground', 'N/A')}")
        st.write(f"**City:** {venue_info.get('city', 'N/A')}")
        st.write(f"**Start:** {convert_timestamp(match_info.get('startDate', ''))}")
    
    with col3:
        st.write(f"**Status:** {match_info.get('status', 'N/A')}")
        st.write(f"**State:** {match_info.get('state', 'N/A')}")
        st.write(f"**Match ID:** {match_info.get('matchId', 'N/A')}")
    
    st.markdown("---")
    
    # Display scores section
    st.markdown("### 📊 LIVE SCORES")
    
    team1_scores = match_score.get('team1Score', {})
    team2_scores = match_score.get('team2Score', {})
    
    if team1_scores or team2_scores:
        score_col1, score_col2 = st.columns(2)
        
        # Team 1 innings
        with score_col1:
            if team1_scores:
                st.markdown(f"**{team1.get('teamName', 'Team 1')}**")
                for innings_key, innings_data in team1_scores.items():
                    if innings_data and isinstance(innings_data, dict):
                        display_slightly_larger_innings_score(innings_key, innings_data)
            else:
                st.info("No score data available")
        
        # Team 2 innings
        with score_col2:
            if team2_scores:
                st.markdown(f"**{team2.get('teamName', 'Team 2')}**")
                for innings_key, innings_data in team2_scores.items():
                    if innings_data and isinstance(innings_data, dict):
                        display_slightly_larger_innings_score(innings_key, innings_data)
            else:
                st.info("No score data available")
    else:
        st.info("No score data available for this match")
    
    st.markdown("---")
    
    # Detailed Scorecard Section
    st.markdown("### 📋 DETAILED SCORECARD")
    
    # Load detailed scorecard when user clicks button
    if st.button("🔄 Load Detailed Scorecard", key=f"load_detail_{match_index}"):
        with st.spinner("Loading detailed scorecard data..."):
            detailed_data = get_detailed_scorecard(match_id)
            
            if detailed_data:
                display_detailed_scorecard_data(detailed_data)
            else:
                st.error("Could not load detailed scorecard data. Possible reasons:")
                st.write("1. API rate limiting - please wait a few moments")
                st.write("2. The match might not have detailed data available yet")
                st.write("3. Match ID might be incorrect or not supported")
                
                # Add a retry button
                if st.button("🔄 Retry", key=f"retry_{match_index}"):
                    st.rerun()

def process_and_display_matches(matches_data, match_type):
    """Process the API response and display matches with filtering"""
    
    if not matches_data or 'typeMatches' not in matches_data:
        st.error("No match data available or invalid API response format")
        return
    
    # Collect all matches
    all_matches = []
    
    for type_match in matches_data['typeMatches']:
        match_type_category = type_match.get('matchType', 'Unknown')
        series_matches = type_match.get('seriesMatches', [])
        
        for series_match in series_matches:
            if 'seriesAdWrapper' in series_match:
                series_data = series_match['seriesAdWrapper']
                series_name = series_data.get('seriesName', 'Unknown Series')
                matches = series_data.get('matches', [])
                
                for match in matches:
                    match_info = match.get('matchInfo', {})
                    match_score = match.get('matchScore', {})
                    
                    match_state = match_info.get('state', '').lower()
                    
                    # Filter based on match type
                    if match_type.lower() == "live":
                        # Show only live and in-progress matches
                        if "complete" in match_state or "finished" in match_state or "upcoming" in match_state:
                            continue
                    elif match_type.lower() == "recent":
                        # Show only completed matches
                        if not ("complete" in match_state or "finished" in match_state):
                            continue
                    elif match_type.lower() == "upcoming":
                        # Show only upcoming matches
                        if not ("upcoming" in match_state or "preview" in match_state):
                            continue
                    
                    # Add match to list with enhanced info
                    enhanced_match = {
                        'match_info': match_info,
                        'match_score': match_score,
                        'series_name': series_name,
                        'match_type': match_type_category
                    }
                    all_matches.append(enhanced_match)
    
    if not all_matches:
        if match_type.lower() == "live":
            st.warning("No live matches currently in progress. Try checking 'Recent' or 'Upcoming' matches.")
        else:
            st.warning(f"No {match_type} matches found.")
        return
    
    # Display match selection
    st.subheader(f"📋 Available Matches ({match_type})")
    
    match_options = {}
    for i, match in enumerate(all_matches):
        match_info = match['match_info']
        team1 = match_info.get('team1', {}).get('teamName', 'TBA')
        team2 = match_info.get('team2', {}).get('teamName', 'TBA')
        state = match_info.get('state', 'Scheduled')
        series_name = match['series_name']
        
        option_text = f"{series_name}: {team1} vs {team2} - {state}"
        match_options[option_text] = i
    
    # Use a unique key based on match_type to avoid duplicate key errors
    unique_key = f"match_selector_{match_type.lower()}"
    selected_match_text = st.selectbox(
        "Choose a match to view details:",
        options=list(match_options.keys()),
        key=unique_key
    )
    
    selected_match_index = match_options[selected_match_text]
    selected_match = all_matches[selected_match_index]
    
    # Display selected match details with unique index
    display_match_details(selected_match, selected_match_index)

def main():
    st.set_page_config(
        page_title="Live Matches - Cricbuzz LiveStats",
        page_icon="🏏",
        layout="wide"
    )
    
    st.header("🏏 Live Cricket Matches")
    
    # API key check
    if not os.getenv('RAPIDAPI_KEY') or not os.getenv('RAPIDAPI_HOST'):
        st.error("❌ API configuration missing. Please check your .env file")
        st.info("Make sure you have RAPIDAPI_KEY and RAPIDAPI_HOST in your .env file")
        return
    
    # Match type selection with unique key
    match_type = st.radio(
        "Select Match Status:",
        ("Live", "Recent", "Upcoming"),
        horizontal=True,
        key="match_type_selector_main"  # Unique key
    )
    
    # Add refresh button with cooldown
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = 0
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", 
                    disabled=time.time() - st.session_state.last_refresh < 10,
                    use_container_width=True,
                    key="refresh_button"):  # Unique key
            st.session_state.last_refresh = time.time()
            # Clear cache to force API call
            st.cache_data.clear()
            st.rerun()
    
    # Load matches
    with st.spinner(f"Loading {match_type.lower()} matches..."):
        matches_data = get_matches(match_type.lower())
    
    if matches_data:
        # Process and display matches
        process_and_display_matches(matches_data, match_type)
    else:
        st.error("Failed to load matches from API. Please check your API configuration.")

if __name__ == "__main__":
    main()