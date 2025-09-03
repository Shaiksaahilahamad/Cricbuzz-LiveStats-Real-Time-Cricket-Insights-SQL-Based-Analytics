# pages/2_🏏_Live_Matches.py
import streamlit as st
import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load environment variables
load_dotenv()

def safe_float(val, default=0.0):
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return default


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
        
        # Debug information
        st.sidebar.info(f"API Status: {response.status_code}")
        
        # Check for rate limiting (429 error)
        if response.status_code == 429:
            error_msg = f"API Rate Limit Exceeded (429). Response: {response.text}"
            return {"error": "rate_limit", "message": error_msg, "status_code": 429}
        
        # Check if response is empty
        if not response.content:
            return {"error": "empty_response", "message": "API returned empty response", "status_code": response.status_code}
        
        # Check if response is valid JSON
        try:
            data = response.json()
            return data
        except ValueError as e:
            # Response is not JSON, show what we got
            error_msg = f"API returned non-JSON response. Status: {response.status_code}, Content: {response.text[:100]}"
            return {"error": "invalid_json", "message": error_msg, "status_code": response.status_code}
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {e}"
        return {"error": "request_error", "message": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        return {"error": "unexpected_error", "message": error_msg}

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
        
        # Check for rate limiting (429 error)
        if response.status_code == 429:
            error_msg = f"API Rate Limit Exceeded (429). Response: {response.text}"
            return {"error": "rate_limit", "message": error_msg}
        
        # Check if response is empty
        if not response.content:
            return {"error": "empty_response", "message": "API returned empty response"}
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response.status_code == 429:
            error_msg = f"API Rate Limit Exceeded (429). Response: {e.response.text}"
            return {"error": "rate_limit", "message": error_msg}
        else:
            error_msg = f"HTTP error: {e}"
            return {"error": "http_error", "message": error_msg}
    except Exception as e:
        error_msg = f"Error: {e}"
        return {"error": "error", "message": error_msg}

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
    """Display detailed scorecard data with visualizations instead of tables"""
    
    # Check if we have valid data
    if not detailed_data or not isinstance(detailed_data, dict):
        st.error("No detailed scorecard data available")
        return
    
    # Check for error response
    if detailed_data.get("error"):
        st.error(f"Error: {detailed_data.get('message', 'Unknown error')}")
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
            st.metric("Run Rate", round(float(innings.get('runrate', 0)), 2))
        
        # BATTING DATA - from 'batsman' list
        if 'batsman' in innings and isinstance(innings['batsman'], list) and innings['batsman']:
            st.markdown("### 🧍 Batting Performance")
            batting_data = []
            
            for batsman in innings['batsman']:
                if isinstance(batsman, dict):
                    runs = batsman.get('runs', batsman.get('score', 0))
                    balls = batsman.get('balls', batsman.get('ballsFaced', 0))
                    strike_rate = safe_float(batsman.get("strkrate") or batsman.get("strikeRate") or batsman.get("sr"))
                    fours = batsman.get('fours', batsman.get('four', 0))
                    sixes = batsman.get('sixes', batsman.get('six', 0))
                    
                    batting_data.append({
                        "Batsman": batsman.get('name', batsman.get('batName', 'N/A')),
                        "Runs": runs,
                        "Balls": balls,
                        "4s": fours,
                        "6s": sixes,
                        "SR": strike_rate,
                        "Status": batsman.get('outdec', batsman.get('dismissal', 'not out')),
                        "Boundaries": fours + sixes,
                        "DotBalls": balls - (fours + sixes) if balls > 0 else 0
                    })
            
            if batting_data:
                df_batting = pd.DataFrame(batting_data)
                
                # Display raw data first
                st.markdown("#### 📋 Raw Batting Data")
                st.dataframe(df_batting[['Batsman', 'Runs', 'Balls', '4s', '6s', 'SR', 'Status']], 
                            use_container_width=True, hide_index=True)
                
                # Add batting performance summary
                top_scorer = df_batting.loc[df_batting['Runs'].idxmax()]
                best_striker = df_batting.loc[df_batting['SR'].idxmax()]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏆 Top Scorer", f"{top_scorer['Batsman']} - {top_scorer['Runs']} runs")
                with col2:
                    st.metric("⚡ Best Strike Rate", f"{best_striker['Batsman']} - {best_striker['SR']}")
                
                st.markdown("---")
                st.markdown("#### 📈 Batting Visualizations")
                
                # Create tabs for different batting visualizations
                tab1, tab2, tab3 = st.tabs(["Runs Distribution", "Strike Rate Analysis", "Boundary Analysis"])
                
                with tab1:
                    # Runs distribution chart
                    fig_runs = px.bar(df_batting, x='Batsman', y='Runs', 
                                     color='Runs', color_continuous_scale='Viridis',
                                     title=f'Runs Scored by Each Batsman - {innings_title}')
                    fig_runs.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_runs, use_container_width=True)
                
                with tab2:
                    # Strike rate analysis
                    fig_sr = go.Figure()
                    fig_sr.add_trace(go.Scatter(x=df_batting['Batsman'], y=df_batting['SR'],
                                               mode='markers+lines', name='Strike Rate',
                                               marker=dict(size=df_batting['Runs']/10 + 10, 
                                                          color=df_batting['Runs'], 
                                                          colorscale='Rainbow',
                                                          showscale=True,
                                                          colorbar=dict(title="Runs"))))
                    fig_sr.update_layout(title=f'Strike Rate Analysis - {innings_title}',
                                        xaxis_title='Batsman', yaxis_title='Strike Rate',
                                        xaxis_tickangle=-45)
                    st.plotly_chart(fig_sr, use_container_width=True)
                
                with tab3:
                    # Boundary analysis
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_boundaries = px.pie(df_batting, values='Boundaries', names='Batsman',
                                               title=f'Boundary Distribution - {innings_title}')
                        st.plotly_chart(fig_boundaries, use_container_width=True)
                    
                    with col2:
                        # 4s vs 6s comparison
                        fig_4s6s = go.Figure(data=[
                            go.Bar(name='4s', x=df_batting['Batsman'], y=df_batting['4s']),
                            go.Bar(name='6s', x=df_batting['Batsman'], y=df_batting['6s'])
                        ])
                        fig_4s6s.update_layout(barmode='stack', 
                                              title=f'4s vs 6s - {innings_title}',
                                              xaxis_tickangle=-45)
                        st.plotly_chart(fig_4s6s, use_container_width=True)
                    
            else:
                st.info("No valid batting data found")
        else:
            st.info("No batting data available")
        
        # BOWLING DATA - from 'bowler' list
        if 'bowler' in innings and isinstance(innings['bowler'], list) and innings['bowler']:
            st.markdown("### 🎯 Bowling Performance")
            bowling_data = []
            
            for bowler in innings['bowler']:
                if isinstance(bowler, dict):
                    wickets = bowler.get('wickets', bowler.get('wicketsTaken', 0))
                    economy = round(float(bowler.get('economy', bowler.get('economyRate', 0))), 2)
                    runs = bowler.get('runs', bowler.get('runsConceded', 0))
                    overs = bowler.get('overs', bowler.get('oversBowled', 0))
                    maidens = bowler.get('maidens', bowler.get('maidenOvers', 0))
                    
                    bowling_data.append({
                        "Bowler": bowler.get('name', bowler.get('bowlName', 'N/A')),
                        "Overs": overs,
                        "Maidens": maidens,
                        "Runs": runs,
                        "Wickets": wickets,
                        "Economy": economy,
                        "Wides": bowler.get('wides', bowler.get('wide', 0)),
                        "StrikeRate": round(runs/wickets, 2) if wickets > 0 else 0
                    })
            
            if bowling_data:
                df_bowling = pd.DataFrame(bowling_data)
                
                # Display raw data first
                st.markdown("#### 📋 Raw Bowling Data")
                st.dataframe(df_bowling[['Bowler', 'Overs', 'Maidens', 'Runs', 'Wickets', 'Economy', 'Wides']], 
                            use_container_width=True, hide_index=True)
                
                # Add bowling performance summary
                most_wickets = df_bowling.loc[df_bowling['Wickets'].idxmax()]
                best_economy = df_bowling.loc[df_bowling['Economy'].idxmin()]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏆 Most Wickets", f"{most_wickets['Bowler']} - {most_wickets['Wickets']}/{most_wickets['Runs']}")
                with col2:
                    st.metric("💰 Best Economy", f"{best_economy['Bowler']} - {best_economy['Economy']}")
                
                st.markdown("---")
                st.markdown("#### 📈 Bowling Visualizations")
                
                # Create tabs for different bowling visualizations
                tab1, tab2, tab3 = st.tabs(["Wickets Analysis", "Economy Analysis", "Performance Matrix"])
                
                with tab1:
                    # Wickets analysis
                    fig_wickets = px.bar(df_bowling, x='Bowler', y='Wickets',
                                        color='Wickets', color_continuous_scale='Reds',
                                        title=f'Wickets Taken - {innings_title}')
                    fig_wickets.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_wickets, use_container_width=True)
                
                with tab2:
                    # Economy analysis
                    fig_economy = px.scatter(df_bowling, x='Bowler', y='Economy',
                                            size='Wickets', color='Runs',
                                            title=f'Economy Rate vs Wickets - {innings_title}',
                                            hover_data=['Overs', 'Maidens'])
                    fig_economy.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_economy, use_container_width=True)
                
                with tab3:
                    # Performance matrix
                    fig_matrix = make_subplots(rows=1, cols=2, subplot_titles=('Wickets by Economy', 'Maidens by Overs'))
                    
                    fig_matrix.add_trace(
                        go.Scatter(x=df_bowling['Economy'], y=df_bowling['Wickets'],
                                  mode='markers', marker=dict(size=15, color=df_bowling['Runs'],
                                                             colorscale='Viridis', showscale=True),
                                  text=df_bowling['Bowler'], name='Economy vs Wickets'),
                        row=1, col=1
                    )
                    
                    fig_matrix.add_trace(
                        go.Bar(x=df_bowling['Bowler'], y=df_bowling['Maidens'], name='Maidens',
                              marker_color='lightblue'),
                        row=1, col=2
                    )
                    
                    fig_matrix.update_layout(height=400, showlegend=False,
                                           title_text=f'Bowling Performance Matrix - {innings_title}')
                    fig_matrix.update_xaxes(tickangle=-45, row=1, col=2)
                    st.plotly_chart(fig_matrix, use_container_width=True)
                    
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
                # Check for error response
                if detailed_data.get("error"):
                    st.error(f"Error: {detailed_data.get('message', 'Unknown error')}")
                else:
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
    
    # Check for error response
    if matches_data and matches_data.get("error"):
        error_type = matches_data.get("error")
        error_msg = matches_data.get("message", "Unknown error")
        
        if error_type == "rate_limit":
            st.error(f"⚠️ API Rate Limit Exceeded: {error_msg}")
        elif error_type == "empty_response":
            st.info("🏏 There are no matches at the moment. Please check back later.")
        elif error_type == "invalid_json":
            st.error(f"❌ API Error: {error_msg}")
            st.info("This might be a temporary issue with the API. Please try again later.")
        else:
            st.error(f"❌ Error: {error_msg}")
        return
    
    if not matches_data or 'typeMatches' not in matches_data:
        st.info("🏏 There are no matches at the moment. Please check back later.")
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
            st.info("🏏 There are no matches at the moment. Please check back later.")
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
    
    # Add API status info in sidebar
    st.sidebar.subheader("API Status")
    if os.getenv('RAPIDAPI_KEY'):
        st.sidebar.success("✅ API Key configured")
    else:
        st.sidebar.error("❌ API Key missing")
    
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
        st.info("🏏 There are no matches at the moment. Please check back later.")

if __name__ == "__main__":
    main()
