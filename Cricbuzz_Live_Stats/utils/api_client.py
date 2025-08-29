# utils/api_client.py
import requests
import os
import time
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

class CricbuzzAPIClient:

    def __init__(self):
        self.base_url = f"https://{os.getenv('RAPIDAPI_HOST')}"
        self.headers = {
            'X-RapidAPI-Key': os.getenv('RAPIDAPI_KEY'),
            'X-RapidAPI-Host': os.getenv('RAPIDAPI_HOST')
        }
        self.last_api_call = 0
        self.call_count = 0
        self.max_calls_per_minute = 60

    def get_player_batting_stats(self, player_id):
        """Get player batting statistics"""
        endpoint = f"stats/v1/player/{player_id}/batting"
        return self.make_api_request(endpoint)

    def get_player_bowling_stats(self, player_id):
        """Get player bowling statistics"""
        endpoint = f"stats/v1/player/{player_id}/bowling"
        return self.make_api_request(endpoint)

    def get_player_career_stats(self, player_id):
        """Get player career statistics"""
        endpoint = f"stats/v1/player/{player_id}/career"
        return self.make_api_request(endpoint)

    def check_rate_limit(self):
        """Check if we need to wait before making another API call"""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self.last_api_call >= 60:
            self.call_count = 0
            self.last_api_call = current_time
        
        # Check if we've exceeded the limit
        if self.call_count >= self.max_calls_per_minute:
            wait_time = 60 - (current_time - self.last_api_call)
            if wait_time > 0:
                time.sleep(wait_time)
                self.last_api_call = time.time()
                self.call_count = 0
        
        self.call_count += 1
    
    def make_api_request(self, endpoint, params=None):
        """Generic API request method"""
        self.check_rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=10
            )
            
            # Handle errors
            if response.status_code == 429:
                st.error(f"⚠️ Rate limit exceeded for {endpoint}.")
                return None
            elif response.status_code == 404:
                st.warning(f"ℹ️ {endpoint} not found.")
                return None
            elif response.status_code >= 400:
                st.error(f"❌ Error accessing {endpoint}: {response.status_code}")
                return None
                
            return response.json()
                
        except Exception as e:
            st.error(f"Error accessing {endpoint}: {e}")
            return None
    
    def get_matches(self, match_type="live"):
        """Get matches based on type (live, recent, upcoming)"""
        endpoint = f"matches/v1/{match_type}"
        data = self.make_api_request(endpoint)
        
        # Handle different response formats
        if data is None:
            return []
        
        # Try different possible response structures
        if 'typeMatches' in data:
            return data.get('typeMatches', [])
        elif 'matchType' in data:
            return [data]  # Wrap single match in a list
        elif isinstance(data, list):
            return data
        else:
            st.warning(f"Unexpected matches response format: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return []
    
    def get_match_details(self, match_id):
        """Get detailed information for a specific match"""
        endpoint = f"mcenter/v1/{match_id}"
        return self.make_api_request(endpoint)
    
    def get_player_profile(self, player_id):
        """Get player profile information from API"""
        endpoint = f"stats/v1/player/{player_id}"
        return self.make_api_request(endpoint)
    
    def search_players(self, search_term):
        """Search for players by name"""
        endpoint = "stats/v1/player/search"
        params = {'plrN': search_term}
        data = self.make_api_request(endpoint, params)
        return data.get('player', []) if data else []

# Global instance
api_client = CricbuzzAPIClient()

# Helper functions for backward compatibility
def get_matches(match_type="live"):
    return api_client.get_matches(match_type)

def get_match_scorecard(match_id):
    return api_client.get_match_details(match_id)

def search_players(search_term):
    return api_client.search_players(search_term)

def get_player_profile(player_id):
    return api_client.get_player_profile(player_id)
def get_player_batting_stats(player_id):
    return api_client.get_player_batting_stats(player_id)

def get_player_bowling_stats(player_id):
    return api_client.get_player_bowling_stats(player_id)

def get_player_career_stats(player_id):
    return api_client.get_player_career_stats(player_id)