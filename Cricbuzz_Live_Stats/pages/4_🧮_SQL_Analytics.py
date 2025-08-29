# pages/4_🧮_SQL_Analytics.py
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

class CricketDataManager:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'cricket_db'),
            'port': os.getenv('DB_PORT', 3306)
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as e:
            st.error(f"Database connection error: {e}")
            return None
    
    def setup_database(self):
        """Initialize database tables"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Create players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    country VARCHAR(100),
                    role VARCHAR(50),
                    batting_style VARCHAR(100),
                    bowling_style VARCHAR(100),
                    date_of_birth DATE,
                    api_player_id INT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create matches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id BIGINT PRIMARY KEY,
                    team1 VARCHAR(100),
                    team2 VARCHAR(100),
                    date DATETIME,
                    venue VARCHAR(200),
                    city VARCHAR(100),
                    country VARCHAR(100),
                    status VARCHAR(50),
                    result VARCHAR(200),
                    match_type VARCHAR(50),
                    toss_winner VARCHAR(100),
                    toss_decision VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create player_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    player_id INT NOT NULL,
                    match_id INT NOT NULL,
                    runs INT DEFAULT 0,
                    wickets INT DEFAULT 0,
                    balls_faced INT DEFAULT 0,
                    strike_rate DECIMAL(5,2) DEFAULT 0.0,
                    format VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players(id),
                    FOREIGN KEY (match_id) REFERENCES matches(match_id)
                )
            """)
            
            # Create venues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS venues (
                    venue_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    city VARCHAR(100),
                    country VARCHAR(100),
                    capacity INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create series table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS series (
                    series_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    host_country VARCHAR(100),
                    match_type VARCHAR(50),
                    start_date DATE,
                    end_date DATE,
                    total_matches INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create batting_partnerships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batting_partnerships (
                    partnership_id INT AUTO_INCREMENT PRIMARY KEY,
                    match_id INT,
                    player1_id INT,
                    player2_id INT,
                    runs INT,
                    innings INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches(match_id),
                    FOREIGN KEY (player1_id) REFERENCES players(id),
                    FOREIGN KEY (player2_id) REFERENCES players(id)
                )
            """)
            
            conn.commit()
            st.success("Database setup completed successfully")
            return True
            
        except Error as e:
            st.error(f"Database setup error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute SQL query and return results"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Error as e:
            st.error(f"Error executing query: {e}")
            return None
        finally:
            if conn.is_connected():
                conn.close()

def display_sql_analytics():
    db_manager = CricketDataManager()
    
    st.title("🏏 Cricbuzz LiveStats - SQL Analytics")
    
    # Query selection
    st.header("📊 SQL Query Interface")
    
    # Define all 25 queries with descriptions
    query_options = {
        "Question 1": "Find all players who represent India",
        "Question 2": "Show cricket matches played in the last 30 days",
        "Question 3": "Top 10 highest run scorers in ODI cricket",
        "Question 4": "Venues with seating capacity > 50,000",
        "Question 5": "Count of matches won by each team",
        "Question 6": "Player count by playing role",
        "Question 7": "Highest individual score in each format",
        "Question 8": "Cricket series starting in 2024",
        "Question 9": "All-rounders with 1000+ runs and 50+ wickets",
        "Question 10": "Last 20 completed matches details",
        "Question 11": "Player performance across different formats",
        "Question 12": "Team performance home vs away",
        "Question 13": "Batting partnerships with 100+ runs",
        "Question 14": "Bowling performance at different venues",
        "Question 15": "Player performance in close matches",
        "Question 16": "Batting performance changes over years",
        "Question 17": "Toss advantage analysis",
        "Question 18": "Most economical bowlers in limited-overs",
        "Question 19": "Batsmen consistency analysis",
        "Question 20": "Player performance by format",
        "Question 21": "Comprehensive player ranking system",
        "Question 22": "Head-to-head match prediction analysis",
        "Question 23": "Recent player form analysis",
        "Question 24": "Successful batting partnerships",
        "Question 25": "Player performance evolution over time"
    }
    
    # Create dropdown for query selection
    selected_query = st.selectbox(
        "Select a query to execute:",
        options=list(query_options.keys()),
        format_func=lambda x: f"{x}: {query_options[x]}"
    )
    
    # Define the actual SQL queries
    queries = {
        "Question 1": """
            SELECT name, role, batting_style, bowling_style 
            FROM players 
            WHERE country = 'India' 
            ORDER BY name;
        """,
        
        "Question 2": """
            SELECT match_id, team1, team2, date, venue, city, result 
            FROM matches 
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) 
            ORDER BY date DESC;
        """,
        
        "Question 3": """
            SELECT p.name, SUM(ps.runs) as total_runs, 
                   ROUND(SUM(ps.runs) / NULLIF(COUNT(CASE WHEN ps.runs IS NOT NULL THEN 1 END), 0), 2) as batting_avg,
                   SUM(CASE WHEN ps.runs >= 100 THEN 1 ELSE 0 END) as centuries
            FROM player_stats ps 
            JOIN players p ON ps.player_id = p.id 
            WHERE ps.format = 'ODI' 
            GROUP BY p.id, p.name 
            ORDER BY total_runs DESC 
            LIMIT 10;
        """,
        
        "Question 4": """
            SELECT name, city, country, capacity 
            FROM venues 
            WHERE capacity > 50000 
            ORDER BY capacity DESC;
        """,
        
        "Question 5": """
            SELECT 
                CASE 
                    WHEN result LIKE '%won by%' THEN SUBSTRING_INDEX(SUBSTRING_INDEX(result, ' ', 1), ' won', 1)
                    ELSE 'Unknown'
                END as winning_team,
                COUNT(*) as wins
            FROM matches 
            WHERE result IS NOT NULL AND result LIKE '%won by%'
            GROUP BY winning_team
            ORDER BY wins DESC;
        """,
        
        "Question 6": """
            SELECT role, COUNT(*) as player_count 
            FROM players 
            WHERE role IS NOT NULL 
            GROUP BY role 
            ORDER BY player_count DESC;
        """,
        
        "Question 7": """
            SELECT format, MAX(runs) as highest_score 
            FROM player_stats 
            WHERE format IN ('Test', 'ODI', 'T20I') 
            GROUP BY format 
            ORDER BY highest_score DESC;
        """,
        
        "Question 8": """
            SELECT name, host_country, match_type, start_date, total_matches 
            FROM series 
            WHERE YEAR(start_date) = 2024 
            ORDER BY start_date;
        """,
        
        "Question 9": """
            SELECT p.name, 
                   SUM(CASE WHEN ps.runs IS NOT NULL THEN ps.runs ELSE 0 END) as total_runs,
                   SUM(CASE WHEN ps.wickets IS NOT NULL THEN ps.wickets ELSE 0 END) as total_wickets,
                   ps.format
            FROM player_stats ps 
            JOIN players p ON ps.player_id = p.id 
            WHERE p.role LIKE '%All-rounder%' OR p.role LIKE '%Allrounder%'
            GROUP BY p.id, p.name, ps.format
            HAVING total_runs > 1000 AND total_wickets > 50 
            ORDER BY total_runs DESC;
        """,
        
        "Question 10": """
            SELECT m.match_id, m.team1, m.team2, m.date, m.venue, m.result,
                   CASE 
                       WHEN m.result LIKE CONCAT(m.team1, '%') THEN m.team1
                       WHEN m.result LIKE CONCAT(m.team2, '%') THEN m.team2
                       ELSE 'Draw/Tie'
                   END as winning_team,
                   CASE 
                       WHEN m.result LIKE '%runs%' THEN 'runs'
                       WHEN m.result LIKE '%wickets%' THEN 'wickets'
                       ELSE 'other'
                   END as victory_type,
                   REGEXP_SUBSTR(m.result, '[0-9]+') as victory_margin
            FROM matches m 
            WHERE m.status = 'Completed' 
            ORDER BY m.date DESC 
            LIMIT 20;
        """,
        
        "Question 11": """
            SELECT p.name,
                   SUM(CASE WHEN ps.format = 'Test' THEN ps.runs ELSE 0 END) as test_runs,
                   SUM(CASE WHEN ps.format = 'ODI' THEN ps.runs ELSE 0 END) as odi_runs,
                   SUM(CASE WHEN ps.format = 'T20I' THEN ps.runs ELSE 0 END) as t20i_runs,
                   ROUND(SUM(ps.runs) / NULLIF(COUNT(CASE WHEN ps.runs IS NOT NULL THEN 1 END), 0), 2) as overall_avg
            FROM player_stats ps 
            JOIN players p ON ps.player_id = p.id 
            WHERE ps.format IN ('Test', 'ODI', 'T20I')
            GROUP BY p.id, p.name
            HAVING COUNT(DISTINCT ps.format) >= 2
            ORDER BY overall_avg DESC;
        """,
        
        "Question 12": """
            SELECT 
                team,
                SUM(CASE WHEN is_home = 1 THEN wins ELSE 0 END) as home_wins,
                SUM(CASE WHEN is_home = 0 THEN wins ELSE 0 END) as away_wins
            FROM (
                SELECT 
                    CASE 
                        WHEN m.result LIKE CONCAT(t.team_name, '%') THEN t.team_name
                    END as team,
                    CASE 
                        WHEN m.country = t.country THEN 1 
                        ELSE 0 
                    END as is_home,
                    COUNT(*) as wins
                FROM matches m
                JOIN (
                    SELECT DISTINCT team1 as team_name, country 
                    FROM matches 
                    UNION 
                    SELECT DISTINCT team2 as team_name, country 
                    FROM matches
                ) t ON (m.team1 = t.team_name OR m.team2 = t.team_name)
                WHERE m.result LIKE CONCAT(t.team_name, '%')
                GROUP BY team, is_home
            ) subquery
            GROUP BY team
            ORDER BY home_wins + away_wins DESC;
        """,
        
        "Question 13": """
            SELECT p1.name as player1, p2.name as player2, 
                   bp.runs as partnership_runs, bp.innings
            FROM batting_partnerships bp
            JOIN players p1 ON bp.player1_id = p1.id
            JOIN players p2 ON bp.player2_id = p2.id
            WHERE bp.runs >= 100
            ORDER BY bp.runs DESC;
        """,
        
        "Question 14": """
            SELECT p.name, m.venue, 
                   ROUND(AVG(ps.strike_rate), 2) as avg_economy,
                   SUM(ps.wickets) as total_wickets,
                   COUNT(DISTINCT ps.match_id) as matches_played
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN matches m ON ps.match_id = m.match_id
            WHERE ps.balls_faced >= 24  -- At least 4 overs (24 balls)
            GROUP BY p.id, p.name, m.venue
            HAVING COUNT(DISTINCT ps.match_id) >= 3
            ORDER BY avg_economy ASC;
        """,
        
        "Question 15": """
            SELECT p.name,
                   ROUND(AVG(ps.runs), 2) as avg_runs_close_matches,
                   COUNT(DISTINCT ps.match_id) as close_matches_played,
                   SUM(CASE WHEN m.result LIKE CONCAT(p.country, '%') THEN 1 ELSE 0 END) as wins_in_close_matches
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN matches m ON ps.match_id = m.match_id
            WHERE (m.result LIKE '%runs' AND CAST(REGEXP_SUBSTR(m.result, '[0-9]+') AS UNSIGNED) < 50)
               OR (m.result LIKE '%wickets' AND CAST(REGEXP_SUBSTR(m.result, '[0-9]+') AS UNSIGNED) < 5)
            GROUP BY p.id, p.name
            HAVING close_matches_played >= 3
            ORDER BY avg_runs_close_matches DESC;
        """,
        
        "Question 16": """
            SELECT p.name, 
                   YEAR(m.date) as year,
                   ROUND(AVG(ps.runs), 2) as avg_runs_per_match,
                   ROUND(AVG(ps.strike_rate), 2) as avg_strike_rate,
                   COUNT(DISTINCT ps.match_id) as matches_played
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN matches m ON ps.match_id = m.match_id
            WHERE YEAR(m.date) >= 2020
            GROUP BY p.id, p.name, YEAR(m.date)
            HAVING matches_played >= 5
            ORDER BY p.name, year DESC;
        """,
        
        "Question 17": """
            SELECT 
                toss_decision,
                COUNT(*) as total_matches,
                SUM(CASE WHEN result LIKE CONCAT(toss_winner, '%') THEN 1 ELSE 0 END) as wins_after_toss,
                ROUND(SUM(CASE WHEN result LIKE CONCAT(toss_winner, '%') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
            FROM matches
            WHERE toss_decision IS NOT NULL AND result IS NOT NULL
            GROUP BY toss_decision
            ORDER BY win_percentage DESC;
        """,
        
        "Question 18": """
            SELECT p.name,
                   ps.format,
                   ROUND(SUM(ps.runs) / NULLIF(SUM(ps.balls_faced), 0) * 100, 2) as economy_rate,
                   SUM(ps.wickets) as total_wickets,
                   COUNT(DISTINCT ps.match_id) as matches_played
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            WHERE ps.format IN ('ODI', 'T20I') 
              AND ps.balls_faced > 0
            GROUP BY p.id, p.name, ps.format
            HAVING matches_played >= 10 AND AVG(ps.balls_faced) >= 12  -- At least 2 overs per match on average
            ORDER BY economy_rate ASC;
        """,
        
        "Question 19": """
            SELECT p.name,
                   ROUND(AVG(ps.runs), 2) as avg_runs,
                   ROUND(STDDEV(ps.runs), 2) as std_dev_runs,
                   COUNT(DISTINCT ps.match_id) as innings_played
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN matches m ON ps.match_id = m.match_id
            WHERE ps.balls_faced >= 10 
              AND YEAR(m.date) >= 2022
            GROUP BY p.id, p.name
            HAVING innings_played >= 5
            ORDER BY std_dev_runs ASC;
        """,
        
        "Question 20": """
            SELECT p.name,
                   SUM(CASE WHEN ps.format = 'Test' THEN 1 ELSE 0 END) as test_matches,
                   ROUND(AVG(CASE WHEN ps.format = 'Test' THEN ps.runs END), 2) as test_avg,
                   SUM(CASE WHEN ps.format = 'ODI' THEN 1 ELSE 0 END) as odi_matches,
                   ROUND(AVG(CASE WHEN ps.format = 'ODI' THEN ps.runs END), 2) as odi_avg,
                   SUM(CASE WHEN ps.format = 'T20I' THEN 1 ELSE 0 END) as t20_matches,
                   ROUND(AVG(CASE WHEN ps.format = 'T20I' THEN ps.runs END), 2) as t20_avg
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            GROUP BY p.id, p.name
            HAVING (test_matches + odi_matches + t20_matches) >= 20
            ORDER BY (test_avg + odi_avg + t20_avg) DESC;
        """,
        
        "Question 21": """
            SELECT p.name,
                   ps.format,
                   -- Batting points
                   (SUM(ps.runs) * 0.01) + 
                   (AVG(CASE WHEN ps.runs IS NOT NULL THEN ps.runs END) * 0.5) + 
                   (AVG(ps.strike_rate) * 0.3) as batting_points,
                   -- Bowling points
                   (SUM(ps.wickets) * 2) + 
                   ((50 - AVG(CASE WHEN ps.wickets > 0 THEN ps.runs/ps.wickets ELSE 50 END)) * 0.5) + 
                   ((6 - AVG(ps.strike_rate)) * 2) as bowling_points,
                   -- Total points (simplified)
                   (SUM(ps.runs) * 0.01) + (SUM(ps.wickets) * 2) as total_points
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            WHERE ps.format IN ('Test', 'ODI', 'T20I')
            GROUP BY p.id, p.name, ps.format
            ORDER BY ps.format, total_points DESC;
        """,
        
        "Question 22": """
            SELECT 
                team1, team2,
                COUNT(*) as total_matches,
                SUM(CASE WHEN result LIKE CONCAT(team1, '%') THEN 1 ELSE 0 END) as team1_wins,
                SUM(CASE WHEN result LIKE CONCAT(team2, '%') THEN 1 ELSE 0 END) as team2_wins,
                ROUND(SUM(CASE WHEN result LIKE CONCAT(team1, '%') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as team1_win_percent,
                ROUND(SUM(CASE WHEN result LIKE CONCAT(team2, '%') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as team2_win_percent
            FROM matches
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR)
              AND result IS NOT NULL
            GROUP BY team1, team2
            HAVING total_matches >= 5
            ORDER BY total_matches DESC;
        """,
        
        "Question 23": """
            WITH recent_matches AS (
                SELECT ps.player_id, ps.runs, ps.strike_rate, m.date,
                       ROW_NUMBER() OVER (PARTITION BY ps.player_id ORDER BY m.date DESC) as rn
                FROM player_stats ps
                JOIN matches m ON ps.match_id = m.match_id
            ),
            form_analysis AS (
                SELECT player_id,
                       AVG(CASE WHEN rn <= 5 THEN runs END) as avg_last_5,
                       AVG(CASE WHEN rn <= 10 THEN runs END) as avg_last_10,
                       AVG(CASE WHEN rn <= 10 THEN strike_rate END) as recent_strike_rate,
                       SUM(CASE WHEN rn <= 10 AND runs >= 50 THEN 1 ELSE 0 END) as scores_above_50,
                       STDDEV(CASE WHEN rn <= 10 THEN runs END) as consistency_std_dev
                FROM recent_matches
                WHERE rn <= 10
                GROUP BY player_id
                HAVING COUNT(*) >= 5
            )
            SELECT p.name,
                   fa.avg_last_5,
                   fa.avg_last_10,
                   fa.recent_strike_rate,
                   fa.scores_above_50,
                   fa.consistency_std_dev,
                   CASE 
                       WHEN fa.avg_last_5 > 50 AND fa.consistency_std_dev < 20 THEN 'Excellent Form'
                       WHEN fa.avg_last_5 > 35 AND fa.consistency_std_dev < 25 THEN 'Good Form'
                       WHEN fa.avg_last_5 > 20 THEN 'Average Form'
                       ELSE 'Poor Form'
                   END as form_category
            FROM form_analysis fa
            JOIN players p ON fa.player_id = p.id
            ORDER BY fa.avg_last_5 DESC;
        """,
        
        "Question 24": """
            SELECT p1.name as player1, p2.name as player2,
                   COUNT(*) as total_partnerships,
                   AVG(bp.runs) as avg_partnership,
                   SUM(CASE WHEN bp.runs > 50 THEN 1 ELSE 0 END) as partnerships_above_50,
                   MAX(bp.runs) as highest_partnership,
                   ROUND(SUM(CASE WHEN bp.runs > 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
            FROM batting_partnerships bp
            JOIN players p1 ON bp.player1_id = p1.id
            JOIN players p2 ON bp.player2_id = p2.id
            GROUP BY p1.id, p1.name, p2.id, p2.name
            HAVING total_partnerships >= 5
            ORDER BY success_rate DESC, avg_partnership DESC;
        """,
        
        "Question 25": """
            WITH quarterly_stats AS (
                SELECT ps.player_id,
                       CONCAT(YEAR(m.date), '-Q', QUARTER(m.date)) as quarter,
                       AVG(ps.runs) as avg_runs,
                       AVG(ps.strike_rate) as avg_strike_rate,
                       COUNT(DISTINCT ps.match_id) as matches_played,
                       LAG(AVG(ps.runs)) OVER (PARTITION BY ps.player_id ORDER BY CONCAT(YEAR(m.date), '-Q', QUARTER(m.date))) as prev_avg_runs,
                       LAG(AVG(ps.strike_rate)) OVER (PARTITION BY ps.player_id ORDER BY CONCAT(YEAR(m.date), '-Q', QUARTER(m.date))) as prev_avg_sr
                FROM player_stats ps
                JOIN matches m ON ps.match_id = m.match_id
                WHERE m.date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
                GROUP BY ps.player_id, CONCAT(YEAR(m.date), '-Q', QUARTER(m.date))
            ),
            career_trajectory AS (
                SELECT player_id,
                       COUNT(DISTINCT quarter) as quarters_played,
                       AVG(avg_runs) as overall_avg_runs,
                       CASE 
                           WHEN AVG(avg_runs) > COALESCE(AVG(prev_avg_runs), 0) + 5 THEN 'Career Ascending'
                           WHEN AVG(avg_runs) < COALESCE(AVG(prev_avg_runs), 0) - 5 THEN 'Career Declining'
                           ELSE 'Career Stable'
                       END as career_phase
                FROM quarterly_stats
                WHERE matches_played >= 3
                GROUP BY player_id
                HAVING quarters_played >= 6
            )
            SELECT p.name, ct.quarters_played, ct.overall_avg_runs, ct.career_phase
            FROM career_trajectory ct
            JOIN players p ON ct.player_id = p.id
            ORDER BY ct.overall_avg_runs DESC;
        """
    }
    
    # Display and execute selected query
    if selected_query:
        st.subheader(f"Executing: {query_options[selected_query]}")
        
        # Show the SQL query
        with st.expander("View SQL Query"):
            st.code(queries[selected_query], language="sql")
        
        # Execute query button
        if st.button("Execute Query"):
            with st.spinner("Executing query..."):
                results = db_manager.execute_query(queries[selected_query])
                
                if results:
                    st.success(f"Query executed successfully! Found {len(results)} records.")
                    
                    # Display results as a table
                    df = pd.DataFrame(results)
                    st.dataframe(df)
                    
                    # Option to download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download results as CSV",
                        data=csv,
                        file_name=f"{selected_query.lower().replace(' ', '_')}_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No results found for this query.")
    
    # Custom query section
    st.header("🔧 Custom SQL Query")
    
    custom_query = st.text_area(
        "Enter your own SQL query:",
        height=150,
        placeholder="SELECT * FROM players LIMIT 10;"
    )
    
    if st.button("Execute Custom Query"):
        if custom_query:
            with st.spinner("Executing custom query..."):
                results = db_manager.execute_query(custom_query)
                
                if results:
                    st.success(f"Query executed successfully! Found {len(results)} records.")
                    
                    # Display results as a table
                    df = pd.DataFrame(results)
                    st.dataframe(df)
                    
                    # Option to download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download results as CSV",
                        data=csv,
                        file_name="custom_query_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No results found for this query.")
        else:
            st.warning("Please enter a SQL query.")

# Run the app
if __name__ == "__main__":
    display_sql_analytics()