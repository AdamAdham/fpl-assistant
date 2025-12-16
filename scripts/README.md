# Scripts Directory

The `scripts/` directory contains initialization and setup scripts for populating the Neo4j knowledge graph and generating semantic embeddings for the FPL Graph-RAG system.

---

## 📁 File Overview

### **fpl_two_seasons.csv** — Raw FPL Data Source

The complete raw dataset containing player performance statistics across two seasons (2021-22 and 2022-23).

**Structure:**

- **~1,200 rows** (600 players/season × 2 seasons)
- **38 rows per player** (one per gameweek)
- **34 columns** of player and fixture data

**Columns:**

| Column                          | Type      | Description                                         |
| ------------------------------- | --------- | --------------------------------------------------- |
| `season`                        | string    | "2021-22" or "2022-23"                              |
| `name`                          | string    | Player name                                         |
| `position`                      | string    | "GK", "DEF", "MID", "FWD"                           |
| `element`                       | int       | Unique player ID in FPL                             |
| `fixture`                       | int       | Fixture number (1-380 per season)                   |
| `kickoff_time`                  | timestamp | Match start time                                    |
| `home_team` / `away_team`       | string    | Team names                                          |
| `team_a_score` / `team_h_score` | int       | Match result scores                                 |
| **Performance Stats**           |           |                                                     |
| `minutes`                       | int       | Minutes played                                      |
| `goals_scored`                  | int       | Goals scored by player                              |
| `assists`                       | int       | Assists provided                                    |
| `total_points`                  | int       | Fantasy points earned (main metric)                 |
| `bonus`                         | int       | Bonus points awarded                                |
| `clean_sheets`                  | int       | Match without conceding (defenders/GK)              |
| `goals_conceded`                | int       | Goals conceded (defenders/GK)                       |
| `yellow_cards`                  | int       | Disciplinary count                                  |
| `red_cards`                     | int       | Red card count                                      |
| `saves`                         | int       | Saves made (GK)                                     |
| `penalties_saved`               | int       | Penalties saved (GK)                                |
| `penalties_missed`              | int       | Penalties missed                                    |
| `bps`                           | int       | Bonus Point System (raw scoring metric)             |
| **Advanced Stats**              |           |                                                     |
| `influence`                     | float     | Statistical influence measure (0-1000)              |
| `creativity`                    | float     | Creative involvement measure (0-1000)               |
| `threat`                        | float     | Threat level measure (0-1000)                       |
| `ict_index`                     | float     | Composite of Influence + Creativity + Threat        |
| `form`                          | float     | Player's recent form (0-10)                         |
| **Transfer Data**               |           |                                                     |
| `selected`                      | int       | % of teams with player                              |
| `value`                         | int       | Player value in £100k units (actual = value × 0.1M) |
| `transfers_in`                  | int       | Transfers INTO player this gameweek                 |
| `transfers_out`                 | int       | Transfers OUT OF player this gameweek               |
| `transfers_balance`             | int       | transfers_in - transfers_out                        |
| `GW`                            | int       | Gameweek number (1-38)                              |

**Usage in System:**

This CSV is loaded by `create_kg.py` to populate Neo4j with:

- Player nodes with performance statistics
- Season/Gameweek/Fixture hierarchy
- Team information
- Relationship data (PLAYED_IN with full performance properties)

---

### **create_kg.py** — Knowledge Graph Population

Transforms the CSV data into a Neo4j knowledge graph with proper structure, constraints, and relationships.

**Architecture:**

1. **`read_config(file_path="config.txt") → dict`**

   - Reads Neo4j connection details from `config.txt`
   - Returns: `{"URI": "...", "USERNAME": "...", "PASSWORD": "..."}`

2. **`create_constraints(tx) → None`**

   - Establishes uniqueness constraints on critical node properties
   - Prevents duplicate nodes and ensures referential integrity

   **Constraints created:**

   ```cypher
   CREATE CONSTRAINT FOR (s:Season) REQUIRE s.season_name IS UNIQUE
   CREATE CONSTRAINT FOR (g:Gameweek) REQUIRE (g.season, g.GW_number) IS UNIQUE
   CREATE CONSTRAINT FOR (f:Fixture) REQUIRE (f.season, f.fixture_number) IS UNIQUE
   CREATE CONSTRAINT FOR (t:Team) REQUIRE t.name IS UNIQUE
   CREATE CONSTRAINT FOR (p:Player) REQUIRE (p.player_name, p.player_element) IS UNIQUE
   CREATE CONSTRAINT FOR (pos:Position) REQUIRE pos.name IS UNIQUE
   ```

3. **`create_data(tx, row) → None`**

   - Processes a single CSV row
   - Creates/merges nodes: Season, Gameweek, Fixture, Team (home & away), Player, Position
   - Creates relationships with properties:
     - `(Season) -[:HAS_GW]-> (Gameweek)`
     - `(Gameweek) -[:HAS_FIXTURE]-> (Fixture)`
     - `(Fixture) -[:HAS_HOME_TEAM]-> (Team)`
     - `(Fixture) -[:HAS_AWAY_TEAM]-> (Team)`
     - `(Player) -[:PLAYS_AS]-> (Position)`
     - `(Player) -[PLAYED_IN]-> (Fixture)` — **with 21 performance properties**

   **PLAYED_IN Relationship Properties:**

   ```
   minutes (int)
   goals_scored (int)
   assists (int)
   total_points (int)
   bonus (int)
   clean_sheets (int)
   goals_conceded (int)
   own_goals (int)
   penalties_saved (int)
   penalties_missed (int)
   yellow_cards (int)
   red_cards (int)
   saves (int)
   bps (int)
   influence (float)
   creativity (float)
   threat (float)
   ict_index (float)
   form (float)
   ```

4. **`main() → None`**
   - Entry point
   - Loads CSV file
   - Connects to Neo4j
   - Creates constraints and populates graph row-by-row
   - Prints progress updates

**Graph Structure Created:**

```
Season (e.g., "2021-22")
  ├─ HAS_GW → Gameweek 1
  │  └─ HAS_FIXTURE → Fixture 1
  │     ├─ HAS_HOME_TEAM → Team (e.g., Arsenal)
  │     └─ HAS_AWAY_TEAM → Team (e.g., Chelsea)
  │        └─ PLAYED_IN ← Player (Salah)
  ├─ HAS_GW → Gameweek 2
  │  └─ ...
  ...
```

**Usage:**

```bash
# Ensure config.txt has correct Neo4j credentials
python scripts/create_kg.py

# Output:
# Loading CSV data...
# Creating Constraints...
# Building Knowledge Graph (this may take some time)...
# Processing row 0...
# Processing row 100...
# ...
# Knowledge Graph created successfully.
```

**Performance:**

- ~5-15 minutes for full dataset on typical hardware
- Uses MERGE for idempotency (safe to run multiple times)

**Notes:**

- Fills NaN values with 0 before processing
- Property types are explicitly cast (integers vs floats)
- Supports incremental updates (running again adds missing data)

---

### **generate_embeddings.py** — Semantic Embedding & FAISS Index Generation

Converts player performance records into semantic embeddings using two sentence-transformer models, then creates FAISS indexes for fast similarity search.

**Architecture:**

1. **Configuration**

   ```python
   MODEL_A_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, 22M params, dim=384
   MODEL_B_NAME = "sentence-transformers/all-mpnet-base-v2"  # High-quality, 109M params, dim=768
   ```

2. **`fetch_rows(tx) → list[dict]`**

   - Complex Cypher query fetching all player-fixture performance records
   - Returns flattened records with:
     - Player info (name, element, position)
     - Fixture context (gameweek, season, teams)
     - All 21 performance metrics

3. **`build_text_description(row) → str`**

   - Converts numeric row into human-readable text
   - Example output:
     ```
     Player: Mohamed Salah | Position: MID | Season: 2022-23 | Gameweek: 10 |
     total_points: 15 | goals_scored: 1 | assists: 0 | minutes: 90 | bonus: 2 |
     clean_sheets: 0 | ict_index: 45.3 | Fixture: Arsenal vs Chelsea
     ```
   - Handles None/NaN values gracefully

4. **Embedding Generation**

   ```python
   # Encode all records with both models
   emb_a = model_a.encode(texts, convert_to_numpy=True)  # shape: (N, 384)
   emb_b = model_b.encode(texts, convert_to_numpy=True)  # shape: (N, 768)

   # Normalize for cosine similarity
   emb_a_norm = emb_a / ||emb_a||
   emb_b_norm = emb_b / ||emb_b||
   ```

5. **FAISS Index Creation**

   ```python
   index_a = faiss.IndexFlatIP(384)      # Inner product on normalized vectors
   index_b = faiss.IndexFlatIP(768)      # = Cosine similarity
   index_a.add(emb_a_norm.astype('float32'))
   index_b.add(emb_b_norm.astype('float32'))
   ```

6. **Persistence**

   - Saves FAISS indexes to disk:

     - `embeddings_out/faiss_index_modelA.index`
     - `embeddings_out/faiss_index_modelB.index`

   - Creates Neo4j Embedding nodes linked to Player nodes
   - Saves index→embedding_id mappings:
     - `embeddings_out/idx_to_embedding_id_modelA.json`
     - `embeddings_out/idx_to_embedding_id_modelB.json`

**Workflow:**

```
fpl_two_seasons.csv
      ↓ (create_kg.py)
Neo4j Knowledge Graph
      ↓ (generate_embeddings.py)
   ┌─────────────────────────────────┐
   │  fetch_rows()                   │
   │  (Cypher query)                 │
   └────────────┬────────────────────┘
                ↓
        [player_id, text, stats...]
                ↓
   ┌────────────────────────────────────┐
   │ SentenceTransformer encode         │
   │ ├─ Model A: 384-dim vectors        │
   │ └─ Model B: 768-dim vectors        │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────┐
   │ FAISS Index (fast search)  │
   ├─ faiss_index_modelA.index  │
   ├─ faiss_index_modelB.index  │
   └────────────────────────────┘
```

**Usage:**

```bash
python scripts/generate_embeddings.py

# Output:
# Fetched 22800 rows from Neo4j.
# Encoding with model A: sentence-transformers/all-MiniLM-L6-v2
# Batches: 100%|████████| 178/178 [00:45<00:00, 3.95it/s]
# Encoding with model B: sentence-transformers/all-mpnet-base-v2
# Batches: 100%|████████| 178/178 [02:15<00:00, 1.55it/s]
# Model A dim: 384 Model B dim: 768
# Saved FAISS indexes to disk.
# Saved mapping files to disk.
```

**Performance:**

- ~4 hours on CPU (45 min for Model A, 2h 15min for Model B)
- ~30 minutes on GPU with CUDA
- Outputs: 4 files (~850MB total)

**Key Characteristics:**

- **Model A (MiniLM):** Fast, small, ~85% quality of larger models
- **Model B (MPNet):** Slower but higher quality for semantic matching
- **Normalized embeddings:** Enables cosine similarity via inner product

---

### **config.txt** — Neo4j Connection Configuration

Simple key-value configuration file for database connectivity.

**Format:**

```plaintext
URI=neo4j://127.0.0.1:7687
USERNAME=neo4j
PASSWORD=<your_password>
```

**Fields:**

- **URI** — Neo4j connection string
  - `neo4j://` — Bolt protocol (recommended)
  - `neo4j+s://` — Bolt with TLS (for remote)
- **USERNAME** — Database user (default: `neo4j`)
- **PASSWORD** — Database password (set during Neo4j installation)

**Usage:**

- Read by `create_kg.py` before connecting to Neo4j
- Not used by `generate_embeddings.py` (hardcoded credentials in that file)

**Security Note:**

- **DO NOT commit passwords to version control**
- Use `.env` files or environment variables in production

---

### **schema.md** — Data Schema Documentation

Reference document describing the Neo4j knowledge graph structure and CSV input schema.

**Contents:**

1. **Neo4j Schema**

   - Node types (Season, Gameweek, Fixture, Team, Player, Position)
   - Relationships and their directions
   - Properties on edges

2. **CSV Schema**
   - Column definitions
   - Data types
   - Useful numerical features for analysis

**Purpose:**

- Quick reference during development
- Helps with query writing and validation
- Documents data transformations from CSV → Knowledge Graph

---

## 🚀 Setup Workflow

### Step 1: Prepare Neo4j

```bash
# Start Neo4j Desktop
# Create a new database (or use default)
# Note the URI, username, password
```

### Step 2: Update config.txt

```plaintext
URI=neo4j://127.0.0.1:7687
USERNAME=neo4j
PASSWORD=your_password_here
```

### Step 3: Populate Knowledge Graph

```bash
python scripts/create_kg.py
# Wait 5-15 minutes...
# "Knowledge Graph created successfully."
```

### Step 4: Generate Embeddings (Optional: Download Pre-computed Instead)

**Option A: Download Pre-computed (Fast, ~1 minute)**

```bash
# Download from Google Drive link in main README
# Place files in embeddings_out/
#   ├── faiss_index_modelA.index
#   ├── faiss_index_modelB.index
#   ├── idx_to_embedding_id_modelA.json
#   └── idx_to_embedding_id_modelB.json
```

**Option B: Generate from Scratch (Slow, ~4 hours)**

```bash
python scripts/generate_embeddings.py
# Wait for encoding...
# "Saved FAISS indexes to disk."
```

### Step 5: Verify Setup

```bash
# Test Neo4j connection
python -c "from modules.db_manager import neo4j_graph; print('Connected!')"

# Check embeddings
ls -la embeddings_out/
# Should see 4 files
```

---

## 📊 Data Flow Diagram

```
fpl_two_seasons.csv
       ↓
   (1,225 rows)
       ↓
  create_kg.py
       ↓
  ┌─────────────────────────────┐
  │  Neo4j Knowledge Graph      │
  ├─────────────────────────────┤
  │  Nodes:                     │
  │  • 2 Seasons                │
  │  • 76 Gameweeks             │
  │  • 760 Fixtures             │
  │  • 20 Teams                 │
  │  • ~600 Players             │
  │  • 4 Positions              │
  │                             │
  │  Relationships:             │
  │  • 22,800 PLAYED_IN records │
  │    with 21 properties each  │
  └─────────────────────────────┘
       ↓
 generate_embeddings.py
       ↓
  ┌──────────────────────────────────────┐
  │  Semantic Embeddings + FAISS Indexes │
  ├──────────────────────────────────────┤
  │  Model A (MiniLM):                   │
  │  • 22,800 embeddings × 384-dim       │
  │  • faiss_index_modelA.index          │
  │  • idx_to_embedding_id_modelA.json   │
  │                                      │
  │  Model B (MPNet):                    │
  │  • 22,800 embeddings × 768-dim       │
  │  • faiss_index_modelB.index          │
  │  • idx_to_embedding_id_modelB.json   │
  └──────────────────────────────────────┘
       ↓
Used by vector_retriever.py for semantic search
```

---

## ⚙️ Configuration & Customization

### Change Embedding Models

Edit `generate_embeddings.py`:

```python
MODEL_A_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # Your choice
MODEL_B_NAME = "sentence-transformers/paraphrase-MiniLM-L6-v2"  # Alternative
```

### Change Neo4j Connection

Update `config.txt` or edit hardcoded values in scripts:

```python
NEO4J_URI = "neo4j+s://your-remote-server.com:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
```

### Skip Certain Players/Seasons

Modify CSV before running `create_kg.py`:

```python
# In create_kg.py, after loading CSV:
df = df[df['season'] == '2022-23']  # Only 2022-23
df = df[~df['name'].str.contains('Salah', na=False)]  # Exclude Salah
```

---

## 🔍 Troubleshooting

### Issue: "Connection refused" when creating KG

**Cause:** Neo4j not running or wrong URI/credentials

**Solution:**

1. Start Neo4j Desktop
2. Verify `config.txt` has correct URI, username, password
3. Test: `neo4j-shell` or use Neo4j Browser

### Issue: "UNIQUE constraint violation"

**Cause:** Script ran multiple times without clearing database

**Solution:**

```cypher
MATCH (n) DETACH DELETE n  # Clear all nodes (careful!)
```

Then re-run `create_kg.py`

### Issue: Embedding generation hangs

**Cause:** Out of memory or very slow CPU

**Solution:**

- Use pre-computed embeddings (Option A in Step 4)
- Run on GPU if available
- Reduce batch size in `generate_embeddings.py`

### Issue: "FileNotFoundError: fpl_two_seasons.csv"

**Cause:** Running script from wrong directory

**Solution:**

```bash
cd /path/to/project
python scripts/create_kg.py
```

---

## 📝 Notes

- **CSV Format:** Ensure CSV is UTF-8 encoded; watch for special characters in player names
- **Neo4j Version:** Compatible with Neo4j 4.4+
- **Dependencies:** Requires pandas, neo4j-driver, sentence-transformers, faiss-cpu/faiss-gpu
- **Idempotency:** Both scripts use MERGE, so re-running is safe (won't create duplicates)
- **Scalability:** For larger datasets, consider batch processing or Neo4j APOC procedures

---

**Last Updated:** December 2025  
**Status:** Active  
**Related:** See [main README](../README.md) for full system documentation
