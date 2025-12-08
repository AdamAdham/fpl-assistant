"""
Cypher Template Library
----------------------

Contains all Cypher query templates and intent → template mapping rules
for the FPL Graph-RAG system.
"""

# Cypher Template Library
# ----------------------
# Contains all Cypher query templates and intent → template mapping rules for the FPL Graph-RAG system.

CYPHER_TEMPLATE_LIBRARY = {
    # -----------------------------------------------------
    # PLAYER PERFORMANCE & COMPARISON
    # -----------------------------------------------------
    # What are the stats for a player in a specific gameweek in a specific season?
    "PLAYER_STATS_GW_SEASON": """
      MATCH (p:Player {player_name: $player1})
         -[r:PLAYED_IN]->
         (f:Fixture)<-[:HAS_FIXTURE]-(gw:Gameweek {GW_number: $gw})
      WHERE gw.season = $season
      RETURN p.player_name AS player,
         gw.season AS season,
         gw.GW_number AS gw,
         r.*
      """,
    # How do two players compare in total points?
    "COMPARE_PLAYERS_BY_TOTAL_POINTS": """
       MATCH (p1:Player {player_name: $player1})
       OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
       WITH p1, coalesce(sum(r1.total_points), 0) AS p1_pts
       MATCH (p2:Player {player_name: $player2})
       OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
       RETURN
              p1.player_name AS player1,
              p1_pts AS player1_points,
              p2.player_name AS player2,
              coalesce(sum(r2.total_points), 0) AS player2_points
       """,
    # How do two players compare in a specific stat sum?
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_SUM": """
       MATCH (p1:Player {player_name: $player1})
       OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
       WITH p1, coalesce(sum(r1.$stat_property), 0) AS p1_sum_$stat_property
       MATCH (p2:Player {player_name: $player2})
       OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
       RETURN
              p1.player_name AS player1,
              p1_sum_$stat_property AS player1_sum_$stat_property,
              p2.player_name AS player2,
              coalesce(sum(r2.$stat_property), 0) AS player2_sum_$stat_property
       """,
    # How do two players compare in a specific stat average?
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_AVG": """
       MATCH (p1:Player {player_name: $player1})
       OPTIONAL MATCH (p1)-[r1:PLAYED_IN]->(:Fixture)
       WITH p1, coalesce(avg(r1.$stat_property), 0) AS p1_avg_$stat_property
       MATCH (p2:Player {player_name: $player2})
       OPTIONAL MATCH (p2)-[r2:PLAYED_IN]->(:Fixture)
       RETURN
              p1.player_name AS player1,
              p1_avg_$stat_property AS player1_avg_$stat_property,
              p2.player_name AS player2,
              coalesce(avg(r2.$stat_property), 0) AS player2_avg_$stat_property
       """,
    # What are the career stats totals for a player?
    "PLAYER_CAREER_STATS_TOTALS": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN p.player_name AS player,
              sum(r.total_points) AS total_points,
              sum(r.goals_scored) AS career_goals,
              sum(r.assists) AS career_assists,
              sum(r.clean_sheets) AS career_clean_sheets,
              count(r) AS matches_played
       """,
    # What are the specific stat sum for a player?
    "PLAYER_SPECIFIC_STAT_SUM": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN p.player_name AS player,
              sum(r.$stat_property) AS sum_$stat_property,
              count(r) AS matches_played
       """,
    # What are the specific stat avg for a player?
    "PLAYER_SPECIFIC_STAT_AVG": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN p.player_name AS player,
              avg(r.$stat_property) AS avg_$stat_property,
              count(r) AS matches_played
       """,
    # What are the specific stat sum for a player in a specific season?
    "PLAYER_SPECIFIC_STAT_SUM_SPECIFIC_SEASON": """
      MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
      MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
      WHERE gw.season = $season
      RETURN p.player_name AS player,
         sum(r.$stat_property) AS sum_$stat_property,
         count(r) AS matches_played
      """,
    # What are the specific stat avg for a player in a specific season?
    "PLAYER_SPECIFIC_STAT_AVG_SPECIFIC_SEASON": """
      MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
      MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
      WHERE gw.season = $season
      RETURN p.player_name AS player,
         avg(r.$stat_property) AS avg_$stat_property,
         count(r) AS matches_played
      """,
    # Who are the top players by a given stat?
    "TOP_PLAYERS_BY_STAT": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.$stat_property) AS total_stat
       RETURN p.player_name AS player, total_stat
       ORDER BY total_stat DESC
       LIMIT $limit
       """,
    # -----------------------------------------------------
    # TOP PERFORMERS & LEADERBOARDS
    # -----------------------------------------------------
    # Who are the top players in a given position in total_points?
    "TOP_PLAYERS_BY_POSITION_IN_POINTS": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.total_points) AS total_pts
       RETURN p.player_name AS player, total_pts
       ORDER BY total_pts DESC
       LIMIT $limit
    """,
    # Who are the top players in a given position by form?
    "TOP_PLAYERS_BY_POSITION_IN_FORM": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, avg(r.form) AS avg_form
       RETURN p.player_name AS player, avg_form
       ORDER BY avg_form DESC
       LIMIT $limit
    """,
    # Who are the top players under a certain budget, in a specific position, in a specific season?
    "TOP_PLAYERS_UNDER_BUDGET_SPECIFIC_POSITION_SPECIFIC_SEASON": """
      MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
      WHERE p.value <= $budget
      MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
      MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
      WHERE gw.season = $season
      WITH p, sum(r.total_points) AS total_pts
      RETURN p.player_name AS player,
         p.value AS value,
         total_pts
      ORDER BY total_pts DESC
      LIMIT $limit
      """,
    # Which players have the most stat in total?
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.$stat_property) AS stat_total
       RETURN p.player_name AS player, stat_total
       ORDER BY stat_total DESC
       LIMIT $limit
       """,
    # Which players have the most stat in a specific position?
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.$stat_property) AS stat_total
       RETURN p.player_name AS player, stat_total
       ORDER BY stat_total DESC
       LIMIT $limit
       """,
    # Which players have the best average of stat?
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, avg(r.$stat_property) AS stat_avg
       RETURN p.player_name AS player, stat_avg
       ORDER BY stat_avg DESC
       LIMIT $limit
       """,
    # Which players have the best average of stat in a specific position?
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, avg(r.$stat_property) AS stat_avg
       RETURN p.player_name AS player, stat_avg
       ORDER BY stat_avg DESC
       LIMIT $limit
       """,
    # -----------------------------------------------------
    # COMPOUND & DERIVED STATS
    # -----------------------------------------------------
    # Which players have the most yellow/red cards?
    "MOST_CARDS_LEADERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
       RETURN p.player_name AS player, yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
       ORDER BY disciplinary_score DESC
       LIMIT $limit
       """,
    # Which players have the most goal contributions (goals + assists)?
    "MOST_GOAL_CONTRIBUTIONS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.goals_scored) AS goals, sum(r.assists) AS assists
       RETURN p.player_name AS player, goals, assists, (goals + assists) AS goal_contributions
       ORDER BY goal_contributions DESC
       LIMIT $limit
       """,
    # Which players have the best minutes per point ratio?
    "MINUTES_PER_POINT_LEADERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
       WHERE total_points > 0 AND total_minutes > 0
       RETURN p.player_name AS player,
              total_minutes / total_points AS minutes_per_point
       ORDER BY minutes_per_point ASC
       LIMIT $limit
       """,
    # What is the minutes per point ratio for a specific player?
    "PLAYER_MINUTES_PER_POINT": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
         WITH sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
         WHERE total_points > 0 AND total_minutes > 0
         RETURN total_minutes / total_points AS minutes_per_point
         """,
    # What is the minutes per point ratio for a specific player in a specific season?
    "PLAYER_MINUTES_PER_POINT_SPECIFIC_SEASON": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
         MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE gw.season = $season
         WITH sum(r.minutes) AS total_minutes, sum(r.total_points) AS total_points
         WHERE total_points > 0 AND total_minutes > 0
         RETURN total_minutes / total_points AS minutes_per_point
         """,
    # What is the total number of cards for a specific player?
    "PLAYER_TOTAL_CARDS": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
         WITH sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
         RETURN yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
         """,
    # What is the total number of goal contributions for a specific player?
    "PLAYER_GOAL_CONTRIBUTIONS": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
         WITH sum(r.goals_scored) AS goals, sum(r.assists) AS assists
         RETURN goals, assists, (goals + assists) AS goal_contributions
         """,
    # What is the total number of goal contributions for a specific player in a specific season?
    "PLAYER_GOAL_CONTRIBUTIONS_SPECIFIC_SEASON": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
         MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE gw.season = $season
         WITH sum(r.goals_scored) AS goals, sum(r.assists) AS assists
         RETURN goals, assists, (goals + assists) AS goal_contributions
         """,
    # What is the total number of cards for a specific player in a specific season?
    "PLAYER_TOTAL_CARDS_SPECIFIC_SEASON": """
         MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
         MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
         WHERE gw.season = $season
         WITH sum(r.yellow_cards) AS yellow_cards, sum(r.red_cards) AS red_cards
         RETURN yellow_cards, red_cards, (yellow_cards * 1 + red_cards * 3) AS disciplinary_score
         """,
    # -----------------------------------------------------
    # TEAM ANALYSIS & AGGREGATES
    # -----------------------------------------------------
    # What is the average goals conceded per game for a team?
    "GET_TEAM_DEFENSE_STRENGTH": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       WITH f, t, sum(r.goals_conceded) AS gc_per_fixture
       RETURN t.name AS team, avg(gc_per_fixture) AS avg_goals_conceded_per_game
       """,
    # What is the average goals conceded per game for a team in a specific season?
    "GET_TEAM_DEFENSE_STRENGTH_SPECIFIC_SEASON": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       WHERE ((f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)) AND gw.season = $season
       WITH t, f, sum(r.goals_conceded) AS fixture_gc
       RETURN t.name AS team, avg(fixture_gc) AS avg_goals_conceded_per_fixture
       ORDER BY avg_goals_conceded_per_fixture ASC
       LIMIT 1
       """,
    # What is the average goals scored per game for a team?
    "GET_TEAM_ATTACK_STRENGTH": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       WITH t, f, sum(r.goals_scored) AS fixture_gs
       RETURN t.name AS team, avg(fixture_gs) AS avg_goals_scored_per_fixture
       ORDER BY avg_goals_scored_per_fixture DESC
       LIMIT 1
       """,
    # What is the average goals scored per game for a team in a specific season?
    "GET_TEAM_ATTACK_STRENGTH_SPECIFIC_SEASON": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       WHERE ((f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)) AND gw.season = $season
       WITH t, f, avg(r.goals_scored) AS fixture_gs
       RETURN t.name AS team, avg(fixture_gs) AS avg_goals_scored_per_fixture
       ORDER BY avg_goals_scored_per_fixture DESC
       LIMIT 1
       """,
    # What is the average goals conceded by a team at home vs away?
    "TEAM_AVG_GOALS_CONCEDED_HOME_AWAY": """
       MATCH (t:Team {name:$team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN
       avg(CASE WHEN (f)-[:HAS_HOME_TEAM]->(t) THEN r.goals_conceded END) AS home_gc,
       avg(CASE WHEN (f)-[:HAS_AWAY_TEAM]->(t) THEN r.goals_conceded END) AS away_gc
       """,
    # Which teams have the most clean sheets?
    "LEADING_TEAMS_BY_CLEAN_SHEETS": """
       MATCH (t:Team)
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       WITH t, sum(r.clean_sheets) AS team_clean_sheets
       RETURN t.name AS team, team_clean_sheets
       ORDER BY team_clean_sheets DESC
       LIMIT $limit
       """,
    # What is the total number of clean sheets for a team in a specific season?
    "TEAM_TOTAL_CLEAN_SHEETS_SPECIFIC_SEASON": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       WHERE ((f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)) AND gw.season = $season
       RETURN t.name AS team, sum(r.clean_sheets) AS total_clean_sheets
       """,
    # What is the total number of clean sheets for a team in all seasons?
    "TEAM_TOTAL_CLEAN_SHEETS_ALL_SEASONS": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN t.name AS team, sum(r.clean_sheets) AS total_clean_sheets
       """,
    # What is the total number of goals scored for a team in a specific season?
    "TEAM_TOTAL_GOALS_SCORED_SPECIFIC_SEASON": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       WHERE ((f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)) AND gw.season = $season
       RETURN t.name AS team, sum(r.goals_scored) AS total_goals_scored
       """,
    # What is the total number of goals scored for a team in all seasons?
    "TEAM_TOTAL_GOALS_SCORED_ALL_SEASONS": """
       MATCH (t:Team {name: $team1})
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN t.name AS team, sum(r.goals_scored) AS total_goals_scored
       """,
    # Which teams have the most goals scored?
    "LEADING_TEAMS_BY_GOALS_SCORED": """
       MATCH (t:Team)
       MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       WITH t, sum(r.goals_scored) AS team_goals_scored
       RETURN t.name AS team, team_goals_scored
       ORDER BY team_goals_scored DESC
       LIMIT $limit
       """,
    # Get fixtures between two teams?
    "GET_FIXTURES_BETWEEN_TEAMS": """
       MATCH (f:Fixture)
       MATCH (t1:Team {name: $team1})
       MATCH (t2:Team {name: $team2})
       WHERE
              ((f)-[:HAS_HOME_TEAM]->(t1) AND (f)-[:HAS_AWAY_TEAM]->(t2)) OR
              ((f)-[:HAS_HOME_TEAM]->(t2) AND (f)-[:HAS_AWAY_TEAM]->(t1))
       RETURN f.kickoff_time AS kickoff,
              t1.name AS team1,
              t2.name AS team2
       ORDER BY f.kickoff_time ASC
       """,
    # How many points has a player scored against a specific team?
    "PLAYER_POINTS_VS_SPECIFIC_TEAM": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (t:Team {name: $team1})
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN p.player_name AS player,
              t.name AS opponent,
              sum(r.total_points) AS total_points_vs_opponent,
              count(f) AS matches_played
       """,
    # -----------------------------------------------------
    # PLAYER VALUE & RECENT PERFORMANCE
    # -----------------------------------------------------
    # Which players offer the best value for money?
    "TOP_VALUE_FOR_MONEY_SPECIFIC_POSITION": """
       MATCH (p:Player)-[:PLAYS_AS]->(pos:Position {name: $position})
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.total_points) AS total_pts
       WHERE p.value IS NOT NULL AND p.value > 0 AND total_pts > 0
       RETURN p.player_name AS player,
              total_pts / p.value AS points_per_value
       ORDER BY points_per_value DESC
       LIMIT $limit
       """,
    # What are the last N fixtures and points for a player?
    "PLAYER_LAST_N_FIXTURES_PERFORMANCE": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       OPTIONAL MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       RETURN f.kickoff_time AS date, gw.GW_number AS gw, r.total_points
       ORDER BY date DESC
       LIMIT $limit
     """,
    # -----------------------------------------------------
    # PLAYER APPEARANCES, SPLITS & CONSISTENCY
    # -----------------------------------------------------
    # What is the maximum stat a player has achieved in a single match?
    "PLAYER_MAX_SPECIFIC_STAT_SINGLE_MATCH": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(:Fixture)
       RETURN max(r.$stat_property) AS max_$stat_property
       """,
    # How many fixtures in a specific season has a player appeared in?
    "PLAYER_FIXTURE_COUNT_SPECIFIC_SEASON": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       WHERE gw.season = $season
       RETURN count(r) AS appearances_in_season
       """,
    # How many fixtures in total has a player appeared?
    "PLAYER_FIXTURE_COUNT_TOTAL": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (gw:Gameweek)-[:HAS_FIXTURE]->(f)
       RETURN count(r) AS appearances_in_season
       """,
    # What are a player's points at home vs away?
    "PLAYER_POINTS_HOME_VS_AWAY": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       OPTIONAL MATCH (f)-[:HAS_HOME_TEAM]->(home)
       OPTIONAL MATCH (f)-[:HAS_AWAY_TEAM]->(away)
       RETURN
       sum(CASE WHEN home IS NOT NULL THEN r.total_points END) AS home_points,
       sum(CASE WHEN away IS NOT NULL THEN r.total_points END) AS away_points
       """,
    # Against which teams has a player scored the most points?
    "PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (t:Team)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN t.name AS opponent, sum(r.total_points) AS points
       ORDER BY points DESC
       LIMIT $limit
       """,
    # Against which teams has a player scored the fewest points?
    "PLAYER_WORST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": """
       MATCH (p:Player {player_name: $player1})-[r:PLAYED_IN]->(f:Fixture)
       MATCH (t:Team)
       WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
       RETURN t.name AS opponent, sum(r.total_points) AS points
       ORDER BY points ASC
       LIMIT $limit
       """,
    # Who is the most impactful player on a team?
    "TEAM_MOST_IMPACTFUL_PLAYER": """
       MATCH (t:Team {name:$team1})<-[:PLAYS_FOR]-(p:Player)
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH p, sum(r.total_points) AS pts
       RETURN p.player_name AS player, pts
       ORDER BY pts DESC
       LIMIT 1
       """,
    # Which position has the best average points?
    "POSITION_BEST_AVG_POINTS": """
       MATCH (pos:Position)<-[:PLAYS_AS]-(p:Player)
       MATCH (p)-[r:PLAYED_IN]->(:Fixture)
       WITH pos, avg(r.total_points) AS avg_points
       RETURN pos.name AS position, avg_points
       ORDER BY avg_points DESC
       """,
    # How many players are there in each position?
    "POSITION_PLAYERS_COUNT": """
       MATCH (pos:Position)<-[:PLAYS_AS]-(p:Player)
       RETURN pos.name AS position, count(p) AS players
       """,
    # Who are the least consistent players (highest stdev)?
    "LEAST_CONSISTENT_PLAYERS": """
       MATCH (p:Player)-[r:PLAYED_IN]->(:Fixture)
       WITH p, stdev(r.total_points) AS inconsistency
       RETURN p.player_name AS player, inconsistency
       ORDER BY inconsistency DESC
       LIMIT $limit
       """,
}

required_params_map = {
    # PLAYER PERFORMANCE & COMPARISON
    "PLAYER_STATS_GW_SEASON": ["player1", "gw", "season"],
    "COMPARE_PLAYERS_BY_TOTAL_POINTS": ["player1", "player2"],
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_SUM": ["player1", "player2", "stat_property"],
    "COMPARE_PLAYERS_BY_SPECIFIC_STAT_AVG": ["player1", "player2", "stat_property"],
    "PLAYER_CAREER_STATS_TOTALS": ["player1"],
    "PLAYER_SPECIFIC_STAT_SUM": ["player1", "stat_property"],
    "PLAYER_SPECIFIC_STAT_AVG": ["player1", "stat_property"],
    "PLAYER_SPECIFIC_STAT_SUM_SPECIFIC_SEASON": ["player1", "stat_property", "season"],
    "PLAYER_SPECIFIC_STAT_AVG_SPECIFIC_SEASON": ["player1", "stat_property", "season"],
    # TOP PERFORMERS & LEADERBOARDS
    "TOP_PLAYERS_BY_STAT": ["stat_property", "limit"],
    "TOP_PLAYERS_BY_POSITION_IN_POINTS": ["position", "limit"],
    "TOP_PLAYERS_BY_POSITION_IN_FORM": ["position", "limit"],
    "TOP_PLAYERS_UNDER_BUDGET_SPECIFIC_POSITION_SPECIFIC_SEASON": [
        "budget",
        "position",
        "season",
        "limit",
    ],
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS": ["stat_property", "limit"],
    "TOP_SUM_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": [
        "position",
        "stat_property",
        "limit",
    ],
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS": ["stat_property", "limit"],
    "TOP_AVG_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION": [
        "position",
        "stat_property",
        "limit",
    ],
    # COMPOUND & DERIVED STATS
    "MOST_CARDS_LEADERS": ["limit"],
    "MOST_GOAL_CONTRIBUTIONS": ["limit"],
    "MINUTES_PER_POINT_LEADERS": ["limit"],
    "PLAYER_MINUTES_PER_POINT": ["player1"],
    "PLAYER_MINUTES_PER_POINT_SPECIFIC_SEASON": ["player1", "season"],
    "PLAYER_TOTAL_CARDS": ["player1"],
    "PLAYER_GOAL_CONTRIBUTIONS": ["player1"],
    "PLAYER_TOTAL_CARDS_SPECIFIC_SEASON": ["player1", "season"],
    "PLAYER_GOAL_CONTRIBUTIONS_SPECIFIC_SEASON": ["player1", "season"],
    # TEAM ANALYSIS & AGGREGATES
    "GET_TEAM_DEFENSE_STRENGTH": ["team1"],
    "GET_TEAM_DEFENSE_STRENGTH_SPECIFIC_SEASON": ["team1", "season"],
    "GET_TEAM_ATTACK_STRENGTH": ["team1"],
    "GET_TEAM_ATTACK_STRENGTH_SPECIFIC_SEASON": ["team1", "season"],
    "TEAM_AVG_GOALS_CONCEDED_HOME_AWAY": ["team1"],
    "LEADING_TEAMS_BY_CLEAN_SHEETS": ["limit"],
    "TEAM_TOTAL_CLEAN_SHEETS_SPECIFIC_SEASON": ["team1", "season"],
    "TEAM_TOTAL_CLEAN_SHEETS_ALL_SEASONS": ["team1"],
    "TEAM_TOTAL_GOALS_SCORED_SPECIFIC_SEASON": ["team1", "season"],
    "TEAM_TOTAL_GOALS_SCORED_ALL_SEASONS": ["team1"],
    "LEADING_TEAMS_BY_GOALS_SCORED": ["limit"],
    "GET_FIXTURES_BETWEEN_TEAMS": ["team1", "team2"],
    "PLAYER_POINTS_VS_SPECIFIC_TEAM": ["player1", "team1"],
    # PLAYER VALUE & RECENT PERFORMANCE
    "TOP_VALUE_FOR_MONEY_SPECIFIC_POSITION": ["position", "limit"],
    "PLAYER_LAST_N_FIXTURES_PERFORMANCE": ["player1", "limit"],
    # PLAYER APPEARANCES, SPLITS & CONSISTENCY
    "PLAYER_MAX_SPECIFIC_STAT_SINGLE_MATCH": ["player1", "stat_property"],
    "PLAYER_FIXTURE_COUNT_SPECIFIC_SEASON": ["player1", "season"],
    "PLAYER_FIXTURE_COUNT_TOTAL": ["player1"],
    "PLAYER_POINTS_HOME_VS_AWAY": ["player1"],
    "PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": ["player1", "limit"],
    "PLAYER_WORST_PERFORMANCE_AGAINST_WHICH_OPPONENTS": ["player1", "limit"],
    "TEAM_MOST_IMPACTFUL_PLAYER": ["team1"],
    "POSITION_BEST_AVG_POINTS": [],
    "POSITION_PLAYERS_COUNT": [],
    "LEAST_CONSISTENT_PLAYERS": ["limit"],
}


def local_intent_classify(text: str) -> str:
    """Very small keyword-based fallback intent classifier."""
    t = text.lower()
    if any(w in t for w in ["captain", "recommend", "suggest", "transfer", "under"]):
        print("Transfer rec detected")
        return "TRANSFER_REC"
    if any(w in t for w in ["compare", "better", "vs", "vs."]):
        print("Compare intent detected")
        return "COMPARE"
    if any(w in t for w in ["fixture", "playing", "next", "opponent"]):
        print("Team fixture intent detected")
        return "TEAM_FIXTURE"
    if any(w in t for w in ["points", "how many", "goals", "assists", "stats"]):
        print("Player stats intent detected")
        return "PLAYER_STATS"
    return "GENERAL"
