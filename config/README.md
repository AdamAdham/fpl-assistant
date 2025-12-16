# Configuration Module

The `config/` directory contains all lookup tables, templates, and settings that power the FPL Graph-RAG system. These files enable robust entity recognition, flexible query templating, and consistent model/retrieval configuration across the application.

---

## 📁 File Overview

### **settings.py** — Application Configuration & Model Selection

Central configuration hub for model choices, embedding options, and retrieval defaults.

**Key Variables:**

- **`EMBEDDING_MODEL_OPTIONS`** — Maps embedding model names to internal identifiers

  - `"all-MiniLM-L6-v2"` → `"A"` (fast, 22M params)
  - `"all-mpnet-base-v2"` → `"B"` (high-quality, 109M params)

- **`MODEL_OPTIONS`** — Maps LLM providers to internal identifiers

  - `"DeepSeek"` → `"A"` (default, cost-effective)
  - `"Llama"` → `"B"` (via Hugging Face Inference API)
  - `"Gemma"` → `"C"` (fast, lightweight)

- **`VECTOR_TOP_K`** — Number of results returned by vector search (default: 5)

- **`DEFAULT_RETRIEVAL_MODE`** — Default retrieval strategy
  - Options: `"Baseline (Cypher)"`, `"Embeddings"`, `"Hybrid"`
  - Streamlit UI allows users to override

**Usage:**

```python
from config.settings import MODEL_OPTIONS, EMBEDDING_MODEL_OPTIONS

llm_choice = st.selectbox("Select LLM", list(MODEL_OPTIONS.keys()))
# "DeepSeek", "Llama", or "Gemma"
```

---

### **template_library.py** — Cypher Query Templates & Intent Mapping

The backbone of the retrieval system. Contains 35+ parameterized Cypher query templates and intent classification rules.

**Structure:**

1. **`CYPHER_TEMPLATE_LIBRARY`** — Dictionary of intent → Cypher template mappings

   **Example Template:**

   ```cypher
   "PLAYER_STATS_GW_SEASON": """
   MATCH (p:Player {player_name: $player1})
      -[r:PLAYED_IN]->(f:Fixture)<-[gw_rel:HAS_FIXTURE]-(gw:Gameweek {GW_number: $gw})
   WHERE gw.season = $season
   RETURN p.player_name, gw.season, gw.GW_number, r.total_points, ...
   """
   ```

2. **`INTENT_PARAMETER_MAP`** — Maps each intent to required/optional parameters

   ```python
   "PLAYER_STATS_GW_SEASON": ["player1", "gw", "season"],
   "COMPARE_PLAYERS_BY_TOTAL_POINTS": ["player1", "player2"],
   ```

3. **`local_intent_classify(text: str) → str`** — Fallback rule-based intent classifier

   Uses keyword matching when LLM classification is unavailable:

   - `["captain", "recommend", "suggest", "transfer"]` → `"PLAYER_POINTS_PER_MINUTE_SPECIFIC_SEASON"`
   - `["compare", "better", "vs"]` → `"COMPARE_PLAYERS_BY_TOTAL_POINTS"`
   - `["fixture", "playing", "next", "opponent"]` → `"PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS"`

**Query Categories:**

| Category           | Example Intent                                    | Purpose                                   |
| ------------------ | ------------------------------------------------- | ----------------------------------------- |
| **Player Stats**   | `PLAYER_STATS_GW_SEASON`                          | Single player's performance in a gameweek |
| **Comparisons**    | `COMPARE_PLAYERS_BY_TOTAL_POINTS`                 | Head-to-head player metrics               |
| **Career Totals**  | `PLAYER_CAREER_STATS_TOTALS`                      | Aggregate stats across all gameweeks      |
| **Rankings**       | `TOP_PLAYERS_BY_POSITION`                         | Ranked lists by position/stat             |
| **Team Analysis**  | `TEAM_FIXTURE_SCHEDULE`                           | Fixture lists and opponent analysis       |
| **Opponent Stats** | `PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS` | Performance distribution by opponent      |

**Usage:**

```python
from config.template_library import CYPHER_TEMPLATE_LIBRARY, INTENT_PARAMETER_MAP

intent = "PLAYER_STATS_GW_SEASON"
cypher = CYPHER_TEMPLATE_LIBRARY[intent]
required_params = INTENT_PARAMETER_MAP[intent]
```

---

### **team_name_variants.py** — Team Name Normalization

Fuzzy name matching dictionary that maps user inputs (abbreviations, nicknames, typos) to canonical team names.

**Key Features:**

- **Abbreviations**: `"mci"` → `"Man City"`, `"liv"` → `"Liverpool"`
- **Full Names**: `"manchester city"` → `"Man City"`, `"arsenal"` → `"Arsenal"`
- **Nicknames**: `"gunners"` → `"Arsenal"`, `"hammers"` → `"West Ham"`
- **Variations**: `"mun"`, `"manchester united"`, `"united"` all → `"Man Utd"`

**Covers all 20 Premier League teams:**

- Man City, Man Utd, Liverpool, Arsenal, Chelsea, Tottenham, Newcastle, Brighton, Aston Villa
- Leicester, West Ham, Everton, Wolves, Southampton, Crystal Palace, Fulham, Bournemouth, Burnley, Leeds, etc.

**Usage:**

```python
from config.team_name_variants import TEAM_ABBREV

user_input = "arsenal"
canonical_name = TEAM_ABBREV.get(user_input.lower(), user_input)
# → "Arsenal"
```

---

### **stat_variants.py** — Statistic Name Normalization

Maps user-friendly stat names to canonical database property names.

**Coverage:**

| Canonical Property | User Variants                                             |
| ------------------ | --------------------------------------------------------- |
| `goals_scored`     | "goals scored", "scored goals", "goal", "goals", "scored" |
| `assists`          | "assist", "assists"                                       |
| `clean_sheets`     | "clean sheet", "clean sheets", "cs"                       |
| `total_points`     | "total points", "points", "total"                         |
| `yellow_cards`     | "yellow card", "yellow cards", "yc"                       |
| `red_cards`        | "red card", "red cards"                                   |
| `minutes`          | "minutes", "mins", "played minutes"                       |
| `bonus`            | "bonus", "bps"                                            |
| `ict_index`        | "ict", "ict index"                                        |
| `penalties_saved`  | "penalty saved", "penalties saved"                        |
| `penalties_missed` | "penalty missed", "penalties missed"                      |
| `transfers_in`     | "transfers in", "transfer in"                             |
| `transfers_out`    | "transfers out", "transfer out"                           |
| `saves`            | "save", "saves"                                           |
| `goals_conceded`   | "conceded", "goals conceded", "goals allowed"             |

**Usage:**

```python
from config.stat_variants import STAT_VARIANTS

user_stat = "goals"
canonical_stat = None
for key, variants in STAT_VARIANTS.items():
    if user_stat.lower() in variants:
        canonical_stat = key
        break
# → "goals_scored"
```

---

### **FPLTrivia.md** — Common User Queries Reference

A **markdown document** listing 60+ typical Fantasy Premier League questions that the system is designed to answer.

**Organized Categories:**

1. **Player Performance & Statistics**

   - Total points, goals, assists, clean sheets per season
   - Best/worst gameweeks, form trends, ICT breakdown

2. **Player vs Team & Opponent Analysis**

   - Points scored against specific teams
   - Home vs away splits

3. **Top Performers & Recommendations**

   - Highest scorers by position
   - Best value for money

4. **Team Analysis & Fixtures**

   - Average goals per game, clean sheets, fixture difficulty

5. **Miscellaneous & Trivia**
   - Most yellow/red cards, minutes played, goal contributions

**Purpose:**

- Training reference for evaluating query understanding
- Benchmark test cases for system evaluation
- Documentation of system scope and capabilities

---

### **standby_library.py** — Legacy/Backup Query Templates

Contains older Cypher templates and fallback patterns. Used when `template_library.py` doesn't cover an edge case.

**When Used:**

- Historical template variants
- Fallback patterns for niche queries
- A/B testing different Cypher approaches

---

### **old_template_library.py** — Deprecated Query Templates

Archive of outdated templates. Kept for reference or reverting if schema changes occur.

---

### ****init**.py** — Module Exports

Exposes the most commonly used configuration objects to simplify imports:

```python
from config import MODEL_OPTIONS, EMBEDDING_MODEL_OPTIONS, VECTOR_TOP_K
```

**Exported:**

- `MODEL_OPTIONS` — LLM choices
- `EMBEDDING_MODEL_OPTIONS` — Embedding model choices
- `VECTOR_TOP_K` — Default vector search result count

---

## 🔄 Data Flow Through Config

```
User Query
    ↓
┌─────────────────────────────────────────────┐
│ preprocessing.py (in modules/)              │
│ ├─ Extract entities (players, teams, stats) │
│ ├─ Team name normalization (team_name_variants.py)│
│ ├─ Stat name normalization (stat_variants.py)    │
│ └─ Intent classification (template_library.py)   │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ cypher_retriever.py (in modules/)           │
│ ├─ Select template from CYPHER_TEMPLATE_LIBRARY│
│ ├─ Validate required parameters             │
│ └─ Execute against Neo4j                    │
└─────────────────────────────────────────────┘
    ↓
Database Results → LLM → Natural Language Answer
```

---

## 🚀 Adding New Features

### Adding a New Query Template

1. **Define Cypher template** in `template_library.py`:

   ```python
   "NEW_QUERY_NAME": """
   MATCH (p:Player)...
   RETURN ...
   """
   ```

2. **Register parameters** in `INTENT_PARAMETER_MAP`:

   ```python
   "NEW_QUERY_NAME": ["param1", "param2"]
   ```

3. **Add fallback keywords** to `local_intent_classify()`:
   ```python
   if any(w in t for w in ["keyword1", "keyword2"]):
       return "NEW_QUERY_NAME"
   ```

### Adding Team/Player Name Variants

Edit `team_name_variants.py`:

```python
"new_abbrev": "Canonical Name",
"alternate_spelling": "Canonical Name",
```

### Adding Stat Aliases

Edit `stat_variants.py`:

```python
"database_property": ["user_variant1", "user_variant2", ...]
```

---

## 📝 Notes

- All **parameter injection** uses Neo4j's `$param` syntax (safe from Cypher injection)
- **Config is loaded at startup**; changes require app restart
- **Embedding models** are cached in memory after first load
- **Team/stat mappings** support case-insensitive lookups

---

**Last Updated:** December 2025  
**Status:** Active Configuration  
**Related:** See [main README](../README.md) for full system documentation
