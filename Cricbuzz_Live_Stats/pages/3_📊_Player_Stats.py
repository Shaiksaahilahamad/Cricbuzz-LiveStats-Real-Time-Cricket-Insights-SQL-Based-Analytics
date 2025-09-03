# pages/3_📊_Player_Stats.py - CLEANED UP VERSION
import streamlit as st
from utils.api_client import (
    search_players,
    get_player_profile,
    get_player_batting_stats,
    get_player_bowling_stats,
    get_player_career_stats
)
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load environment variables
load_dotenv()

def create_batting_visualizations(batting_stats):
    """Create visualizations for batting statistics"""
    if not batting_stats or 'headers' not in batting_stats or 'values' not in batting_stats:
        return None
    
    headers = batting_stats['headers']
    values = batting_stats['values']
    
    # Convert to dictionary for easy access
    stats_dict = {}
    for row in values:
        if 'values' in row and len(row['values']) > 1:
            stat_name = row['values'][0]
            stats_dict[stat_name] = {
                headers[1]: row['values'][1] if len(row['values']) > 1 else 0,
                headers[2]: row['values'][2] if len(row['values']) > 2 else 0, 
                headers[3]: row['values'][3] if len(row['values']) > 3 else 0,
                headers[4]: row['values'][4] if len(row['values']) > 4 else 0
            }
    
    # Prepare data for visualization
    formats = headers[1:]
    visualization_data = []
    
    # Key metrics to visualize
    key_metrics = ['Runs', 'Average', 'Strike Rate', '50s', '100s', 'Highest']
    
    for metric in key_metrics:
        if metric in stats_dict:
            for format_name in formats:
                value = stats_dict[metric].get(format_name, 0)
                # Convert string values to numeric if possible
                try:
                    if isinstance(value, str) and value != 'N/A':
                        # Remove * from highest score (e.g., "183*" -> 183)
                        value = float(value.replace('*', '').replace('-', '0'))
                    else:
                        value = float(value)
                except (ValueError, TypeError):
                    value = 0
                
                visualization_data.append({
                    'Metric': metric,
                    'Format': format_name,
                    'Value': value
                })
    
    if not visualization_data:
        return None
    
    df = pd.DataFrame(visualization_data)
    
    # Create visualizations
    visualizations = {}
    
    # 1. Runs by Format
    runs_data = df[df['Metric'] == 'Runs']
    if not runs_data.empty:
        fig_runs = px.bar(runs_data, x='Format', y='Value', title='Total Runs by Format',
                         color='Format', text='Value')
        fig_runs.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_runs.update_layout(showlegend=False)
        visualizations['runs'] = fig_runs
    
    # 2. Batting Average by Format
    avg_data = df[df['Metric'] == 'Average']
    if not avg_data.empty:
        fig_avg = px.bar(avg_data, x='Format', y='Value', title='Batting Average by Format',
                        color='Format', text='Value')
        fig_avg.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_avg.update_layout(showlegend=False)
        visualizations['average'] = fig_avg
    
    # 3. Centuries and Half-centuries
    centuries_data = df[df['Metric'].isin(['50s', '100s'])]
    if not centuries_data.empty:
        fig_centuries = px.bar(centuries_data, x='Format', y='Value', color='Metric',
                              title='50s and 100s by Format', barmode='group')
        fig_centuries.update_traces(texttemplate='%{y}', textposition='outside')
        visualizations['centuries'] = fig_centuries
    
    # 4. Radar chart for overall batting performance
    radar_metrics = ['Average', 'Strike Rate', 'Runs']
    radar_data = df[df['Metric'].isin(radar_metrics)]
    
    if not radar_data.empty and len(formats) > 0:
        # Normalize values for radar chart
        max_values = radar_data.groupby('Metric')['Value'].max()
        radar_data['Normalized'] = radar_data.apply(
            lambda row: row['Value'] / max_values[row['Metric']] if max_values[row['Metric']] > 0 else 0, 
            axis=1
        )
        
        fig_radar = go.Figure()
        
        for format_name in formats:
            format_data = radar_data[radar_data['Format'] == format_name]
            if not format_data.empty:
                fig_radar.add_trace(go.Scatterpolar(
                    r=format_data['Normalized'].tolist() + [format_data['Normalized'].iloc[0]],
                    theta=radar_metrics + [radar_metrics[0]],
                    fill='toself',
                    name=format_name
                ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title='Batting Performance Radar (Normalized)'
        )
        visualizations['radar'] = fig_radar
    
    return visualizations

def create_bowling_visualizations(bowling_stats):
    """Create visualizations for bowling statistics"""
    if not bowling_stats or 'headers' not in bowling_stats or 'values' not in bowling_stats:
        return None
    
    headers = bowling_stats['headers']
    values = bowling_stats['values']
    
    # Convert to dictionary for easy access
    stats_dict = {}
    for row in values:
        if 'values' in row and len(row['values']) > 1:
            stat_name = row['values'][0]
            stats_dict[stat_name] = {
                headers[1]: row['values'][1] if len(row['values']) > 1 else 0,
                headers[2]: row['values'][2] if len(row['values']) > 2 else 0, 
                headers[3]: row['values'][3] if len(row['values']) > 3 else 0,
                headers[4]: row['values'][4] if len(row['values']) > 4 else 0
            }
    
    # Prepare data for visualization
    formats = headers[1:]
    visualization_data = []
    
    # Key metrics to visualize
    key_metrics = ['Wickets', 'Average', 'Economy', '4W', '5W', '10W']
    
    for metric in key_metrics:
        if metric in stats_dict:
            for format_name in formats:
                value = stats_dict[metric].get(format_name, 0)
                # Convert string values to numeric if possible
                try:
                    if isinstance(value, str) and value != 'N/A':
                        value = float(value.replace('-', '0'))
                    else:
                        value = float(value)
                except (ValueError, TypeError):
                    value = 0
                
                visualization_data.append({
                    'Metric': metric,
                    'Format': format_name,
                    'Value': value
                })
    
    if not visualization_data:
        return None
    
    df = pd.DataFrame(visualization_data)
    
    # Create visualizations
    visualizations = {}
    
    # 1. Wickets by Format
    wickets_data = df[df['Metric'] == 'Wickets']
    if not wickets_data.empty:
        fig_wickets = px.bar(wickets_data, x='Format', y='Value', title='Total Wickets by Format',
                            color='Format', text='Value')
        fig_wickets.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_wickets.update_layout(showlegend=False)
        visualizations['wickets'] = fig_wickets
    
    # 2. Bowling Average by Format
    avg_data = df[df['Metric'] == 'Average']
    if not avg_data.empty:
        fig_avg = px.bar(avg_data, x='Format', y='Value', title='Bowling Average by Format',
                        color='Format', text='Value')
        fig_avg.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_avg.update_layout(showlegend=False)
        visualizations['average'] = fig_avg
    
    # 3. Wicket hauls (4W, 5W, 10W)
    hauls_data = df[df['Metric'].isin(['4W', '5W', '10W'])]
    if not hauls_data.empty:
        fig_hauls = px.bar(hauls_data, x='Format', y='Value', color='Metric',
                          title='Wicket Hauls by Format', barmode='group')
        fig_hauls.update_traces(texttemplate='%{y}', textposition='outside')
        visualizations['hauls'] = fig_hauls
    
    return visualizations

def display_top_batting_stats(batting_stats):
    """Display top batting statistics in a clean, visual format"""
    if not batting_stats:
        return
    
    st.subheader("🏆 Top Batting Performance")
    
    if isinstance(batting_stats, dict) and 'headers' in batting_stats and 'values' in batting_stats:
        headers = batting_stats['headers']
        values = batting_stats['values']
        
        # Convert to dictionary for easy access
        stats_dict = {}
        for row in values:
            if 'values' in row and len(row['values']) > 1:
                stat_name = row['values'][0]
                stats_dict[stat_name] = {
                    headers[1]: row['values'][1] if len(row['values']) > 1 else 'N/A',
                    headers[2]: row['values'][2] if len(row['values']) > 2 else 'N/A', 
                    headers[3]: row['values'][3] if len(row['values']) > 3 else 'N/A',
                    headers[4]: row['values'][4] if len(row['values']) > 4 else 'N/A'
                }
        
        # Create metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        # Check which batting metrics are available
        batting_metrics = [
            ('Matches', 'Matches', col1),
            ('Runs', 'Runs', col2),
            ('Average', 'Average', col3),
            ('Strike Rate', 'SR', col4),
            ('Highest', 'Highest', col1),
            ('50s', '50s', col2),
            ('100s', '100s', col3),
            ('200s', '200s', col4)
        ]
        
        metrics_displayed = 0
        for display_name, stat_key, col in batting_metrics:
            if stat_key in stats_dict:
                # Try to get ODI stats first, fallback to Test
                value = stats_dict[stat_key].get('ODI') or stats_dict[stat_key].get('Test', 'N/A')
                if value != 'N/A':
                    col.metric(display_name, value)
                    metrics_displayed += 1
        
        if metrics_displayed == 0:
            st.info("No batting performance metrics available.")

def display_batting_stats(stats_data):
    """Display batting statistics in a formatted way for Cricbuzz API structure"""
    if not stats_data:
        st.info("No batting statistics available.")
        return
    
    st.subheader("🏏 Batting Statistics")
    
    # Handle the Cricbuzz API table format
    if 'headers' in stats_data and 'values' in stats_data:
        headers = stats_data['headers']
        values = stats_data['values']
        
        # Convert to a more readable format
        stats_dict = {}
        for row in values:
            if 'values' in row and len(row['values']) > 1:
                stat_name = row['values'][0]
                stats_dict[stat_name] = {
                    headers[1]: row['values'][1] if len(row['values']) > 1 else 'N/A',
                    headers[2]: row['values'][2] if len(row['values']) > 2 else 'N/A', 
                    headers[3]: row['values'][3] if len(row['values']) > 3 else 'N/A',
                    headers[4]: row['values'][4] if len(row['values']) > 4 else 'N/A'
                }
        
        # Display key metrics in a nice format
        st.write("**Career Summary**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Key batting metrics to display
        key_metrics = [
            ('Matches', 'Matches', col1),
            ('Runs', 'Runs', col2),
            ('Average', 'Average', col3),
            ('Strike Rate', 'SR', col4),
            ('Highest', 'Highest', col1),
            ('50s', '50s', col2),
            ('100s', '100s', col3),
            ('6s', 'Sixes', col4)
        ]
        
        for display_name, stat_key, col in key_metrics:
            if stat_key in stats_dict:
                test_val = stats_dict[stat_key].get('Test', 'N/A')
                odi_val = stats_dict[stat_key].get('ODI', 'N/A')
                col.metric(display_name, f"Test: {test_val}", f"ODI: {odi_val}")
        
        # Display full statistics table
        st.subheader("📊 Detailed Batting Statistics")
        
        # Create a dataframe for better display
        table_data = []
        for stat_name, formats in stats_dict.items():
            if stat_name not in ['ROWHEADER', '300s', '400s', '200s']:
                row = {'Statistic': stat_name}
                for format_name in headers[1:]:
                    if format_name in formats:
                        row[format_name] = formats[format_name]
                table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    else:
        st.info("Batting statistics format not recognized.")

def display_bowling_stats(bowling_stats):
    """Display bowling statistics in a formatted way"""
    if not bowling_stats:
        st.info("No bowling statistics available for this player.")
        return
    
    st.subheader("🎯 Bowling Statistics")
    
    # Handle different response structures
    if isinstance(bowling_stats, dict):
        if 'headers' in bowling_stats and 'values' in bowling_stats:
            # Cricbuzz API table format (similar to batting)
            headers = bowling_stats['headers']
            values = bowling_stats['values']
            
            # Convert to dictionary
            stats_dict = {}
            for row in values:
                if 'values' in row and len(row['values']) > 1:
                    stat_name = row['values'][0]
                    stats_dict[stat_name] = {
                        headers[1]: row['values'][1] if len(row['values']) > 1 else 'N/A',
                        headers[2]: row['values'][2] if len(row['values']) > 2 else 'N/A', 
                        headers[3]: row['values'][3] if len(row['values']) > 3 else 'N/A',
                        headers[4]: row['values'][4] if len(row['values']) > 4 else 'N/A'
                    }
            
            # Display key metrics
            st.write("**Career Summary**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Key bowling metrics to look for
            bowling_metrics = [
                ('Matches', 'Matches', col1),
                ('Wickets', 'Wickets', col2),
                ('Average', 'Average', col3),
                ('Economy', 'Economy', col4),
                ('Best', 'Best', col1),
                ('4W', '4W', col2),
                ('5W', '5W', col3),
                ('10W', '10W', col4)
            ]
            
            metrics_found = False
            for display_name, stat_key, col in bowling_metrics:
                if stat_key in stats_dict:
                    test_val = stats_dict[stat_key].get('Test', 'N/A')
                    odi_val = stats_dict[stat_key].get('ODI', 'N/A')
                    col.metric(display_name, f"Test: {test_val}", f"ODI: {odi_val}")
                    metrics_found = True
            
            if not metrics_found:
                st.info("No bowling metrics found in the data.")
            
            # Display full statistics table
            st.subheader("📊 Detailed Bowling Statistics")
            
            # Create a dataframe for better display
            table_data = []
            for stat_name, formats in stats_dict.items():
                if stat_name not in ['ROWHEADER']:
                    row = {'Statistic': stat_name}
                    for format_name in headers[1:]:
                        if format_name in formats:
                            row[format_name] = formats[format_name]
                    table_data.append(row)
            
            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No detailed bowling statistics available.")
        
        elif 'career' in bowling_stats:
            # Original format handling
            career = bowling_stats['career']
            st.write("**Career Summary**")
            
            col1, col2, col3, col4 = st.columns(4)
            stats_to_display = [
                ('Matches', 'matches', col1),
                ('Wickets', 'wickets', col2),
                ('Average', 'average', col3),
                ('Economy', 'economy', col4),
                ('Best', 'best', col1),
                ('5W', 'fiveWickets', col2),
                ('10W', 'tenWickets', col3)
            ]
            
            for label, key, col in stats_to_display:
                if key in career:
                    col.metric(label, career[key])
            
            # Format-wise statistics
            if 'format' in bowling_stats:
                st.write("**Format-wise Statistics**")
                for format_name, format_data in bowling_stats['format'].items():
                    with st.expander(f"{format_name.upper()} Format"):
                        for stat_key, stat_value in format_data.items():
                            if stat_value not in [None, '', 0]:
                                st.write(f"**{stat_key}:** {stat_value}")
        
        else:
            # Show all bowling stats as key-value pairs
            st.write("**Bowling Statistics**")
            for key, value in bowling_stats.items():
                if value not in [None, '', 0] and not isinstance(value, (dict, list)):
                    st.write(f"**{key}:** {value}")
    
    elif isinstance(bowling_stats, list):
        # Show as table if it's a list
        st.dataframe(bowling_stats, use_container_width=True)
    
    else:
        st.info("Bowling statistics format not recognized.")

def display_top_bowling_stats(bowling_stats):
    """Display top bowling statistics in a clean, visual format"""
    if not bowling_stats:
        return
    
    st.subheader("🏆 Top Bowling Performance")
    
    if isinstance(bowling_stats, dict):
        if 'headers' in bowling_stats and 'values' in bowling_stats:
            headers = bowling_stats['headers']
            values = bowling_stats['values']
            
            # Convert to dictionary for easy access
            stats_dict = {}
            for row in values:
                if 'values' in row and len(row['values']) > 1:
                    stat_name = row['values'][0]
                    stats_dict[stat_name] = {
                        headers[1]: row['values'][1] if len(row['values']) > 1 else 'N/A',
                        headers[2]: row['values'][2] if len(row['values']) > 2 else 'N/A', 
                        headers[3]: row['values'][3] if len(row['values']) > 3 else 'N/A',
                        headers[4]: row['values'][4] if len(row['values']) > 4 else 'N/A'
                    }
            
            # Create metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            # Check which bowling metrics are available
            bowling_metrics = [
                ('Matches', 'Matches', col1),
                ('Wickets', 'Wickets', col2),
                ('Average', 'Average', col3),
                ('Economy', 'Economy', col4),
                ('Best', 'Best', col1),
                ('4W', '4W', col2),
                ('5W', '5W', col3),
                ('10W', '10W', col4)
            ]
            
            metrics_displayed = 0
            for display_name, stat_key, col in bowling_metrics:
                if stat_key in stats_dict:
                    # Try to get ODI stats first, fallback to Test
                    value = stats_dict[stat_key].get('ODI') or stats_dict[stat_key].get('Test', 'N/A')
                    if value != 'N/A':
                        col.metric(display_name, value)
                        metrics_displayed += 1
            
            if metrics_displayed == 0:
                st.info("No bowling performance metrics available.")
        
        elif 'career' in bowling_stats:
            # Original format handling
            career = bowling_stats['career']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Matches", career.get('matches', 'N/A'))
                st.metric("Best", career.get('best', 'N/A'))
            
            with col2:
                st.metric("Wickets", career.get('wickets', 'N/A'))
                st.metric("4W", career.get('fourWickets', 'N/A'))
            
            with col3:
                st.metric("Average", career.get('average', 'N/A'))
                st.metric("5W", career.get('fiveWickets', 'N/A'))
            
            with col4:
                st.metric("Economy", career.get('economy', 'N/A'))
                st.metric("10W", career.get('tenWickets', 'N/A'))

def display_player_profile(profile):
    """Display player profile information from API response"""
    if not profile:
        st.info("No profile information available.")
        return
    
    st.subheader(f"👤 {profile.get('name', 'N/A')}'s Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Full Name:** {profile.get('name', 'N/A')}")
        st.write(f"**Nickname:** {profile.get('nickName', 'N/A')}")
        st.write(f"**Role:** {profile.get('role', 'N/A')}")
        st.write(f"**Batting Style:** {profile.get('bat', 'N/A')}")
        st.write(f"**Bowling Style:** {profile.get('bowl', 'N/A')}")
    
    with col2:
        st.write(f"**Date of Birth:** {profile.get('DoB', 'N/A')}")
        # Extract age from DoBFormat if available
        dob_format = profile.get('DoBFormat', '')
        age = dob_format.split('(')[-1].replace(')', '') if '(' in dob_format else 'N/A'
        #st.write(f"**Age:** {age}")
        st.write(f"**Birth Place:** {profile.get('birthPlace', 'N/A')}")
        st.write(f"**Height:** {profile.get('height', 'N/A')}")
        st.write(f"**International Team:** {profile.get('intlTeam', 'N/A')}")
    
    # Teams played for
    if 'teams' in profile:
        st.write(f"**Teams:** {profile['teams']}")
    
    # Add Cricbuzz link button
    if st.session_state.selected_player and st.session_state.player_profile:
        player = st.session_state.selected_player
        player_name = player['name']
        player_id = player['id']
        cricbuzz_url = f"https://www.cricbuzz.com/profiles/{player_id}/{player_name.lower().replace(' ', '-')}"
        st.markdown(f"<a href='{cricbuzz_url}' target='_blank'><button style='background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border: none; border-radius: 4px;'>📋 View on Cricbuzz</button></a>", unsafe_allow_html=True)

def clear_search():
    """Clear search results and reset session state"""
    st.session_state.selected_player = None
    st.session_state.player_profile = None
    st.session_state.batting_stats = None
    st.session_state.bowling_stats = None
    st.session_state.players_found = []
    st.session_state.player_options = {}
    st.session_state.last_selected_player = None
    st.session_state.auto_loaded = False
    # Clear the search input by setting it to empty string
    st.session_state.player_search_input = ""

def display_page_description():
    """Display a detailed description of the Player Stats page"""
    st.markdown("---")
    st.subheader("ℹ️ About This Page")
    
    with st.expander("Learn more about the Player Statistics functionality"):
        st.markdown("""
        ### 📊 Player Statistics Dashboard
        
        This interactive dashboard provides comprehensive cricket player statistics with the following features:
        
        #### 🔍 Player Search
        - Search for any international cricket player by name
        - Automatic suggestions with player international teams
        - Single-click loading for players with unique names
        
        #### 👤 Player Profile
        - Complete biographical information
        - Playing role and style details
        - Direct link to Cricbuzz profile
        
        #### 📈 Performance Visualizations
        - **Batting Performance**: Runs, averages, strike rates across formats
        - **Bowling Performance**: Wickets, averages, economy rates
        - **Interactive Charts**: Bar charts, radar plots, and comparative visuals
        - **Format-wise Analysis**: Test, ODI, and T20 statistics comparison
        
        #### 📊 Detailed Statistics
        - Comprehensive career statistics in tabular format
        - Key performance metrics highlighted
        - Format-specific breakdowns
        
        #### 🏆 Top Performance Highlights
        - Quick glance at most important career achievements
        - Key metrics displayed in an easy-to-read format
        
        #### 🔧 Technical Features
        - Real-time data from Cricbuzz API
        - Responsive design that works on all devices
        - Interactive visualizations with Plotly
        - Session state management for seamless navigation
        
        **Note**: Data is sourced from Cricbuzz via RapidAPI and may have slight delays in updates compared to live matches.
        """)

def main():
    st.header("📊 Cricket Player Statistics")
    
    # API key check
    if not os.getenv('RAPIDAPI_KEY') or not os.getenv('RAPIDAPI_HOST'):
        st.error("❌ API configuration missing. Please check your .env file")
        st.info("Make sure you have RAPIDAPI_KEY and RAPIDAPI_HOST in your .env file")
        return
    
    # Player search section with aligned buttons
    st.subheader("🔍 Search for Player")
    
    # Create a container for the search row
    search_container = st.container()
    with search_container:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            search_name = st.text_input("Enter player name:", 
                                      placeholder="e.g., Virat Kohli",
                                      key="player_search_input",
                                      label_visibility="collapsed")
        with col2:
            search_clicked = st.button("🔍 Search", use_container_width=True, key="search_button")
        with col3:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True, key="clear_button", on_click=clear_search)
    
    # Initialize session state
    if 'selected_player' not in st.session_state:
        st.session_state.selected_player = None
    if 'player_profile' not in st.session_state:
        st.session_state.player_profile = None
    if 'batting_stats' not in st.session_state:
        st.session_state.batting_stats = None
    if 'bowling_stats' not in st.session_state:
        st.session_state.bowling_stats = None
    if 'players_found' not in st.session_state:
        st.session_state.players_found = []
    if 'player_options' not in st.session_state:
        st.session_state.player_options = {}
    if 'last_selected_player' not in st.session_state:
        st.session_state.last_selected_player = None
    if 'auto_loaded' not in st.session_state:
        st.session_state.auto_loaded = False
    
    if search_clicked and search_name:
        with st.spinner("Searching for players..."):
            players_found = search_players(search_name)
            st.session_state.players_found = players_found
            st.session_state.auto_loaded = False
            
            if players_found:
                player_options = {}
                for idx, player in enumerate(players_found, 1):
                    player_name = player.get('name', 'Unknown Player')
                    player_id = player.get('id')
                    
                    # Get the player profile to access international team
                    if player_id:
                        player_profile = get_player_profile(player_id)
                        international_team = player_profile.get('intlTeam', 'N/A') if player_profile else 'N/A'
                    
                    if player_id and player_name:
                        # Format as "1. Player Name - (International Team)"
                        key = f"{idx}. {player_name} - ({international_team})"
                        player_options[key] = {
                            'id': player_id,
                            'name': player_name,
                            'international_team': international_team
                        }
                
                st.session_state.player_options = player_options
                
                if player_options:
                    # If only one player is found, automatically load their data
                    if len(player_options) == 1:
                        selected_option = list(player_options.keys())[0]
                        selected_player = player_options[selected_option]
                        st.session_state.selected_player = selected_player
                        st.session_state.last_selected_player = selected_option
                        
                        with st.spinner(f"Loading {selected_player['name']}'s data..."):
                            profile = get_player_profile(selected_player['id'])
                            batting = get_player_batting_stats(selected_player['id'])
                            bowling = get_player_bowling_stats(selected_player['id'])
                            
                            st.session_state.player_profile = profile
                            st.session_state.batting_stats = batting
                            st.session_state.bowling_stats = bowling
                            st.session_state.auto_loaded = True
                        
                        st.success(f"✅ Found and loaded data for {selected_player['name']}")
                    else:
                        st.success(f"✅ Found {len(players_found)} matching players")
                else:
                    st.warning("No valid players found in the search results.")
            else:
                st.warning("No players found with that name. Try a different search term.")
                st.session_state.selected_player = None
                st.session_state.player_profile = None
                st.session_state.batting_stats = None
                st.session_state.bowling_stats = None
    
    # Display player selection dropdown only if multiple players were found
    if (st.session_state.player_options and 
        len(st.session_state.player_options) > 1 and
        not st.session_state.auto_loaded):
        
        st.subheader("👥 Select Player")
        
        selected_option = st.selectbox(
            "Choose a player:",
            options=list(st.session_state.player_options.keys()),
            key="player_selector"
        )
        
        # Automatically load player data when a selection is made
        if selected_option and selected_option != st.session_state.get('last_selected_player', ''):
            selected_player = st.session_state.player_options[selected_option]
            st.session_state.selected_player = selected_player
            st.session_state.last_selected_player = selected_option
            
            with st.spinner(f"Loading {selected_player['name']}'s data..."):
                profile = get_player_profile(selected_player['id'])
                batting = get_player_batting_stats(selected_player['id'])
                bowling = get_player_bowling_stats(selected_player['id'])
                
                st.session_state.player_profile = profile
                st.session_state.batting_stats = batting
                st.session_state.bowling_stats = bowling
            
            st.success(f"✅ Loaded data for {selected_player['name']}")
    
    # Display player information if available
    if (st.session_state.selected_player and 
        st.session_state.player_profile):
        
        player = st.session_state.selected_player
        profile = st.session_state.player_profile
        
        # Display profile information
        display_player_profile(profile)
        
        # Top Performance Section
        st.markdown("---")
        
        # Top Batting Stats
        if st.session_state.batting_stats:
            display_top_batting_stats(st.session_state.batting_stats)
        
        # Top Bowling Stats (if available)
        if st.session_state.bowling_stats:
            display_top_bowling_stats(st.session_state.bowling_stats)
        

                

        st.markdown("---")
        st.subheader("📊 Detailed Statistics")
        
        stats_tab1, stats_tab2 = st.tabs(["🏏 Batting Details", "🎯 Bowling Details"])
        
        with stats_tab1:
            if st.session_state.batting_stats:
                # Show detailed batting stats first
                #st.subheader("📋 Batting Statistics")
                display_batting_stats(st.session_state.batting_stats)
                
                # Show batting visualizations after the table
                batting_viz = create_batting_visualizations(st.session_state.batting_stats)
                if batting_viz:
                    st.markdown("---")
                    st.subheader("📈 Batting Visualizations")
                    
                    # Arrange graphs in columns (2 side by side)
                    if 'runs' in batting_viz and 'average' in batting_viz:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(batting_viz['runs'], use_container_width=True)
                        with col2:
                            st.plotly_chart(batting_viz['average'], use_container_width=True)
                    
                    # Centuries and radar charts side by side if available
                    if 'centuries' in batting_viz and 'radar' in batting_viz:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(batting_viz['centuries'], use_container_width=True)
                        with col2:
                            st.plotly_chart(batting_viz['radar'], use_container_width=True)
                    elif 'centuries' in batting_viz:
                        st.plotly_chart(batting_viz['centuries'], use_container_width=True)
                    elif 'radar' in batting_viz:
                        st.plotly_chart(batting_viz['radar'], use_container_width=True)
            else:
                st.info("No batting statistics available.")
        
        with stats_tab2:
            if st.session_state.bowling_stats:
                # Show detailed bowling stats first
                #st.subheader("📋 Bowling Statistics")
                display_bowling_stats(st.session_state.bowling_stats)
                
                # Show bowling visualizations after the table
                bowling_viz = create_bowling_visualizations(st.session_state.bowling_stats)
                if bowling_viz:
                    st.markdown("---")
                    st.subheader("📈 Bowling Visualizations")
                    
                    # Arrange graphs in columns (2 side by side)
                    if 'wickets' in bowling_viz and 'average' in bowling_viz:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(bowling_viz['wickets'], use_container_width=True)
                        with col2:
                            st.plotly_chart(bowling_viz['average'], use_container_width=True)
                    
                    # Hauls chart (if available, could add another chart here if needed)
                    if 'hauls' in bowling_viz:
                        st.plotly_chart(bowling_viz['hauls'], use_container_width=True)
            else:
                st.info("No bowling statistics available for this player.")
    
    # Add the page description at the end
    display_page_description()

if __name__ == "__main__":
    main()