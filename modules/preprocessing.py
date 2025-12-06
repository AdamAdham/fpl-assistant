# modules/preprocessing.py

"""
This module handles:
1. Intent classification (keyword-based)
2. Entity extraction (NER + regex)
3. Fuzzy matching entities to Neo4j node values

Author: ACL M3 FPL Graph-RAG
"""

import re
from typing import Dict, List, Optional
import spacy
from thefuzz import (
    process,
    fuzz,
)

# TODO decide on wether to keep thefuzz only or both fuzzywuzzy and thefuzz
from fuzzywuzzy import fuzz

from modules.db_manager import Neo4jGraph
from config.stat_variants import STAT_VARIANTS


# ----------------------------
# Load spaCy model once
# ----------------------------
try:
    nlp = spacy.load("en_core_web_trf")  # transformer model
except:
    nlp = spacy.load("en_core_web_sm")  # fallback


# ----------------------------
# Raw Entity Extraction
# ----------------------------


def extract_entities(user_query: str) -> Dict[str, List[str]]:
    entities = {
        "players": [],
        "teams": [],
        "gameweeks": [],
        "positions": [],
        "seasons": [],
        "statistics": [],
    }

    query_lower = user_query.lower()
    
    # Run spaCy NER pipeline to extract named entities
    doc = nlp(user_query)
     
    # Extract PERSON entities as potential player names from the spacy NER(DIDNT WORK AT ALL)
    #spacy_persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    
    # Extract ORG entities as potential team names from the spacy NER
    spacy_orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

    # ------------------
    # Gameweeks
    # ------------------
    gw_matches = re.findall(r"(?:gw|gameweek|week|round|matchday)\s?(\d+)", query_lower)
    if gw_matches:
        entities["gameweeks"] = [int(g) for g in gw_matches]

    # ------------------
    # Positions
    # ------------------
    position_variants = {
        "DEF": ["defender", "defenders", "defence", "defense", "backline", "def", "back"],
        "MID": ["midfielder", "midfielders", "midfield", "mid"],
        "FWD": ["forward", "forwards", "attacker", "attackers", "striker", "strikers", "attack", "fwd"],
        "GK": ["goalkeeper", "goalkeepers", "keeper", "keepers", "goalies", "goalie", "gk"],
    }
    for code, variants in position_variants.items():
        for var in variants:
            # First, check for exact substring match (most reliable)
            if var in query_lower:
                if code not in entities["positions"]:
                    entities["positions"].append(code)
                break
            # Fallback: Use fuzzy matching for typos/variations
            elif fuzz.token_set_ratio(var, query_lower) >= 85:
                if code not in entities["positions"]:
                    entities["positions"].append(code)
                break

    # ------------------
    # Teams
    # ------------------
    all_teams = fetch_all_names_from_db("Team", "name")
    
    # Team abbreviations mapping - mapped to EXACT names in database
    team_abbrev = {
        "mci": "Man City",
        "manchester city": "Man City",
        "mancity": "Man City",
        "city": "Man City",
        "mun": "Man Utd",
        "manchester united": "Man Utd",
        "manchester utd": "Man Utd",
        "manutd": "Man Utd",
        "united": "Man Utd",
        "liv": "Liverpool",
        "liver": "Liverpool",
        "lfc": "Liverpool",
        "che": "Chelsea",
        "ars": "Arsenal",
        "gunners": "Arsenal",
        "tot": "Spurs",
        "tottenham": "Spurs",
        "Tottenham Hotspur": "Spurs",
        "lei": "Leicester",
        "whu": "West Ham",
        "hammers": "West Ham",
        "west ham united": "West Ham",
        "eve": "Everton",
        "avl": "Aston Villa",
        "villa": "Aston Villa",\
        "Aston": "Aston Villa",
        "new": "Newcastle",
        "newcastle utd": "Newcastle",
        "newcastle united": "Newcastle",
        "nufc": "Newcastle",
        "bha": "Brighton",
        "brighton": "Brighton",
        "brighton & hove albion": "Brighton",
        "wol": "Wolves",
        "wolverhampton": "Wolves",
        "Wolverhampton Wanderers": "Wolves",
        "sou": "Southampton",
        "saints": "Southampton",
        "cry": "Crystal Palace",
        "palace": "Crystal Palace",
        "cpfc": "Crystal Palace",
        "crystal": "Crystal Palace",
        "ful": "Fulham",
        "bou": "Bournemouth",
        "AFC Bournemouth": "Bournemouth",
        "bur": "Burnley",
        "lee": "Leeds",
        "Leeds United": "Leeds",
        "lufc": "Leeds",
        "nor": "Norwich",
        "Norwich City": "Norwich",
        "ncfc": "Norwich",
        "wat": "Watford",
        "bre": "Brentford",
        "nffc": "Nott'm Forest",
        "nottingham": "Nott'm Forest",
        "forest": "Nott'm Forest",
        "nott'm": "Nott'm Forest",
    }
    
    # First, check for team abbreviations (like we do name parts for players)
    for abbrev, full_name in team_abbrev.items():
        if re.search(r'\b' + re.escape(abbrev) + r'\b', query_lower):
            if full_name in all_teams and full_name not in entities["teams"]:
                entities["teams"].append(full_name)
    
    # Second, use spaCy's ORG entities and fuzzy match them
    for org in spacy_orgs:
        best_match = process.extractOne(
            org, 
            all_teams, 
            scorer=fuzz.token_sort_ratio, 
            score_cutoff=85
        )
        if best_match and best_match[0] not in entities["teams"]:
            entities["teams"].append(best_match[0])
    
    # Third, check for exact substring matches (case-insensitive)
    for team in all_teams:
        if team.lower() in query_lower:
            if team not in entities["teams"]:
                entities["teams"].append(team)

    # ------------------
    # Players
    # ------------------
    all_players = fetch_all_names_from_db("Player", "player_name")
    matched_players = []
    
    # Approach 1: Full name fuzzy matching (handles "Mohamed Salah stats")
    for player_name in all_players:
        score = fuzz.token_set_ratio(player_name.lower(), query_lower)
        if score >= 80:
            matched_players.append((player_name, score))
    
    # Approach 2: Partial name matching (handles "Salah goals", "Son assists")
    # Only check if we haven't found good matches yet
    if len(matched_players) < 2:
        for player_name in all_players:
            name_parts = player_name.lower().split()
            
            for part in name_parts:
                # Check if a name part appears as a standalone word in the query
                if len(part) >= 3 and re.search(r'\b' + re.escape(part) + r'\b', query_lower):
                    # Verify this isn't already matched
                    if not any(player_name == m[0] for m in matched_players):
                        # Score based on how unique/long the matching part is
                        score = fuzz.token_set_ratio(player_name.lower(), query_lower)
                        matched_players.append((player_name, score))
                    break
    
    matched_players.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    for name, score in matched_players:
        if name not in seen:
            entities["players"].append(name)
            seen.add(name)

    # ------------------
    # Seasons
    # ------------------
    # Match exact season patterns like "2021-22" or "21-22"
    season_pattern = r'\b(2021-22|2022-23|21-22|22-23)\b'
    season_matches = re.findall(season_pattern, user_query, re.IGNORECASE)
    
    season_map = {
        "21-22": "2021-22",
        "2021-22": "2021-22",
        "22-23": "2022-23",
        "2022-23": "2022-23",
    }
    
    for match in season_matches:
        normalized = season_map.get(match.lower())
        if normalized and normalized not in entities["seasons"]:
            entities["seasons"].append(normalized)
    
    # Fallback: Find standalone years like "season 22"
    if not entities["seasons"]:  # Only if no exact season pattern matched
        year_map = {
            21: "2021-22",
            2021: "2021-22",
            22: "2022-23",
            2022: "2022-23",
        }
        year_matches = re.findall(r'\b(20\d{2}|2[12])\b', user_query)
        for year in year_matches:
            year_int = int(year)
            if year_int in year_map:
                season = year_map[year_int]
                if season not in entities["seasons"]:
                    entities["seasons"].append(season)

    # ------------------
    # Statistics
    # ------------------
    for stat, variants in STAT_VARIANTS.items():
        for var in variants:
            # For very short variants (2-3 chars), use word boundaries to avoid false matches
            if len(var) <= 3:
                if re.search(r'\b' + re.escape(var) + r'\b', query_lower):
                    if stat not in entities["statistics"]:
                        entities["statistics"].append(stat)
                        break
            else:
                # For longer variants, check for exact substring match (most reliable)
                if var.lower() in query_lower:
                    if stat not in entities["statistics"]:
                        entities["statistics"].append(stat)
                        break
                # Use fuzzy matching for typos/variations
                elif fuzz.token_set_ratio(var.lower(), query_lower) >= 85:
                    if stat not in entities["statistics"]:
                        entities["statistics"].append(stat)
                        break

    return entities


# ----------------------------
# DB Helpers: Fetch valid names
# ----------------------------


def fetch_all_names_from_db(label: str, property_name: str) -> List[str]:
    """
    Loads names from Neo4j, e.g. fetch_all_names_from_db("Player", "player_name")
    """
    query = f"""
    MATCH (n:{label})
    RETURN n.{property_name} AS name
    """

    db = Neo4jGraph()
    result = db.execute_query(query)

    return [row["name"] for row in result]
