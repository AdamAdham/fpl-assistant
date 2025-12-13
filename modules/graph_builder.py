from modules.db_manager import Neo4jGraph

db = Neo4jGraph()


#  Intent mapping to graph type

GRAPHABLE_INTENTS = {
    # Player -> Fixture -> Team graph
    "PLAYER_LAST_N_FIXTURES_PERFORMANCE": "player_history",
    "PLAYER_STATS_GW_SEASON": "player_history",
    "PLAYER_CAREER_STATS_TOTALS": "player_history",
    "PLAYER_POINTS_VS_SPECIFIC_TEAM": "player_history",

    # Comparison graph
    "COMPARE_PLAYERS_BY_TOTAL_POINTS": "comparison",
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_TOTAL_ALL_TIME": "comparison",
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_AVG": "comparison",

    # Team -> Fixture -> Opponents graph
    "GET_FIXTURES_BETWEEN_TEAMS": "team_fixture",
    "GET_TEAM_DEFENSE_STRENGTH": "team_fixture",

    # Leaderboard graph
    "TOP_PLAYERS_BY_STAT": "leaderboard",
    "TOP_PLAYERS_BY_POSITION_IN_POINTS": "leaderboard",
    "LEADING_TEAMS_BY_GOALS_SCORED": "leaderboard",

    # Position graph
    "POSITION_PLAYERS_COUNT": "position",
}


def build_player_history_graph(player, limit=5):
    cypher = """
    MATCH (p:Player {player_name:$player})-[:PLAYED_IN]->(f:Fixture)
    OPTIONAL MATCH (f)-[:HAS_HOME_TEAM]->(ht:Team)
    OPTIONAL MATCH (f)-[:HAS_AWAY_TEAM]->(at:Team)
    RETURN p, f, ht, at
    ORDER BY f.fixture_number DESC
    LIMIT $limit
    """

    rows = db.execute_query(cypher, {"player": player, "limit": limit})

    nodes = {}
    relationships = []

    for r in rows:
        p = r.get("p")
        f = r.get("f")
        ht = r.get("ht")
        at = r.get("at")

        # Player node
        if p:
            pid = p["player_name"]
            nodes[pid] = {"id": pid, "label": "Player"}

        # Fixture node
        if f:
            fid = f["fixture_number"]
            nodes[fid] = {"id": fid, "label": "Fixture"}
            relationships.append({"start": pid, "end": fid, "type": "PLAYED_IN"})

        # Home team node
        if ht:
            tid = ht["name"]
            nodes[tid] = {"id": tid, "label": "Team"}
            relationships.append({"start": fid, "end": tid, "type": "HOME_TEAM"})

        # Away team node
        if at:
            tid = at["name"]
            nodes[tid] = {"id": tid, "label": "Team"}
            relationships.append({"start": fid, "end": tid, "type": "AWAY_TEAM"})

    return list(nodes.values()), relationships


def build_comparison_graph(player1, player2):
    nodes = {
        player1: {"id": player1, "label": "Player"},
        player2: {"id": player2, "label": "Player"}
    }

    rels = [
        {"start": player1, "end": player2, "type": "COMPARES_WITH"}
    ]

    return list(nodes.values()), rels


def build_team_fixture_graph(team1, team2):
    cypher = """
    MATCH (f:Fixture)
    MATCH (t1:Team {name:$team1})
    MATCH (t2:Team {name:$team2})
    WHERE 
        ((f)-[:HAS_HOME_TEAM]->(t1) AND (f)-[:HAS_AWAY_TEAM]->(t2))
        OR
        ((f)-[:HAS_HOME_TEAM]->(t2) AND (f)-[:HAS_AWAY_TEAM]->(t1))
    RETURN f, t1, t2
    """


    rows = db.execute_query(cypher, {"team1": team1, "team2": team2})

    nodes = {}
    rels = []
    nodes[team1] = {"id": team1, "label": "Team"}
    nodes[team2] = {"id": team2, "label": "Team"}
    for r in rows:
        f = r.get("f")

        fid = f["fixture_number"]
        nodes[fid] = {"id": fid, "label": "Fixture"}

        rels.append({"start": team1, "end": fid, "type": "INVOLVED_IN"})
        rels.append({"start": team2, "end": fid, "type": "INVOLVED_IN"})

    return list(nodes.values()), rels


def build_leaderboard_graph(results, stat_name="stat"):
    nodes = {}
    edges = []

    center = f"Top_{stat_name}"
    nodes[center] = {"id": center, "label": "Leaderboard"}

    for row in results:
        p = row.get("player")
        nodes[p] = {"id": p, "label": "Player"}
        edges.append({"start": center, "end": p, "type": stat_name})

    return list(nodes.values()), edges


def build_position_graph(results):
    nodes = {"Positions": {"id": "Positions", "label": "Positions"}}
    edges = []

    for row in results:
        pos = row["position"]
        nodes[pos] = {"id": pos, "label": "Position"}
        edges.append({"start": "Positions", "end": pos, "type": "HAS_PLAYERS"})

    return list(nodes.values()), edges



# Main dispatcher


def build_graph(intent, params, results):
    graph_type = GRAPHABLE_INTENTS.get(intent)

    if not graph_type:
        return [], []

    if graph_type == "player_history":
        return build_player_history_graph(params.get("player1"), params.get("limit", 5))

    if graph_type == "comparison":
        return build_comparison_graph(params.get("player1"), params.get("player2"))

    if graph_type == "team_fixture":
        return build_team_fixture_graph(params.get("team1"), params.get("team2"))

    if graph_type == "leaderboard":
        stat_name = params.get("stat_property", "stat")
        return build_leaderboard_graph(results, stat_name)

    if graph_type == "position":
        return build_position_graph(results)

    return [], []
