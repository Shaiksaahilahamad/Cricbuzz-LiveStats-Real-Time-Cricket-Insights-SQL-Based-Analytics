# sql_analytics.py
import os
import sys
import time
import json
import math
from typing import Any, Dict, List, Optional, Tuple,Union

import requests
import pandas as pd
import streamlit as st

from utils.db_connection import get_db_connection



# ================================
# Global API config + counters
# ================================
# Your monthly plan safety: default to 8000 for UI (you can override by env)
API_BUDGET = int(os.getenv("API_BUDGET", "8000"))
API_CALLS = 0
MAX_CALLS = int(os.getenv("MAX_API_CALLS", str(API_BUDGET)))  # soft cap for run
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY or "",
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
    "Accept": "application/json",
}

# ================================
# Helpers
# ================================

def api_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    retries: int = 5,
    backoff: float = 0.8
) -> Optional[Dict[str, Any]]:
    """GET wrapper with global counter, throttle, retries, and JSON safety."""
    global API_CALLS
    if not RAPIDAPI_KEY:
        raise RuntimeError("RAPIDAPI_KEY is not set in environment.")
    if API_CALLS >= MAX_CALLS:
        raise RuntimeError(f"Stopped: API calls reached safety cap {MAX_CALLS}.")

    attempt = 0
    while True:
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
            API_CALLS += 1
            # Log minimal trace in Streamlit
            st.session_state.setdefault("api_trace", []).append(
                f"[API {API_CALLS}] GET {url} params={params or {}}"
            )
            resp.raise_for_status()

            try:
                return resp.json()
            except ValueError:
                # JSON decoding failed — log preview of raw text
                text_preview = resp.text[:200].replace("\n", " ")
                print(f"⚠️ Invalid JSON at {url}, params={params}, preview={text_preview}")
                return None

        except requests.RequestException as e:
            attempt += 1
            if attempt > retries:
                print(f"❌ API failed after {retries} retries: {url}")
                return None
            wait = backoff * attempt
            print(f"⏳ Error {e}, retrying in {wait:.1f}s...")
            time.sleep(wait)

# --- tiny helpers ---
def _to_int(x, default=None):
    try:
        if x is None or x == "": return default
        return int(x)
    except Exception:
        return default

def _to_float(x, default=None):
    try:
        if x is None or x == "": return default
        return float(x)
    except Exception:
        return default

def _short(text, n=50):
    if text is None: return None
    s = str(text)
    return s[:n]


def _to_date(value: Any) -> Optional[str]:
    """Best-effort date normalizer → 'YYYY-MM-DD' or None."""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            x = int(value)
            if x > 10_000_000_000:  # epoch ms
                x //= 1000
            return time.strftime("%Y-%m-%d", time.gmtime(x))
        s = str(value)
        if len(s) >= 10 and s[4] == '-' and s[7] == '-':
            return s[:10]
        if s.isdigit():
            x = int(s)
            if x > 10_000_000_000:
                x //= 1000
            return time.strftime("%Y-%m-%d", time.gmtime(x))
    except Exception:
        pass
    return None


# ================================
# DB Schema Setup (idempotent)
# ================================

def init_schema(conn):
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS teams (
            team_id INT PRIMARY KEY,
            name VARCHAR(120),
            short_name VARCHAR(20),
            country VARCHAR(80)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            player_id INT PRIMARY KEY,
            name VARCHAR(120),
            role VARCHAR(50),
            bat_style VARCHAR(50),
            bowl_style VARCHAR(50),
            team_id INT,
            country VARCHAR(100),
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS series (
            series_id INT PRIMARY KEY,
            name VARCHAR(255),
            host_country VARCHAR(80),
            match_type VARCHAR(20),
            start_date DATE,
            end_date DATE,
            total_matches INT
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS venues (
            venue_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(150),
            city VARCHAR(100),
            country VARCHAR(80),
            capacity INT,
            UNIQUE KEY uniq_venue (name, city, country)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            match_id INT PRIMARY KEY,
            series_id INT,
            team1_id INT,
            team2_id INT,
            match_date DATE,
            venue_id INT,
            winner_id INT,
            win_margin VARCHAR(50),
            victory_type TEXT,
            toss_winner_id INT,
            toss_decision VARCHAR(20),
            match_format VARCHAR(20),
            description VARCHAR(255),
            FOREIGN KEY (series_id) REFERENCES series(series_id),
            FOREIGN KEY (team1_id) REFERENCES teams(team_id),
            FOREIGN KEY (team2_id) REFERENCES teams(team_id),
            FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS batting_stats (
            id INT PRIMARY KEY AUTO_INCREMENT,
            match_id INT,
            player_id INT,
            team_id INT,
            runs INT,
            balls INT,
            fours INT,
            sixes INT,
            strike_rate FLOAT,
            innings_no INT,
            batting_pos INT,
            is_out TINYINT(1),
            FOREIGN KEY (match_id) REFERENCES matches(match_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bowling_stats (
            id INT PRIMARY KEY AUTO_INCREMENT,
            match_id INT,
            player_id INT,
            team_id INT,
            overs FLOAT,
            maidens INT,
            runs INT,
            wickets INT,
            economy FLOAT,
            innings_no INT,
            FOREIGN KEY (match_id) REFERENCES matches(match_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS partnerships (
            id INT PRIMARY KEY AUTO_INCREMENT,
            match_id INT,
            innings_no INT,
            player1_id INT,
            player2_id INT,
            runs INT,
            balls INT,
            pair_pos_diff INT,
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fielding_stats (
            id INT PRIMARY KEY AUTO_INCREMENT,
            match_id INT,
            player_id INT,
            catches INT,
            stumpings INT,
            FOREIGN KEY (match_id) REFERENCES matches(match_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        ) ENGINE=InnoDB;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS etl_state (
            k VARCHAR(64) PRIMARY KEY,
            v VARCHAR(255)
        ) ENGINE=InnoDB;
        """
    )

    conn.commit()


# ================================
# Extract – needed APIs only (+ pagination where possible)
# ================================



def extract_teams():
    return api_get("https://cricbuzz-cricket.p.rapidapi.com/teams/v1/international")

def extract_players(team_id: int):
    return api_get(f"https://cricbuzz-cricket.p.rapidapi.com/teams/v1/{team_id}/players")

def extract_player_profile(player_id: int):
    """Fetch full player profile from API."""
    return api_get(f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}")

def extract_series_page(cursor: Optional[str] = None):
    params = {"cursor": cursor} if cursor else None
    return api_get("https://cricbuzz-cricket.p.rapidapi.com/series/v1/international", params=params)

def extract_archives_page(cursor: Optional[str] = None):
    params = {"cursor": cursor} if cursor else None
    return api_get("https://cricbuzz-cricket.p.rapidapi.com/series/v1/archives/international", params=params)

def extract_series_detail(series_id: int):
    return api_get(f"https://cricbuzz-cricket.p.rapidapi.com/series/v1/{series_id}")

def extract_match_info(match_id: int):
    return api_get(f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}")

def extract_scorecard(match_id: int):
    return api_get(f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard")

def extract_recent_matches(cursor: Optional[str] = None):
    params = {"cursor": cursor} if cursor else None
    return api_get("https://cricbuzz-cricket.p.rapidapi.com/matches/v1/recent", params=params)

def extract_venue(venue_id: int):
    """Fetch detailed venue info by venue ID"""
    return api_get(f"https://cricbuzz-cricket.p.rapidapi.com/venues/v1/{venue_id}")


def resolve_team_id(conn, team_name: str):
    """Look up team_id from teams table by team_name."""
    if not team_name:
        return None
    cur = conn.cursor()
    cur.execute(
        "SELECT team_id FROM teams WHERE name = %s OR short_name = %s LIMIT 1",
        (team_name, team_name)
    )
    row = cur.fetchone()
    return row[0] if row else None


# ================================
# Insert / Upsert helpers
# ================================

def upsert_team(conn, team: Dict[str, Any]):
    cur = conn.cursor()
    team_id = int(team.get("teamId") or team.get("id") or 0)
    if not team_id:
        return

    name = team.get("teamName") or team.get("name")
    sname = team.get("teamSName") or team.get("shortName") or team.get("sName")
    
    # country is not in this JSON, fallback to name (or NULL)
    country = team.get("country") or name  

    cur.execute(
        """
        INSERT INTO teams(team_id, name, short_name, country)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name=VALUES(name),
            short_name=VALUES(short_name),
            country=VALUES(country)
        """,
        (team_id, name, sname, country),
    )

def upsert_player(conn, player: Dict[str, Any], team_id: int, enrich: Dict[str, Any] = None):
    cur = conn.cursor()
    pid = int(player.get("id") or player.get("playerId") or 0)
    if not pid:
        return

    # ✅ If enrichment missing, fetch it
    if enrich is None:
        enrich = extract_player_profile(pid) or {}

    # ✅ Name
    name = (
        player.get("name")
        or enrich.get("name")
        or player.get("fullName")
        or player.get("batName")
        or f"Player {pid}"
    )

    # ✅ Role from profile
    role = (
        player.get("role")
        or player.get("playingRole")
        or enrich.get("role")
    )

    # ✅ Batting / Bowling style
    bat = player.get("bat") or player.get("battingStyle") or enrich.get("bat")
    bowl = player.get("bowl") or player.get("bowlingStyle") or enrich.get("bowl")

    # ✅ Country
    country = (
        player.get("intlTeam")
        or player.get("teamName")
        or enrich.get("intlTeam")
    )

    cur.execute(
        """
        INSERT INTO players (player_id, name, role, bat_style, bowl_style, team_id, country)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          name = VALUES(name),
          role = VALUES(role),
          bat_style = VALUES(bat_style),
          bowl_style = VALUES(bowl_style),
          team_id = VALUES(team_id),
          country = VALUES(country)
        """,
        (pid, name, role, bat, bowl, team_id, country),
    )
    conn.commit()

def get_or_create_venue(conn, name: Optional[str], city: Optional[str], country: Optional[str], capacity: Optional[Union[str, int]]) -> Optional[int]:
    if not name:
        return None

    # ✅ Normalize capacity safely
    def safe_capacity(val):
        if val is None:
            return None
        try:
            val = str(val).replace(",", "").strip()
            if not val or val in ["-", "N/A", "NA", "null"]:
                return None
            return int(val)
        except Exception:
            return None

    capacity = safe_capacity(capacity)

    cur = conn.cursor()
    cur.execute(
        "SELECT venue_id FROM venues WHERE name=%s AND COALESCE(city,'')=COALESCE(%s,'') AND COALESCE(country,'')=COALESCE(%s,'')",
        (name, city, country),
    )
    row = cur.fetchone()
    if row:
        vid = row[0]
        # ✅ update only if new capacity is higher
        cur.execute(
            "UPDATE venues SET capacity = GREATEST(COALESCE(capacity,0), COALESCE(%s,0)) WHERE venue_id=%s",
            (capacity, vid),
        )
        return vid

    cur.execute(
        "INSERT INTO venues(name, city, country, capacity) VALUES (%s,%s,%s,%s)",
        (name, city, country, capacity),
    )
    return cur.lastrowid

def upsert_series(conn, s: Dict[str, Any]):
    cur = conn.cursor()

    sid = int(s.get("seriesId") or s.get("id") or 0)
    if not sid:
        return

    name = s.get("seriesName") or s.get("name")

    # --- Default values ---
    host_country = s.get("hostCountry")
    match_type = s.get("matchType")
    total_matches = s.get("totalMatches")

    # --- Derive host country, match type, and total matches ---
    md = s.get("matchDetails") or []
    if md:
        first_match = None
        for bucket in md:
            if isinstance(bucket, dict) and "matchDetailsMap" in bucket:
                matches = bucket["matchDetailsMap"].get("match", [])
                if matches:
                    first_match = matches[0].get("matchInfo")
                    break
        if first_match:
            vinfo = first_match.get("venueInfo", {})
            if not host_country:
                host_country = vinfo.get("country") or vinfo.get("city")
            if not match_type:
                match_type = first_match.get("matchFormat")
        if not total_matches:
            total_matches = sum(
                len(bucket.get("matchDetailsMap", {}).get("match", []))
                for bucket in md if isinstance(bucket, dict)
            )

    cur.execute(
        """
        INSERT INTO series(series_id, name, host_country, match_type, start_date, end_date, total_matches)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            name=VALUES(name),
            host_country=VALUES(host_country),
            match_type=VALUES(match_type),
            start_date=VALUES(start_date),
            end_date=VALUES(end_date),
            total_matches=VALUES(total_matches)
        """,
        (
            sid,
            name,
            host_country,
            match_type,
            _to_date(s.get("seriesStartDt") or s.get("startDt")),
            _to_date(s.get("seriesEndDt") or s.get("endDt")),
            total_matches,
        ),
    )

def upsert_match_basic(conn, m: Dict[str, Any], series_id: Optional[int] = None):
    cur = conn.cursor()
    mid = _to_int(m.get("matchId") or m.get("id"))
    if not mid:
        return

    # --- Teams (ensure FKs exist) ---
    t1 = (m.get("team1") or {}) or {}
    t2 = (m.get("team2") or {}) or {}
    team1_id = _to_int(t1.get("teamId") or t1.get("id"), 0)
    team2_id = _to_int(t2.get("teamId") or t2.get("id"), 0)
    if team1_id: upsert_team(conn, t1)
    if team2_id: upsert_team(conn, t2)

    # --- Venue ---
    vinfo = m.get("venueInfo") or m.get("venue") or {}
    venue_name = vinfo.get("ground") or vinfo.get("name")
    venue_city = vinfo.get("city")
    venue_country = vinfo.get("country")
    capacity = vinfo.get("capacity")
    venue_id = get_or_create_venue(conn, venue_name, venue_city, venue_country, capacity)

    # --- Dates ---
    mdate = _to_date(m.get("matchDate") or m.get("startDate") or m.get("startTime"))

    # --- Winner / Toss / Result (light, from list object) ---
    winner_id = None
    if isinstance(m.get("matchWinner"), dict):
        winner_id = _to_int(m["matchWinner"].get("teamId"))
    elif _to_int(m.get("winnerTeamId")):
        winner_id = _to_int(m.get("winnerTeamId"))

    toss = m.get("tossResults") or m.get("toss") or {}
    toss_winner_id = _to_int(toss.get("tossWinnerId") or toss.get("winnerId"))
    toss_decision = toss.get("decision") or toss.get("tossDecision")

    result = m.get("result") or {}
    win_margin = result.get("resultMargin") or result.get("margin") or m.get("winMargin")
    victory_type = result.get("resultType") or result.get("victoryType") or m.get("status")
    victory_type = _short(victory_type, 50)  # avoid “Data too long for column 'victory_type'”

    mformat = m.get("matchFormat") or m.get("format")
    desc = m.get("matchDescription") or m.get("matchDesc") or m.get("seriesName") or m.get("status")

    # --- If any of these are missing, query mcenter ---
    need_mcenter = any(x is None for x in [winner_id, toss_winner_id, toss_decision, win_margin, victory_type])
    if need_mcenter:
        try:
            mc = extract_match_info(mid) or {}
            hdr = mc.get("matchHeader") or {}
            # winner
            winner_id = winner_id or _to_int(hdr.get("winningTeamId"))
            # toss
            toss_block = hdr.get("tossResults") or {}
            toss_winner_id = toss_winner_id or _to_int(toss_block.get("tossWinnerId") or toss_block.get("winnerId"))
            toss_decision = toss_decision or toss_block.get("decision") or toss_block.get("tossDecision")
            # result
            res = hdr.get("result") or {}
            win_margin = win_margin or res.get("resultMargin") or res.get("margin")
            victory_type = victory_type or res.get("resultType") or res.get("victoryType") or hdr.get("status")
            victory_type = _short(victory_type, 50)
        except Exception as e:
            print(f"⚠️ mcenter enrichment failed for match {mid}: {e}")

    # try to coerce numeric margin if sent like "by 5 wickets" (we keep text if not numeric)
    try:
        if isinstance(win_margin, str) and win_margin.strip().isdigit():
            win_margin = int(win_margin.strip())
    except Exception:
        pass

    cur.execute(
        """
        INSERT INTO matches(
            match_id, series_id, team1_id, team2_id, match_date, venue_id,
            winner_id, win_margin, victory_type,
            toss_winner_id, toss_decision,
            match_format, description
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            series_id=VALUES(series_id),
            team1_id=VALUES(team1_id),
            team2_id=VALUES(team2_id),
            match_date=VALUES(match_date),
            venue_id=VALUES(venue_id),
            winner_id=VALUES(winner_id),
            win_margin=VALUES(win_margin),
            victory_type=VALUES(victory_type),
            toss_winner_id=VALUES(toss_winner_id),
            toss_decision=VALUES(toss_decision),
            match_format=VALUES(match_format),
            description=VALUES(description)
        """,
        (
            mid, series_id, team1_id, team2_id, mdate, venue_id,
            winner_id, win_margin, victory_type,
            toss_winner_id, toss_decision,
            mformat, desc
        ),
    )

def insert_batting_score(conn, mid: int, innings_no: int, team_id: int, b: Dict[str, Any], order: int = None):
    cur = conn.cursor()
    pid = int(b.get("playerId") or b.get("id") or 0)
    if not pid:
        return

    def safe_int(val, default=0):
        try:
            return int(val)
        except Exception:
            return default

    def safe_float(val, default=None):
        try:
            return float(val)
        except Exception:
            return default

    runs = safe_int(b.get("runs"))
    balls = safe_int(b.get("balls") or b.get("ballsFaced"))
    fours = safe_int(b.get("fours"))
    sixes = safe_int(b.get("sixes"))

    # ✅ Strike rate (API or calculate manually)
    sr = safe_float(b.get("strkrate") or b.get("strikeRate") or b.get("sr"))
    if sr is None and balls > 0:
        sr = round((runs / balls) * 100, 2)

    # ✅ Resolve team_id if missing
    if not team_id:
        team_id = safe_int(b.get("teamId"))
    if not team_id:
        team_name = b.get("teamName") or b.get("team")  # some APIs use teamName
        team_id = resolve_team_id(conn, team_name)

    # Batting position
    pos = order if order is not None else safe_int(b.get("battingOrder") or b.get("order"), None)

    # Out / not out detection
    if "isOut" in b:
        is_out = 1 if b.get("isOut") else 0
    else:
        out_desc = (b.get("outDesc") or "").lower()
        is_out = 0 if "not out" in out_desc else 1 if out_desc else None

    cur.execute(
        """
        INSERT INTO batting_stats(
            match_id, player_id, team_id, runs, balls, fours, sixes,
            strike_rate, innings_no, batting_pos, is_out
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            runs=VALUES(runs),
            balls=VALUES(balls),
            fours=VALUES(fours),
            sixes=VALUES(sixes),
            strike_rate=VALUES(strike_rate),
            batting_pos=VALUES(batting_pos),
            is_out=VALUES(is_out)
        """,
        (mid, pid, team_id, runs, balls, fours, sixes, sr, innings_no, pos, is_out),
    )

    
def insert_bowling_figures(conn, mid: int, innings_no: int, team_id: int, bw: Dict[str, Any]):
    cur = conn.cursor()
    pid = int(bw.get("playerId") or bw.get("id") or 0)
    if not pid:
        return

    def safe_int(val, default=0):
        try:
            return int(val)
        except Exception:
            return default

    def safe_float(val, default=None):
        try:
            return float(val)
        except Exception:
            return default

    overs = safe_float(bw.get("overs") or bw.get("o"), 0.0)
    maidens = safe_int(bw.get("maidens") or bw.get("m"))
    runs = safe_int(bw.get("runs") or bw.get("r"))
    wkts = safe_int(bw.get("wickets") or bw.get("w"))
    econ = safe_float(bw.get("economy") or bw.get("eco"))

    cur.execute(
        """
        INSERT INTO bowling_stats(match_id, player_id, team_id, overs, maidens, runs, wickets, economy, innings_no)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            overs=VALUES(overs),
            maidens=VALUES(maidens),
            runs=VALUES(runs),
            wickets=VALUES(wickets),
            economy=VALUES(economy)
        """,
        (mid, pid, team_id, overs, maidens, runs, wkts, econ, innings_no),
    )

def insert_partnership(conn, mid: int, innings_no: int, p1: int, p2: int, runs: int, balls: Optional[int], pos_diff: Optional[int]):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO partnerships(match_id, innings_no, player1_id, player2_id, runs, balls, pair_pos_diff)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            runs=VALUES(runs),
            balls=VALUES(balls),
            pair_pos_diff=VALUES(pair_pos_diff)
        """,
        (mid, innings_no, p1, p2, runs, balls, pos_diff),
    )

def insert_fielding(conn, mid: int, pid: int, catches: Optional[int], stumpings: Optional[int]):
    if not pid:
        return
    def safe_int(val, default=0):
        try:
            return int(val)
        except Exception:
            return default

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO fielding_stats(match_id, player_id, catches, stumpings)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            catches=VALUES(catches),
            stumpings=VALUES(stumpings)
        """,
        (mid, pid, safe_int(catches), safe_int(stumpings)),
    )

def derive_partnerships_from_batsmen(batsmen):
    partnerships = []
    current_pair = []
    runs_accum, balls_accum = 0, 0

    for b in batsmen:
        pid = b.get("id")
        runs = int(b.get("runs") or 0)
        balls = int(b.get("balls") or 0)

        current_pair.append(pid)
        runs_accum += runs
        balls_accum += balls

        # When pair is complete
        if len(current_pair) == 2:
            partnerships.append({
                "player1Id": current_pair[0],
                "player2Id": current_pair[1],
                "runs": runs_accum,
                "balls": balls_accum
            })
            # Reset for next stand: keep last batter for next partnership
            current_pair = [current_pair[1]]
            runs_accum, balls_accum = 0, 0

    return partnerships

# ================================
# Parse scorecard JSON
# ================================

def derive_partnerships_from_batsmen(batsmen):
    """Fallback: build partnerships from batsmen list if JSON has no partnerships block."""
    partnerships = []
    current_pair = []
    runs_accum, balls_accum = 0, 0

    for b in batsmen:
        pid = b.get("id")
        runs = int(b.get("runs") or 0)
        balls = int(b.get("balls") or 0)

        current_pair.append(pid)
        runs_accum += runs
        balls_accum += balls

        # When pair is complete
        if len(current_pair) == 2:
            partnerships.append({
                "player1Id": current_pair[0],
                "player2Id": current_pair[1],
                "runs": runs_accum,
                "balls": balls_accum
            })
            # Reset for next partnership
            current_pair = [current_pair[1]]
            runs_accum, balls_accum = 0, 0

    return partnerships


def parse_scorecard(conn, mid: int, sc_json: Dict[str, Any]):
    """Parse a match scorecard JSON and populate batting, bowling, partnerships, and fielding tables."""
    cards = sc_json.get("scoreCard") or sc_json.get("scorecard") or []
    if not cards:
        print(f"⚠️ No scorecards found for match {mid}")
        return

    for inn_idx, card in enumerate(cards, start=1):

        # ===============================
        # --- Case 1: New/Simple Format ---
        # ===============================
        if "batsman" in card:
            bat_team_id = card.get("batteamid") or None
            for order, b in enumerate(card.get("batsman", []), start=1):
                try:
                    insert_batting_score(conn, mid, inn_idx, bat_team_id, b, order)
                except Exception as e:
                    print(f"⚠️ Skipped batting insert (simple) for match {mid}, inns {inn_idx}: {e}")

        if "bowler" in card:
            bowl_team_id = card.get("bowlteamid") or None
            for bw in card.get("bowler", []):
                try:
                    insert_bowling_figures(conn, mid, inn_idx, bowl_team_id, bw)
                except Exception as e:
                    print(f"⚠️ Skipped bowling insert (simple) for match {mid}, inns {inn_idx}: {e}")

        if "fielder" in card:
            for fd in card.get("fielder", []):
                try:
                    pid = int(fd.get("id") or 0)
                except Exception:
                    pid = 0
                if not pid:
                    continue
                catches = int(fd.get("catches") or 0)
                stump = int(fd.get("stumpings") or fd.get("st") or 0)
                try:
                    insert_fielding(conn, mid, pid, catches, stump)
                except Exception as e:
                    print(f"⚠️ Skipped fielding insert (simple) for match {mid}, inns {inn_idx}, player {pid}: {e}")

        # ===============================
        # --- Case 2: Old/Structured Format ---
        # ===============================
        bat_team = card.get("batTeamDetails") or {}
        bat_team_id = bat_team.get("teamId")
        batsmen = bat_team.get("batsmenData") or {}

        for key, b in batsmen.items():
            try:
                order = int(key.split("_")[1]) if "_" in key else None
            except Exception:
                order = None

            try:
                insert_batting_score(conn, mid, inn_idx, bat_team_id, b, order)
            except Exception as e:
                print(f"⚠️ Skipped batting insert for match {mid}, inns {inn_idx}, player {b.get('batName')}: {e}")

        bowl_team = card.get("bowlTeamDetails") or {}
        bowl_team_id = bowl_team.get("teamId")
        bowlers = bowl_team.get("bowlersData") or {}

        for _, bw in bowlers.items():
            try:
                insert_bowling_figures(conn, mid, inn_idx, bowl_team_id, bw)
            except Exception as e:
                print(f"⚠️ Skipped bowling insert for match {mid}, inns {inn_idx}: {e}")

        # --- Partnerships ---
        parts = card.get("partnerships") or bat_team.get("partnerships") or []
        if not parts and "batsman" in card:  # derive from batsman list if missing
            batsmen_list = card.get("batsman", [])
            parts = derive_partnerships_from_batsmen(batsmen_list)

        for p in parts:
            p1 = p.get("player1Id") or p.get("p1Id") or p.get("strikerId")
            p2 = p.get("player2Id") or p.get("p2Id") or p.get("nonStrikerId")
            runs = p.get("runs") or p.get("r") or 0
            balls = p.get("balls") or p.get("b") or 0

            if p1 and p2:
                try:
                    insert_partnership(
                        conn, mid, inn_idx,
                        int(p1), int(p2),
                        int(runs), int(balls),
                        None  # no pos_diff in new JSON
                    )
                except Exception as e:
                    print(f"⚠️ Skipped partnership insert for match {mid}, inns {inn_idx}: {e}")

        # --- Fielding (old format) ---
        field = card.get("fieldingData") or {}
        if isinstance(field, dict):
            field_items = field.items()
        elif isinstance(field, list):
            field_items = [(str(fd.get("playerId")), fd) for fd in field if isinstance(fd, dict)]
        else:
            field_items = []

        for pid_str, fd in field_items:
            try:
                pid = int(fd.get("playerId") or pid_str or 0)
            except Exception:
                continue
            if not pid:
                continue

            catches = int(fd.get("catches") or 0)
            stump = int(fd.get("stumpings") or fd.get("st") or 0)

            try:
                insert_fielding(conn, mid, pid, catches, stump)
            except Exception as e:
                print(f"⚠️ Skipped fielding insert for match {mid}, inns {inn_idx}, player {pid}: {e}")

    # ✅ Commit all inserts at once after processing the match
    try:
        conn.commit()
    except Exception as e:
        print(f"⚠️ Commit failed for match {mid}: {e}")


# ================================
# High-level ELT (safe version)
# ================================

def load_teams_and_players(conn):
    data = extract_teams()
    if not data:
        print("⚠️ Skipping teams fetch, API returned None")
        return

    teams = []
    if isinstance(data, dict):
        if "list" in data:
            teams = [x.get("team") or x for x in data.get("list", [])]
        elif "teams" in data:
            teams = data.get("teams", [])
    for t in teams:
        upsert_team(conn, t)
    conn.commit()

    cur = conn.cursor()
    cur.execute("SELECT team_id FROM teams")
    for (team_id,) in cur.fetchall():
        pdata = extract_players(team_id)
        if not pdata:
            print(f"⚠️ Skipping players for team {team_id}, API returned None")
            continue
        plist = []
        if isinstance(pdata, dict):
            plist = pdata.get("player") or pdata.get("players") or []
        for p in plist:
            upsert_player(conn, p, team_id)
        conn.commit()

def load_series_matches_deep(conn, series_id: int):
    sdet = extract_series_detail(series_id)
    if not sdet or not isinstance(sdet, dict):
        print(f"⚠️ Skipping series {series_id}, no data or wrong type")
        return

    # store basic series info
    upsert_series(conn, sdet)
    conn.commit()

    matches: List[Dict[str, Any]] = []

    # -----------------------------
    # Collect matches safely
    # -----------------------------
    if "matches" in sdet and isinstance(sdet["matches"], list):
        matches = [m for m in sdet["matches"] if isinstance(m, dict)]

    if not matches:
        md = sdet.get("matchDetails") or sdet.get("typeMatches") or []
        if isinstance(md, list):
            for bucket in md:
                if not isinstance(bucket, dict):
                    continue

                # Case 1: seriesMatches block
                if "seriesMatches" in bucket:
                    for sm in bucket.get("seriesMatches", []):
                        if not isinstance(sm, dict):
                            continue
                        for mwrap in sm.get("matches", []):
                            if isinstance(mwrap, dict):
                                mobj = mwrap.get("matchInfo") or mwrap
                                if isinstance(mobj, dict):
                                    matches.append(mobj)

                # Case 2: matchDetailsMap block
                if "matchDetailsMap" in bucket:
                    md_map = bucket.get("matchDetailsMap")

                    # Sometimes dict, sometimes list
                    if isinstance(md_map, dict):
                        for m in md_map.get("match", []):
                            if isinstance(m, dict):
                                matches.append(m.get("matchInfo") or m)

                    elif isinstance(md_map, list):
                        for item in md_map:
                            if not isinstance(item, dict):
                                continue
                            for m in item.get("match", []):
                                if isinstance(m, dict):
                                    matches.append(m.get("matchInfo") or m)

    # -----------------------------
    # Process matches safely
    # -----------------------------
    for m in matches:
        if not isinstance(m, dict):
            continue
        mobj = m.get("matchInfo") or m.get("match") or m
        if not isinstance(mobj, dict):
            continue

        upsert_match_basic(conn, mobj, series_id)
        mid = int(mobj.get("matchId") or mobj.get("id") or 0)
        if not mid:
            continue

        try:
            sc = extract_scorecard(mid)
            if sc and isinstance(sc, dict):
                parse_scorecard(conn, mid, sc)
                conn.commit()
            else:
                print(f"⚠️ No valid scorecard for match {mid}")
        except Exception as e:
            print(f"❌ Scorecard parse failed for match {mid}: {e}")
            conn.rollback()

def load_all_series_and_matches(conn, *, from_year: Optional[int] = None, max_pages: int = 50):
    # current series pages
    cursor = None
    pages = 0
    while pages < max_pages:
        pack = extract_series_page(cursor)
        if not pack:
            print("⚠️ Empty response for current series page, stopping.")
            break
        pages += 1
        series_ids = []
        if isinstance(pack, dict):
            if "seriesMapProto" in pack:
                for bucket in pack.get("seriesMapProto", []):
                    for item in bucket.get("series", []):
                        sid = int(item.get("id") or item.get("seriesId") or 0)
                        if sid:
                            start_dt = _to_date(item.get("startDt") or item.get("startDate"))
                            if from_year and start_dt and int(start_dt[:4]) < from_year:
                                continue
                            upsert_series(conn, item)
                            series_ids.append(sid)
            elif "series" in pack:
                for item in pack.get("series", []):
                    sid = int(item.get("id") or item.get("seriesId") or 0)
                    if sid:
                        start_dt = _to_date(item.get("startDt") or item.get("startDate"))
                        if from_year and start_dt and int(start_dt[:4]) < from_year:
                            continue
                        upsert_series(conn, item)
                        series_ids.append(sid)
        conn.commit()
        for sid in series_ids:
            load_series_matches_deep(conn, sid)
        cursor = pack.get("next") or pack.get("cursor") or None
        if not cursor:
            break

    # archives pages
    cursor = None
    pages = 0
    while pages < max_pages:
        pack = extract_archives_page(cursor)
        if not pack:
            print("⚠️ Empty response for archive page, stopping.")
            break
        pages += 1
        series_ids = []
        if isinstance(pack, dict):
            if "seriesMapProto" in pack:
                for bucket in pack.get("seriesMapProto", []):
                    for item in bucket.get("series", []):
                        sid = int(item.get("id") or item.get("seriesId") or 0)
                        if sid:
                            start_dt = _to_date(item.get("startDt") or item.get("startDate"))
                            if from_year and start_dt and int(start_dt[:4]) < from_year:
                                continue
                            upsert_series(conn, item)
                            series_ids.append(sid)
            elif "series" in pack:
                for item in pack.get("series", []):
                    sid = int(item.get("id") or item.get("seriesId") or 0)
                    if sid:
                        start_dt = _to_date(item.get("startDt") or item.get("startDate"))
                        if from_year and start_dt and int(start_dt[:4]) < from_year:
                            continue
                        upsert_series(conn, item)
                        series_ids.append(sid)
        conn.commit()
        for sid in series_ids:
            load_series_matches_deep(conn, sid)
        cursor = pack.get("next") or pack.get("cursor") or None
        if not cursor:
            break

def incremental_refresh(conn, max_pages: int = 5):
    """Use recent matches to find new/updated matchIds and deep-load them."""
    cursor = None
    pages = 0
    while pages < max_pages:
        data = extract_recent_matches(cursor)
        if not data:
            print("⚠️ Empty response for recent matches, stopping.")
            break
        pages += 1
        type_matches = data.get("typeMatches") or []
        for t in type_matches:
            for sm in t.get("seriesMatches", []):
                sid = int(sm.get("seriesId") or 0)
                sname = sm.get("seriesName")
                if sid:
                    upsert_series(conn, {"seriesId": sid, "seriesName": sname})
                for mwrap in sm.get("matches", []):
                    m = mwrap.get("matchInfo") or mwrap
                    upsert_match_basic(conn, m, sid if sid else None)
                    mid = int(m.get("matchId") or 0)
                    if not mid:
                        continue
                    sc = extract_scorecard(mid)
                    if sc:
                        try:
                            parse_scorecard(conn, mid, sc)
                            conn.commit()
                        except Exception as e:
                            print(f"❌ Scorecard parse failed for match {mid}: {e}")
                            conn.rollback()
                    else:
                        print(f"⚠️ No scorecard for match {mid}")
        cursor = data.get("next") or data.get("cursor") or None
        if not cursor:
            break

# ================================
# Analytics Views (Q1 – Q25)
# ================================

def create_views(conn):
    cur = conn.cursor()

    # Q1
    cur.execute(
        """
        CREATE OR REPLACE VIEW q1_players_india AS
        SELECT p.name AS full_name, p.role AS playing_role, p.bat_style AS batting_style, p.bowl_style AS bowling_style
        FROM players p JOIN teams t ON p.team_id=t.team_id
        WHERE t.country='India';
        """
    )

    # Q2
    cur.execute(
        """
        CREATE OR REPLACE VIEW q2_matches_last_30_days AS
        SELECT m.match_id, m.description AS match_description,
               t1.name AS team1, t2.name AS team2,
               v.name AS venue_name, v.city AS venue_city,
               m.match_date
        FROM matches m
        JOIN teams t1 ON m.team1_id=t1.team_id
        JOIN teams t2 ON m.team2_id=t2.team_id
        JOIN venues v ON m.venue_id=v.venue_id
        WHERE m.match_date >= CURDATE() - INTERVAL 30 DAY
        ORDER BY m.match_date DESC, m.match_id DESC;
        """
    )

    # Q3
    cur.execute(
        """
        CREATE OR REPLACE VIEW q3_top10_odi_run_scorers AS
        SELECT p.player_id, p.name,
               SUM(b.runs) AS total_runs,
               CASE WHEN SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END)=0 THEN NULL
                    ELSE ROUND(SUM(b.runs)/SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END),2) END AS batting_average,
               SUM(CASE WHEN b.runs>=100 THEN 1 ELSE 0 END) AS centuries
        FROM batting_stats b
        JOIN players p ON p.player_id=b.player_id
        JOIN matches m ON m.match_id=b.match_id
        WHERE m.match_format='ODI'
        GROUP BY p.player_id, p.name
        ORDER BY total_runs DESC
        LIMIT 10;
        """
    )

    # Q4
    cur.execute(
        """
        CREATE OR REPLACE VIEW q4_big_venues AS
        SELECT name AS venue_name, city, country, capacity
        FROM venues
        WHERE capacity IS NOT NULL AND capacity > 50000
        ORDER BY capacity DESC, venue_name;
        """
    )

    # Q5
    cur.execute(
        """
        CREATE OR REPLACE VIEW q5_team_wins AS
        SELECT t.name AS team_name, COUNT(*) AS total_wins
        FROM matches m JOIN teams t ON m.winner_id=t.team_id
        GROUP BY t.team_id, t.name
        ORDER BY total_wins DESC, team_name;
        """
    )

    # Q6
    cur.execute(
        """
        CREATE OR REPLACE VIEW q6_players_by_role AS
        SELECT COALESCE(role,'Unknown') AS role, COUNT(*) AS player_count
        FROM players
        GROUP BY COALESCE(role,'Unknown')
        ORDER BY player_count DESC, role;
        """
    )

    # Q7
    cur.execute(
        """
        CREATE OR REPLACE VIEW q7_highest_individual_by_format AS
        SELECT m.match_format AS format, MAX(b.runs) AS highest_score
        FROM batting_stats b JOIN matches m ON m.match_id=b.match_id
        GROUP BY m.match_format;
        """
    )

    # Q8
    cur.execute(
        """
        CREATE OR REPLACE VIEW q8_series_started_2024 AS
        SELECT name AS series_name, host_country, match_type, start_date, total_matches
        FROM series
        WHERE start_date >= '2024-01-01' AND start_date < '2025-01-01'
        ORDER BY start_date, series_name;
        """
    )

    # Q9
    cur.execute(
        """
        CREATE OR REPLACE VIEW q9_all_rounders_1000_50 AS
        WITH bat_totals AS (
            SELECT player_id, SUM(runs) AS total_runs
            FROM batting_stats
            GROUP BY player_id
        ),
        bowl_totals AS (
            SELECT player_id, SUM(wickets) AS total_wickets
            FROM bowling_stats
            GROUP BY player_id
        )
        SELECT p.player_id, p.name,
            COALESCE(b.total_runs,0) AS total_runs,
            COALESCE(w.total_wickets,0) AS total_wickets
        FROM players p
        LEFT JOIN bat_totals b ON p.player_id=b.player_id
        LEFT JOIN bowl_totals w ON p.player_id=w.player_id
        WHERE COALESCE(b.total_runs,0) > 1000
        AND COALESCE(w.total_wickets,0) > 50
        ORDER BY total_runs DESC, total_wickets DESC;
        """
    )

    # Q10
    cur.execute(
        """
        CREATE OR REPLACE VIEW q10_last20_completed AS
        SELECT m.match_id, m.description AS match_description,
               t1.name AS team1, t2.name AS team2,
               tw.name AS winner_team,
               m.win_margin, m.victory_type,
               v.name AS venue_name
        FROM matches m
        JOIN teams t1 ON m.team1_id=t1.team_id
        JOIN teams t2 ON m.team2_id=t2.team_id
        LEFT JOIN teams tw ON m.winner_id=tw.team_id
        JOIN venues v ON m.venue_id=v.venue_id
        WHERE m.victory_type IS NOT NULL
        ORDER BY m.match_date DESC, m.match_id DESC
        LIMIT 20;
        """
    )

    # Q11
    cur.execute(
        """
        CREATE OR REPLACE VIEW q11_player_format_compare AS
        SELECT x.player_id, x.name,
               SUM(CASE WHEN x.format='Test' THEN x.runs ELSE 0 END) AS runs_test,
               SUM(CASE WHEN x.format='ODI' THEN x.runs ELSE 0 END) AS runs_odi,
               SUM(CASE WHEN x.format='T20I' THEN x.runs ELSE 0 END) AS runs_t20i,
               CASE WHEN SUM(x.dismissals)=0 THEN NULL ELSE ROUND(SUM(x.runs)/SUM(x.dismissals),2) END AS overall_bat_avg
        FROM (
            SELECT p.player_id, p.name, m.match_format AS format,
                   SUM(b.runs) AS runs,
                   SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END) AS dismissals
            FROM batting_stats b
            JOIN matches m ON m.match_id=b.match_id
            JOIN players p ON p.player_id=b.player_id
            GROUP BY p.player_id, p.name, m.match_format
        ) x
        GROUP BY x.player_id, x.name
        HAVING COUNT(CASE WHEN x.runs>0 THEN x.format END) >= 2;
        """
    )

    # Q12
    cur.execute(
        """
        CREATE OR REPLACE VIEW q12_home_away_wins AS
        SELECT t.team_id, t.name,
               SUM(CASE WHEN v.country=t.country AND m.winner_id=t.team_id THEN 1 ELSE 0 END) AS home_wins,
               SUM(CASE WHEN (v.country IS NULL OR v.country<>t.country) AND m.winner_id=t.team_id THEN 1 ELSE 0 END) AS away_wins
        FROM teams t
        JOIN matches m ON (m.team1_id=t.team_id OR m.team2_id=t.team_id)
        JOIN venues v ON m.venue_id=v.venue_id
        GROUP BY t.team_id, t.name;
        """
    )

    # Q13
    cur.execute(
        """
        CREATE OR REPLACE VIEW q13_big_partnerships AS
        SELECT p1.name AS player1, p2.name AS player2, pr.runs AS partnership_runs, pr.innings_no, pr.match_id
        FROM partnerships pr
        JOIN players p1 ON p1.player_id=pr.player1_id
        JOIN players p2 ON p2.player_id=pr.player2_id
        WHERE pr.runs >= 100 AND (pr.pair_pos_diff IS NULL OR pr.pair_pos_diff=1);
        """
    )

    # Q14
    cur.execute(
        """
        CREATE OR REPLACE VIEW q14_bowling_venue AS
        SELECT v.name AS venue_name, v.city, bw.player_id, p.name AS player_name,
            COUNT(DISTINCT bw.match_id) AS matches_played,
            SUM(bw.wickets) AS total_wickets,
            ROUND(SUM(bw.runs)/NULLIF(SUM(bw.overs),0),2) AS avg_economy
        FROM bowling_stats bw
        JOIN matches m ON m.match_id=bw.match_id
        JOIN venues v ON v.venue_id=m.venue_id
        JOIN players p ON p.player_id=bw.player_id
        WHERE bw.overs >= 4
        GROUP BY v.name, v.city, bw.player_id, p.name
        HAVING matches_played >= 3;

        """
    )

    # Q15
    cur.execute(
        """
        CREATE OR REPLACE VIEW q15_close_matches AS
        SELECT b.player_id, p.name,
               AVG(b.runs) AS avg_runs_in_close,
               COUNT(DISTINCT b.match_id) AS close_matches_played,
               SUM(CASE WHEN m.winner_id=b.team_id THEN 1 ELSE 0 END) AS wins_when_batted
        FROM batting_stats b
        JOIN matches m ON m.match_id=b.match_id
        JOIN players p ON p.player_id=b.player_id
        WHERE (
            (m.victory_type='runs' AND CAST(REGEXP_SUBSTR(m.win_margin, '^[0-9]+') AS UNSIGNED) < 50) OR
            (m.victory_type='wickets' AND CAST(REGEXP_SUBSTR(m.win_margin, '^[0-9]+') AS UNSIGNED) < 5)
        )
        GROUP BY b.player_id, p.name;
        """
    )

    # Q16
    cur.execute(
        """
        CREATE OR REPLACE VIEW q16_yearly_perf_since_2020 AS
        SELECT p.player_id, p.name, YEAR(m.match_date) AS yr,
               ROUND(AVG(b.runs),2) AS avg_runs_per_match,
               ROUND(AVG(NULLIF(b.strike_rate,0)),2) AS avg_strike_rate,
               COUNT(DISTINCT m.match_id) AS matches_in_year
        FROM batting_stats b
        JOIN matches m ON m.match_id=b.match_id
        JOIN players p ON p.player_id=b.player_id
        WHERE m.match_date >= '2020-01-01'
        GROUP BY p.player_id, p.name, YEAR(m.match_date)
        HAVING matches_in_year >= 5;
        """
    )

    # Q17
    cur.execute(
        """
        CREATE OR REPLACE VIEW q17_toss_advantage AS
        SELECT m.toss_decision,
               ROUND(100.0 * SUM(CASE WHEN m.winner_id=m.toss_winner_id THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_won_after_winning_toss,
               COUNT(*) AS total_matches
        FROM matches m
        WHERE m.toss_winner_id IS NOT NULL AND m.victory_type IS NOT NULL
        GROUP BY m.toss_decision;
        """
    )

    # Q18
    cur.execute(
        """
        CREATE OR REPLACE VIEW q18_economical_limited_overs AS
        SELECT bw.player_id, p.name,
               SUM(bw.runs) AS runs_conceded,
               SUM(bw.overs) AS overs_bowled,
               SUM(bw.wickets) AS wickets,
               ROUND(SUM(bw.runs)/NULLIF(SUM(bw.overs),0),2) AS economy
        FROM bowling_stats bw
        JOIN matches m ON m.match_id=bw.match_id
        JOIN players p ON p.player_id=bw.player_id
        WHERE m.match_format IN ('ODI','T20I')
        GROUP BY bw.player_id, p.name
        HAVING COUNT(DISTINCT bw.match_id) >= 10 AND (SUM(bw.overs)/COUNT(DISTINCT bw.match_id)) >= 2
        ORDER BY economy ASC, wickets DESC;
        """
    )

    # Q19
    cur.execute(
        """
        CREATE OR REPLACE VIEW q19_consistent_batsmen AS
        SELECT b.player_id, p.name,
               ROUND(AVG(b.runs),2) AS avg_runs,
               ROUND(STDDEV_SAMP(b.runs),2) AS stddev_runs,
               COUNT(*) AS innings_count
        FROM batting_stats b
        JOIN matches m ON m.match_id=b.match_id
        JOIN players p ON p.player_id=b.player_id
        WHERE m.match_date >= '2022-01-01' AND b.balls >= 10
        GROUP BY b.player_id, p.name
        HAVING innings_count >= 1
        ORDER BY stddev_runs ASC, avg_runs DESC;
        """
    )

    # Q20
    cur.execute(
        """
        CREATE OR REPLACE VIEW q20_formats_played_avg AS
        SELECT x.player_id, x.name,
               SUM(CASE WHEN x.format='Test' THEN x.matches ELSE 0 END) AS tests,
               SUM(CASE WHEN x.format='ODI' THEN x.matches ELSE 0 END) AS odis,
               SUM(CASE WHEN x.format='T20I' THEN x.matches ELSE 0 END) AS t20is,
               ROUND(AVG(CASE WHEN x.avg IS NOT NULL THEN x.avg END),2) AS overall_avg_of_avgs
        FROM (
            SELECT p.player_id, p.name, m.match_format AS format,
                   COUNT(DISTINCT m.match_id) AS matches,
                   CASE WHEN SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END)=0 THEN NULL
                        ELSE ROUND(SUM(b.runs)/SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END),2) END AS avg
            FROM batting_stats b
            JOIN matches m ON m.match_id=b.match_id
            JOIN players p ON p.player_id=b.player_id
            GROUP BY p.player_id, p.name, m.match_format
        ) x
        GROUP BY x.player_id, x.name
        HAVING (tests + odis + t20is) >= 20;
        """
    )

    # Q21
    cur.execute(
        """
        CREATE OR REPLACE VIEW q21_composite_rank AS
        WITH bat AS (
            SELECT p.player_id, p.name, m.match_format,
                SUM(b.runs) AS runs,
                CASE WHEN SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END)=0 THEN 0
                        ELSE ROUND(SUM(b.runs)/SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END),2) END AS bat_avg,
                ROUND(AVG(NULLIF(b.strike_rate,0)),2) AS strike_rate
            FROM players p
            LEFT JOIN batting_stats b ON b.player_id=p.player_id
            LEFT JOIN matches m ON m.match_id=b.match_id
            GROUP BY p.player_id, p.name, m.match_format
        ),
        bowl AS (
            SELECT p.player_id, m.match_format,
                SUM(w.wickets) AS wkts,
                CASE WHEN SUM(w.wickets)=0 THEN NULL
                        ELSE ROUND(SUM(w.runs)/NULLIF(SUM(w.wickets),0),2) END AS bowl_avg,
                ROUND(SUM(w.runs)/NULLIF(SUM(w.overs),0),2) AS economy
            FROM players p
            LEFT JOIN bowling_stats w ON w.player_id=p.player_id
            LEFT JOIN matches m ON m.match_id=w.match_id
            GROUP BY p.player_id, m.match_format
        ),
        field AS (
            SELECT p.player_id, m.match_format,
                COALESCE(SUM(f.catches),0) AS catches,
                COALESCE(SUM(f.stumpings),0) AS stumpings
            FROM players p
            LEFT JOIN fielding_stats f ON f.player_id=p.player_id
            LEFT JOIN matches m ON m.match_id=f.match_id
            GROUP BY p.player_id, m.match_format
        )
        SELECT b.player_id, b.name, b.match_format AS format,
            (COALESCE(b.runs,0)*0.01) + (COALESCE(b.bat_avg,0)*0.5) + (COALESCE(b.strike_rate,0)*0.3) AS batting_points,
            (COALESCE(w.wkts,0)*2) + ((50-COALESCE(w.bowl_avg,50))*0.5) + ((6-COALESCE(w.economy,6))*2) AS bowling_points,
            (COALESCE(f.catches,0) + COALESCE(f.stumpings,0)) AS fielding_points,
            ROUND(
                (COALESCE(b.runs,0)*0.01) + (COALESCE(b.bat_avg,0)*0.5) + (COALESCE(b.strike_rate,0)*0.3)
                + (COALESCE(w.wkts,0)*2) + ((50-COALESCE(w.bowl_avg,50))*0.5) + ((6-COALESCE(w.economy,6))*2)
                + (COALESCE(f.catches,0) + COALESCE(f.stumpings,0))
            , 2) AS total_score
        FROM bat b
        LEFT JOIN bowl w ON w.player_id=b.player_id AND w.match_format=b.match_format
        LEFT JOIN field f ON f.player_id=b.player_id AND f.match_format=b.match_format;

        """
    )

    # Q22
    cur.execute(
        """
        CREATE OR REPLACE VIEW q22_head_to_head AS
        SELECT LEAST(m.team1_id, m.team2_id) AS team_a,
               GREATEST(m.team1_id, m.team2_id) AS team_b,
               COUNT(*) AS total_matches,
               SUM(CASE WHEN m.winner_id=LEAST(m.team1_id, m.team2_id) THEN 1 ELSE 0 END) AS wins_team_a,
               SUM(CASE WHEN m.winner_id=GREATEST(m.team1_id, m.team2_id) THEN 1 ELSE 0 END) AS wins_team_b,
               ROUND(AVG(CASE WHEN m.winner_id=LEAST(m.team1_id, m.team2_id) AND m.victory_type='runs' THEN CAST(REGEXP_SUBSTR(m.win_margin,'^[0-9]+') AS UNSIGNED) END),2) AS avg_margin_runs_a,
               ROUND(AVG(CASE WHEN m.winner_id=GREATEST(m.team1_id, m.team2_id) AND m.victory_type='runs' THEN CAST(REGEXP_SUBSTR(m.win_margin,'^[0-9]+') AS UNSIGNED) END),2) AS avg_margin_runs_b
        FROM matches m
        WHERE m.match_date >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR)
        GROUP BY LEAST(m.team1_id, m.team2_id), GREATEST(m.team1_id, m.team2_id)
        HAVING total_matches >= 5;
        """
    )

    # Q23
    cur.execute(
        """
        CREATE OR REPLACE VIEW q23_recent_form AS
        SELECT x.player_id, x.name,
               ROUND(AVG(CASE WHEN rn<=5 THEN runs END),2) AS avg_last5,
               ROUND(AVG(runs),2) AS avg_last10,
               SUM(CASE WHEN runs>=50 THEN 1 ELSE 0 END) AS fifties_in_last10,
               ROUND(STDDEV_SAMP(runs),2) AS consistency_std
        FROM (
            SELECT b.player_id, p.name, b.runs,
                   ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC, b.id DESC) AS rn
            FROM batting_stats b
            JOIN matches m ON m.match_id=b.match_id
            JOIN players p ON p.player_id=b.player_id
        ) x
        WHERE x.rn <= 10
        GROUP BY x.player_id, x.name;
        """
    )

    # Q24
    cur.execute(
        """
        CREATE OR REPLACE VIEW q24_best_partnerships AS
        SELECT pr.player1_id, pr.player2_id, p1.name AS player1, p2.name AS player2,
               ROUND(AVG(pr.runs),2) AS avg_partnership,
               SUM(CASE WHEN pr.runs>50 THEN 1 ELSE 0 END) AS over50_count,
               MAX(pr.runs) AS highest,
               COUNT(*) AS total_partnerships,
               ROUND(100.0 * SUM(CASE WHEN pr.runs>50 THEN 1 ELSE 0 END)/COUNT(*),2) AS success_rate
        FROM partnerships pr
        JOIN players p1 ON p1.player_id=pr.player1_id
        JOIN players p2 ON p2.player_id=pr.player2_id
        WHERE pr.pair_pos_diff=1 OR pr.pair_pos_diff IS NULL
        GROUP BY pr.player1_id, pr.player2_id, p1.name, p2.name
        HAVING total_partnerships >= 5
        ORDER BY success_rate DESC, avg_partnership DESC, highest DESC;
        """
    )

    # Q25
    cur.execute(
        """
        CREATE OR REPLACE VIEW q25_quarterly_trends AS
        SELECT player_id, name, yr, qtr,
               ROUND(AVG(runs),2) AS avg_runs,
               ROUND(AVG(NULLIF(sr,0)),2) AS avg_sr,
               matches_in_qtr,
               CASE
                 WHEN diff_prev > 1 THEN 'Improving'
                 WHEN diff_prev < -1 THEN 'Declining'
                 ELSE 'Stable'
               END AS trend
        FROM (
            SELECT p.player_id, p.name,
                   YEAR(m.match_date) AS yr,
                   QUARTER(m.match_date) AS qtr,
                   b.runs, b.strike_rate AS sr,
                   COUNT(*) OVER (PARTITION BY p.player_id, YEAR(m.match_date), QUARTER(m.match_date)) AS matches_in_qtr,
                   ROUND(AVG(b.runs) OVER (PARTITION BY p.player_id, YEAR(m.match_date), QUARTER(m.match_date)),2) AS avg_in_qtr,
                   ROUND(
                     AVG(b.runs) OVER (PARTITION BY p.player_id ORDER BY YEAR(m.match_date), QUARTER(m.match_date)
                                       ROWS BETWEEN 1 PRECEDING AND CURRENT ROW)
                     -
                     AVG(b.runs) OVER (PARTITION BY p.player_id ORDER BY YEAR(m.match_date), QUARTER(m.match_date)
                                       ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING)
                   ,2) AS diff_prev
            FROM batting_stats b
            JOIN matches m ON m.match_id=b.match_id
            JOIN players p ON p.player_id=b.player_id
        ) z
        WHERE matches_in_qtr >= 3
        GROUP BY player_id, name, yr, qtr, matches_in_qtr, trend;
        """
    )

    conn.commit()

# ================================
# Query registry (Q1–Q25)
# ================================

QUERIES: Dict[str, str] = {
    "Q1: Players who represent India":
        "SELECT * FROM q1_players_india",
    "Q2: Matches in the last 30 days":
        "SELECT * FROM q2_matches_last_30_days",
    "Q3: Top 10 ODI run scorers":
        "SELECT * FROM q3_top10_odi_run_scorers",
    "Q4: Venues with capacity > 50,000":
        "SELECT * FROM q4_big_venues",
    "Q5: Matches won by each team":
        "SELECT * FROM q5_team_wins",
    "Q6: Player counts by playing role":
        "SELECT * FROM q6_players_by_role",
    "Q7: Highest individual score per format":
        "SELECT * FROM q7_highest_individual_by_format",
    "Q8: Series started in 2024":
        "SELECT * FROM q8_series_started_2024",
    "Q9: All-rounders (>1000 runs & >50 wkts)":
        "SELECT * FROM q9_all_rounders_1000_50",
    "Q10: Last 20 completed matches":
        "SELECT * FROM q10_last20_completed",
    "Q11: Player performance across formats":
        "SELECT * FROM q11_player_format_compare",
    "Q12: Team wins at home vs away":
        "SELECT * FROM q12_home_away_wins",
    "Q13: Partnerships >= 100 runs (consecutive positions)":
        "SELECT * FROM q13_big_partnerships",
    "Q14: Bowling performance by venue":
        "SELECT * FROM q14_bowling_venue",
    "Q15: Players in close matches":
        "SELECT * FROM q15_close_matches",
    "Q16: Year-wise batting since 2020":
        "SELECT * FROM q16_yearly_perf_since_2020",
    "Q17: Toss win advantage by decision":
        "SELECT * FROM q17_toss_advantage",
    "Q18: Economical bowlers (ODI/T20I)":
        "SELECT * FROM q18_economical_limited_overs",
    "Q19: Most consistent batsmen since 2022":
        "SELECT * FROM q19_consistent_batsmen",
    "Q20: Matches & batting averages by format":
        "SELECT * FROM q20_formats_played_avg",
    "Q21: Composite performance ranking":
        "SELECT * FROM q21_composite_rank ORDER BY format, total_score DESC",
    "Q22: Head-to-head (last 3 years, >=5 matches)":
        "SELECT * FROM q22_head_to_head",
    "Q23: Recent form (last 10 innings)":
        "SELECT * FROM q23_recent_form",
    "Q24: Best batting partnerships (>=5 together)":
        "SELECT * FROM q24_best_partnerships",
    "Q25: Quarterly performance trends":
        "SELECT * FROM q25_quarterly_trends",
}

# ================================
# Streamlit UI
# ================================

st.set_page_config(page_title="SQL Analytics (25 Queries)", layout="wide")
st.title("🏏 SQL Analytics (Q1–Q25)")

# Keep a small session log for API calls
if "api_trace" not in st.session_state:
    st.session_state["api_trace"] = []

# Sidebar: controls & API usage
with st.sidebar:


    st.divider()
    st.subheader("Database Fill (Heavy)")
    from_year = st.number_input("From year (recommended: 2020)", min_value=2000, max_value=2030, value=2020, step=1)
    max_pages = st.slider("Max pages per list", min_value=1, max_value=200, value=30)
    if st.button("🚀 Full Backfill (Teams, Players, Series, Matches, Scorecards)"):
        try:
            conn = get_db_connection()
            init_schema(conn)
            with st.spinner("Loading teams & players..."):
                load_teams_and_players(conn)
            with st.spinner("Loading series & matches (deep)..."):
                load_all_series_and_matches(conn, from_year=int(from_year), max_pages=int(max_pages))
            with st.spinner("Creating analytics views..."):
                create_views(conn)
            conn.close()
            st.success(f"Full backfill completed. API used: {API_CALLS}")
        except Exception as e:
            st.error(f"Full backfill error: {e}")

    st.divider()
    st.subheader("Refresh (Light)")
    if st.button("🔄 Refresh Recent Matches"):
        try:
            conn = get_db_connection()
            init_schema(conn)
            with st.spinner("Refreshing recent matches & scorecards..."):
                incremental_refresh(conn, max_pages=5)
            with st.spinner("Refreshing analytics views..."):
                create_views(conn)
            conn.close()
            st.success(f"Recent refresh completed. API used: {API_CALLS}")
        except Exception as e:
            st.error(f"Refresh error: {e}")

    st.divider()
    with st.expander("API Call Trace (last 50)"):
        for line in st.session_state.get("api_trace", [])[-50:]:
            st.code(line, language="text")

# Main area: queries
st.subheader("📊 Run Analytics Queries")
query_name = st.selectbox("Select a query (Q1–Q25)", list(QUERIES.keys()))
sql_text = QUERIES[query_name]

cols = st.columns([1,1])
with cols[0]:
    if st.button("👁️ View SQL"):
        st.code(sql_text, language="sql")
with cols[1]:
    if st.button("▶️ Execute Query"):
        try:
            conn = get_db_connection()
            init_schema(conn)  # safe no-op if already created
            create_views(conn) # ensure latest definitions exist
            df = pd.read_sql(sql_text, conn)
            conn.close()
            st.success(f"Returned {len(df)} rows")
            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Query execution error: {e}")


st.caption("Tip: Do a Full Backfill once (from 2020) to populate most of the needed data for all queries. Use Refresh to keep it up-to-date with recent matches.")


if __name__ == "__main__":
    # 🔍 Debug a specific series
    series_id = 10840  # Afghanistan vs Bangladesh in UAE 2025
    sdet = extract_series_detail(series_id)
    import json
    print(json.dumps(sdet, indent=2)[:2000])  # preview first 2000 characters
