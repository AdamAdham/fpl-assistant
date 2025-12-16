# Modules Directory

The `modules/` directory contains the core business logic of the FPL Graph-RAG system. These modules handle data preprocessing, retrieval, LLM integration, and visualization across the entire pipeline.

---

## 📁 Module Architecture

```
User Query (from Streamlit UI)
    ↓
┌──────────────────────────────────────────┐
│ 1. preprocessing.py                      │
│    ├─ Intent Classification              │
│    ├─ Entity Extraction (NER)            │
│    └─ Fuzzy Matching                     │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ 2. Retrieval Layer (Select One)          │
│    ├─ cypher_retriever.py                │
│    ├─ vector_retriever.py                │
│    └─ Hybrid combination                 │
└──────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────┐
│ 3. llm_engine.py / llm_helper.py               │
│    ├─ Generate Answer (DeepSeek/Llama/Gemma)   │
│    └─ Answer Grounding & Validation            │
└────────────────────────────────────────────────┘
    ↓
Natural Language Answer + Follow-up Question
```

---

## 📚 Module Descriptions

### **preprocessing.py** — Query Understanding & Entity Extraction

Converts raw user queries into structured entity-based representations for downstream retrieval.

**Key Functions:**

#### `extract_entities(user_query: str) → Dict[str, List]`

Extracts all relevant entities from user input using multi-strategy approach:

**Extraction Methods:**

1. **Gameweek Detection** — Regex matching for "GW10", "gameweek 5", "week 3"
2. **Position Detection** — Matches position variants (DEF, MID, FWD, GK)
3. **Season Detection** — Captures "2021-22", "2022-23", "this season"
4. **Statistic Detection** — Maps aliases to canonical stat names via `STAT_VARIANTS`
5. **Team Detection** — Uses spaCy ORG entities + fuzzy matching via `TEAM_ABBREV`
6. **Player Detection** — Fuzzy matching against Neo4j player list

**Returns:**

```python
{
    "players": ["Mohamed Salah", "Harry Kane"],
    "teams": ["Arsenal", "Liverpool"],
    "gameweeks": [10, 15],
    "positions": ["MID", "FWD"],
    "seasons": ["2022-23"],
    "statistics": ["goals_scored", "assists"]
}
```

**Technologies:**

- **spaCy NER** — Organization recognition (team names)
- **Fuzzy Matching** — Handles typos (thefuzz library)
- **Regex Patterns** — Gameweeks, seasons, positions
- **Database Lookups** — Validates against Neo4j player/team lists

**Example:**

```python
entities = extract_entities("Compare Salah and Haaland's goals in GW5 2022-23")
# Output:
# {
#   "players": ["Mohamed Salah", "Erling Haaland"],
#   "statistics": ["goals_scored"],
#   "gameweeks": [5],
#   "seasons": ["2022-23"]
# }
```

---

### **cypher_retriever.py** — Deterministic Graph Queries

Baseline retrieval strategy using templated Cypher queries for precise, rule-based data fetching.

**Key Functions:**

#### `retrieve_data_via_cypher(intent: str, entities: Dict, limit: int) → Dict`

**Process:**

1. **Intent → Template** — Selects Cypher template from `CYPHER_TEMPLATE_LIBRARY`
2. **Entities → Parameters** — Maps extracted entities to Cypher parameters
3. **Parameter Validation** — Checks that required parameters are present
4. **Query Execution** — Runs parameterized query against Neo4j
5. **Result Formatting** — Returns JSON-friendly results + visualization data

**Output Structure:**

```python
{
    "status": "success" | "error",
    "results": [...],  # Query results
    "reasoning": "...",  # Why this template was chosen
    "graph_nodes": [...],  # For vis.js visualization
    "graph_edges": [...]   # For vis.js visualization
}
```

**Intent Examples:**

- `PLAYER_STATS_GW_SEASON` — Player stats in specific gameweek
- `COMPARE_PLAYERS_BY_TOTAL_POINTS` — Head-to-head comparison
- `TOP_PLAYERS_BY_POSITION` — Ranked lists
- `PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS` — Opponent analysis

**Pros:**

- ✅ Deterministic & predictable
- ✅ Fast execution
- ✅ Safe parameter injection
- ✅ Works when entities are exactly matched

**Cons:**

- ❌ Fails on unmatched entity names (typos, variations)
- ❌ Limited to predefined templates
- ❌ No semantic understanding of similar queries

**Graph Visualization:**

- Returns node/edge data for interactive vis.js graphs
- Used in Streamlit sidebar for context visualization

---

### **vector_retriever.py** — Semantic Embedding-Based Retrieval

Alternative retrieval strategy using semantic similarity for fuzzy, exploratory queries.

**Key Functions:**

#### `get_models_and_indexes() → Tuple`

Cached loader for embedding models and FAISS indexes:

```python
model_A, model_B, index_A, index_B, mapping_A, mapping_B = get_models_and_indexes()
```

**Caching:** Uses Streamlit's `@st.cache_resource` for efficient memory usage

#### `vector_search(entities: Dict, top_k: int, model_choice: str) → Dict`

**Process:**

1. **Entity → Query Text** — Builds descriptive text from entities

   ```
   "Players: Salah | Teams: Liverpool | Statistics: goals_scored | Season: 2022-23"
   ```

2. **Text → Embedding** — Encodes query using SentenceTransformer

   - Model A (MiniLM): 384-dim, fast
   - Model B (MPNet): 768-dim, high-quality

3. **FAISS Search** — Finds top-k most similar embeddings

   ```
   D, I = index.search(query_embedding, k=5)
   ```

4. **Neo4j Lookup** — Fetches source nodes for returned embeddings
5. **Result Aggregation** — Returns ranked results by similarity score

**Output:**

```python
{
    "results": [
        {"node": {...}, "similarity_score": 0.92},
        {"node": {...}, "similarity_score": 0.87},
        ...
    ],
    "retrieval_time_sec": 1.23,
    "model_used": "all-MiniLM-L6-v2"
}
```

**Models:**

- **Model A**: `sentence-transformers/all-MiniLM-L6-v2` (fast, small)
- **Model B**: `sentence-transformers/all-mpnet-base-v2` (high-quality)

**Pros:**

- ✅ Robust to phrasing variations
- ✅ Discovers semantically similar items
- ✅ Works with partial/fuzzy matches
- ✅ No strict entity matching required

**Cons:**

- ❌ Slower than Cypher
- ❌ Less precise for factual queries
- ❌ Requires pre-computed embeddings

---

### **db_manager.py** — Neo4j Connection Management

Singleton pattern for safe, pooled database access throughout the application.

**Key Classes:**

#### `Neo4jGraph` (Singleton)

Manages a single persistent Neo4j driver instance.

**Key Methods:**

- **`__new__()` → Neo4jGraph**

  - Initializes driver on first instantiation
  - Subsequent calls return same instance
  - Reads credentials from `.env`

- **`execute_query(query: str, params: dict) → List[Dict]`**

  - Executes Cypher query with safe parameter injection
  - Returns list of result rows
  - Handles errors gracefully with detailed logging

- **`execute_query_with_graph(query: str, params: dict) → Tuple`**
  - Returns both raw results AND graph visualization data
  - Extracts nodes/relationships for vis.js rendering

**Usage:**

```python
from modules.db_manager import Neo4jGraph

db = Neo4jGraph()  # Singleton instance
results = db.execute_query(
    "MATCH (p:Player) WHERE p.player_name = $name RETURN p",
    {"name": "Mohamed Salah"}
)
```

**Features:**

- ✅ Connection pooling (max 20 connections)
- ✅ Parameter binding (safe from Cypher injection)
- ✅ Error logging with query context
- ✅ Automatic driver lifecycle management

**Configuration:**

- Reads from `.env`: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`

---

### **llm_engine.py** — Multi-Model LLM Answer Generation

Interfaces with multiple LLM providers to generate grounded, factual answers.

**Key Functions:**

#### `deepseek_generate_answer(user_query: str, context_data: Dict) → str`

Calls DeepSeek API to synthesize answer from retrieved context.

**Process:**

1. Serializes context data to JSON
2. Combines with system prompt (emphasizes grounding in data)
3. Sends to DeepSeek API with temperature=0.0 (deterministic)
4. Extracts answer from response + estimates tokens & cost

**System Prompt:**

```
You are an elite Fantasy Premier League (FPL) analyst.
Answer ONLY using provided data.
If context doesn't contain answer, say so.
Suggest one relevant follow-up question at the end.
```

**Returns:**

```python
{
    "answer": "Mohamed Salah scored 15 goals in 2022-23...",
    "input_tokens": 269.1,
    "output_tokens": 33.8,
    "total_tokens": 302.9,
    "cost": 0.000047
}
```

#### `llama_generate_answer(user_query: str, context_data: Dict) → Dict`

Calls Hugging Face Inference API for Llama 2 (70B) model.

#### `gemma_generate_answer(user_query: str, context_data: Dict) → Dict`

Calls Hugging Face Inference API for Gemma model.

**Supported Models:**
| Model | Provider | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| DeepSeek | Deepseek API | ⚡ Fast | ⭐⭐⭐⭐ | 💰 |
| Llama 70B | HF Inference | 🐢 Slow | ⭐⭐⭐⭐⭐ | 💰💰 |
| Gemma 7B | HF Inference | ⚡ Fast | ⭐⭐⭐ | 💰 |

**Token Estimation:**

- DeepSeek: Exact token count from API response
- Llama/Gemma: Estimated using heuristics (words × 1.3)

**Configuration:**

- Reads from `.env`: API keys, endpoints, model names

---

### **llm_helper.py** — Intent Classification & Cypher Generation

High-level LLM utilities for understanding queries and generating dynamic Cypher.

**Key Functions:**

#### `classify_with_deepseek(query: str, options: List[str]) → List[str]`

Maps a user query to up to 3 most relevant Cypher templates using LLM.

**Process:**

1. Sends query + list of available intents to DeepSeek
2. LLM ranks intents by relevance
3. Returns top 3 template names

**Example:**

```python
intents = classify_with_deepseek(
    "Which defender has the most clean sheets?",
    ["PLAYER_CAREER_STATS_TOTALS", "TOP_PLAYERS_BY_POSITION", ...]
)
# Returns: ["TOP_PLAYERS_BY_POSITION", "PLAYER_CAREER_STATS_TOTALS", ...]
```

#### `create_query_with_deepseek(query: str, schema: str) → str`

Generates a Cypher query from user prompt using LLM.

**Process:**

1. Provides KG schema to DeepSeek
2. Asks it to generate single Cypher query
3. Returns raw Cypher (cleaned of markdown)

**System Prompt:**

```
You are an expert Cypher query generator for FPL knowledge graph.
Given schema, generate single Cypher query answering user's prompt.
Return ONLY the query, no explanation.
```

**Example:**

```python
cypher = create_query_with_deepseek(
    "How many goals did Salah score in 2022-23?"
)
# Returns: "MATCH (p:Player {player_name: 'Mohamed Salah'}) ... RETURN sum(r.goals_scored)"
```

**Fallback:**

- If LLM fails, uses `local_intent_classify()` from `config/template_library.py`
- Rule-based keyword matching as backup

---

### **graph_visualizer.py** — Interactive Graph Rendering

Converts Neo4j query results into vis.js-compatible format for interactive visualization.

**Key Functions:**

#### `neo4j_to_visjs_graph(nodes: List, relationships: List) → Dict`

Converts Neo4j nodes/relationships to vis.js nodes/edges.

**Node Styling:**

- Color-coded by type (Player, Team, Fixture, etc.)
- Size varies by properties
- Label extracted from name properties

**Edge Styling:**

- Color-coded by relationship type (PLAYED_IN, PLAYS_AS, etc.)
- Arrows indicate direction
- Labels show relationship types

**Output Structure:**

```python
{
    "nodes": [
        {"id": 123, "label": "Mohamed Salah", "color": "#3498db", "type": "Player"},
        {"id": 456, "label": "Arsenal", "color": "#e74c3c", "type": "Team"},
        ...
    ],
    "edges": [
        {"from": 123, "to": 456, "label": "PLAYED_FOR", "color": "#7f8c8d"},
        ...
    ]
}
```

**Color Scheme:**

```python
{
    "Player": "#3498db",      # Blue
    "Team": "#e74c3c",        # Red
    "Fixture": "#f39c12",     # Orange
    "Gameweek": "#9b59b6",    # Purple
    "Position": "#1abc9c",    # Teal
    "Season": "#34495e"       # Dark gray
}
```

**Usage in Streamlit:**

```python
graph_data = neo4j_to_visjs_graph(nodes, relationships)
st.write(graph_html(graph_data))  # Renders interactive vis.js graph
```

---

### **tests_llm_engine.py** — Evaluation-Focused LLM Wrapper

Modified version of `llm_engine.py` designed for performance testing and evaluation.

**Differences from llm_engine.py:**

- Returns additional metadata: tokens, timing, cost
- Compatible with experiment framework
- Standardized output format for benchmarking

**Key Functions:**

#### `deepseek_generate_answer(user_query: str, context_data: Dict) → Dict`

Enhanced DeepSeek call with full metrics.

**Returns:**

```python
{
    "answer": "...",
    "input_tokens": 269.1,
    "output_tokens": 33.8,
    "total_tokens": 302.9,
    "cost": 0.000047
}
```

#### `llama_generate_answer(user_query: str, context_data: Dict) → Dict`

#### `gemma_generate_answer(user_query: str, context_data: Dict) → Dict`

**Used by:** `experiments/run_experiments.py` for benchmarking

---

### \***\*init**.py\*\* — Module Exports

Exposes core modules for easy import:

```python
from modules import (
    db_manager,
    preprocessing,
    cypher_retriever,
    vector_retriever,
    graph_visualizer
)
```

---

## 🔄 Data Flow Example

**Query:** "How many goals did Salah score against Chelsea in 2022-23?"

```
1. preprocessing.py
   ↓
   extract_entities() → {
       "players": ["Mohamed Salah"],
       "teams": ["Chelsea"],
       "seasons": ["2022-23"],
       "statistics": ["goals_scored"]
   }

2. cypher_retriever.py or vector_retriever.py
   ↓
   retrieve_data_via_cypher() → {
       "results": [{"opponent": "Chelsea", "goals": 2}],
       "graph_nodes": [...],
       "graph_edges": [...]
   }

3. llm_engine.py
   ↓
   deepseek_generate_answer() → {
       "answer": "Salah scored 2 goals against Chelsea...",
       "tokens": 302.9,
       "cost": 0.000047
   }

4. main.py (Streamlit UI)
   ↓
   Display answer + graph + follow-up question
```

---

## 🏗️ Design Patterns

### Singleton Pattern

- **Used in:** `db_manager.py`
- **Why:** Ensure single database connection shared across application
- **Benefit:** Resource efficiency, consistent connection pool

### Caching Pattern

- **Used in:** `vector_retriever.py` (Streamlit @cache_resource)
- **Why:** Embedding models are large; load once, reuse many times
- **Benefit:** Faster response times after initial load

### Dependency Injection

- **Used in:** All modules take `entities` dict as parameter
- **Why:** Decouples preprocessing from retrieval/LLM
- **Benefit:** Easy to swap retrievers or preprocessing methods

---

## 🚀 Usage Examples

### Basic Query Processing

```python
from modules.preprocessing import extract_entities
from modules.cypher_retriever import retrieve_data_via_cypher
from modules.llm_engine import deepseek_generate_answer

# Step 1: Extract entities
query = "Who are the top 5 forwards by total points?"
entities = extract_entities(query)

# Step 2: Retrieve data
intent = "TOP_PLAYERS_BY_POSITION"
context = retrieve_data_via_cypher(intent, entities, limit=5)

# Step 3: Generate answer
answer = deepseek_generate_answer(query, context["results"])
print(answer)
```

### Hybrid Retrieval

```python
from modules.cypher_retriever import retrieve_data_via_cypher
from modules.vector_retriever import vector_search

# Run both in parallel
cypher_results = retrieve_data_via_cypher(intent, entities)
vector_results = vector_search(entities, top_k=5, model_choice="A")

# Combine & deduplicate
combined = {**cypher_results, **vector_results}
```

---

## 📝 Configuration

All modules read from `.env`:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# LLM APIs
DEEPSEEK_API_KEY=...
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat

HF_TOKEN=...

# Embedding Models
MODEL_A_NAME=sentence-transformers/all-MiniLM-L6-v2
MODEL_B_NAME=sentence-transformers/all-mpnet-base-v2

# FAISS Indexes
FAISS_INDEX_A_PATH=./embeddings_out/faiss_index_modelA.index
FAISS_INDEX_B_PATH=./embeddings_out/faiss_index_modelB.index
MAPPING_A_PATH=./embeddings_out/idx_to_embedding_id_modelA.json
MAPPING_B_PATH=./embeddings_out/idx_to_embedding_id_modelB.json
```

---

## 🔧 Common Tasks

### Add Support for New Intent

1. Add template to `config/template_library.py`
2. Add parameters to `INTENT_PARAMETER_MAP`
3. Add fallback keywords to `local_intent_classify()`

### Change Default LLM

Edit `main.py`:

```python
st.session_state.llm_choice = "Llama"  # or "Gemma"
```

### Switch Embedding Model

Edit `main.py` sidebar:

```python
embedding_model = st.selectbox("Embedding Model",
    list(EMBEDDING_MODEL_OPTIONS.keys())
)
```

---

## ⚠️ Troubleshooting

### "Neo4j connection failed"

→ Check `.env` has valid credentials and Neo4j is running

### "FAISS index not found"

→ Run `scripts/generate_embeddings.py` or download pre-computed indexes

### "LLM API timeout"

→ Check internet connection and API key validity

### "spaCy model not found"

→ Run `python -m spacy download en_core_web_trf`

---

**Last Updated:** December 2025  
**Status:** Active Development  
**Related:** See [main README](../README.md) for system overview
