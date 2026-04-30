import requests
import json
from datetime import datetime

# --- Configuration ---
LEAGUE_SHORTCUT = "bl1"          # bl1, bl2, prem (if available), etc.
LEAGUE_SEASON = None             # None = current season, or int like 2024
GROUP_ORDER_ID = None            # None = current matchday, or int like 8

# Fallback logo (OpenLigaDB doesn't provide logos)
FALLBACK_LOGO = "https://example.com/placeholder.png"

def fetch_matches(league, season=None, group=None):
    """Fetch matches from OpenLigaDB following official API."""
    if group is not None:
        url = f"https://api.openligadb.de/getmatchdata/{league}/{season}/{group}"
    elif season is not None:
        url = f"https://api.openligadb.de/getmatchdata/{league}/{season}"
    else:
        url = f"https://api.openligadb.de/getmatchdata/{league}"
    
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            print(f"Unexpected response: {type(data)}")
            return []
        
        if len(data) == 0:
            print("No matches found.")
            return []
        
        print(f"Received {len(data)} matches")
        matches = []
        
        for match in data:
            # Extract teams (note: lowercase keys!)
            team1 = match.get("team1")
            team2 = match.get("team2")
            if not team1 or not team2:
                print(f"Skipping match {match.get('matchID')} - missing teams")
                continue
            
            home_team = team1.get("teamName")
            away_team = team2.get("teamName")
            if not home_team or not away_team:
                continue
            
            # Determine status
            if match.get("matchIsFinished"):
                status = "FINISHED"
            elif match.get("matchIsLive"):
                status = "LIVE"
            else:
                status = "SCHEDULED"
            
            # Extract final score (resultTypeID == 2)
            home_score = 0
            away_score = 0
            match_results = match.get("matchResults", [])
            for res in match_results:
                if res.get("resultTypeID") == 2:  # Final result
                    home_score = res.get("pointsTeam1", 0)
                    away_score = res.get("pointsTeam2", 0)
                    break
            
            # Build output object
            match_obj = {
                "id": str(match.get("matchID", "")),
                "status": status,
                "home_team": home_team,
                "away_team": away_team,
                "home_logo": FALLBACK_LOGO,
                "away_logo": FALLBACK_LOGO,
                "score": {"home": home_score, "away": away_score},
                "minute": 0,   # OpenLigaDB doesn't provide minute by minute
                "league": match.get("leagueName", league.upper())
            }
            matches.append(match_obj)
        
        return matches
    except Exception as e:
        print(f"Error: {e}")
        return []

def save_to_json(matches):
    output = {
        "last_updated": datetime.now().isoformat(),
        "matches": matches
    }
    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved {len(matches)} matches to data.json")

if __name__ == "__main__":
    # Try to get current season (no season param) first
    matches = fetch_matches(LEAGUE_SHORTCUT, season=None, group=None)
    
    # If empty, try with a known past season (e.g., 2024)
    if not matches:
        print("No current matches, trying season 2024...")
        matches = fetch_matches(LEAGUE_SHORTCUT, season=2024, group=None)
    
    # Fallback to another league if still empty (e.g., Austrian Bundesliga)
    if not matches:
        print("Trying Austrian Bundesliga (aut1)...")
        matches = fetch_matches("aut1", season=None, group=None)
    
    if matches:
        save_to_json(matches)
    else:
        print("No matches found. Check league shortcut or network.")
