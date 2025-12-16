# Experiments & Evaluation Framework

The `experiments/` directory contains a comprehensive evaluation suite for benchmarking the FPL Graph-RAG system across multiple dimensions: **retrieval strategies**, **LLM models**, **embedding models**, and **real-world query scenarios**.

---

## 📊 Overview

**Purpose:** Measure system performance, accuracy, latency, and cost across all permutations of model choices and retrieval strategies.

**Scale:**

- **30 test prompts** across 7 query categories
- **18 permutations per prompt** (3 LLM × 4 retrieval modes × embedding models)
- **540 total experiments** producing detailed metrics

**Output:** Detailed results JSON + automated visualizations (bar charts, summaries)

---

## 📁 File Structure

### **run_experiments.py** — Main Experiment Orchestrator

Executes all 540 trials sequentially, collecting performance metrics for each combination.

**Key Functions:**

- **`call_llm(model_key, query, context) → dict`**

  - Wraps LLM calls (DeepSeek, Llama, Gemma)
  - Returns: answer, input_tokens, output_tokens, total_tokens, cost

- **`run_retrieval(mode, intents, entities, k, embedding_model) → dict`**

  - Routes to correct retrieval strategy:
    - `"Baseline (Cypher)"` — Deterministic Cypher templates
    - `"Embeddings (Vector)"` — FAISS semantic search
    - `"Hybrid"` — Combined Cypher + Vector results
    - `"LLM-generated Cypher"` — DeepSeek generates Cypher dynamically

- **`run_all() → None`**
  - Main entry point
  - Iterates through all test prompts and permutations
  - Records: latency, tokens, cost, accuracy, LLM output
  - Writes results to `results.json`

**Experiment Loop:**

```python
for prompt in test_prompts:
    for llm_model in ["DeepSeek", "Llama", "Gemma"]:
        for retrieval_mode in ["Baseline", "Embeddings", "Hybrid", "LLM-Cypher"]:
            for embedding_model in ["all-MiniLM-L6-v2", "all-mpnet-base-v2"]:
                # Execute trial & record metrics
```

**Usage:**

```bash
python -m experiments.run_experiments
# Writes 540 trial results to experiments/results.json
```

---

### **tests.json** — Ground Truth Test Prompts

Array of **30 diverse test questions** covering the full scope of FPL queries.

**Categories:**

1. **Player Performance (5 queries)**

   - Single player stats, career aggregates, points per minute

2. **Player Comparisons (5 queries)**

   - Head-to-head: total points, assists, goals, averages

3. **Rankings & Top Performers (5 queries)**

   - Top 5 by position, by stat, by form
   - Example: "Who are the top 5 players by total points?"

4. **Opponent Analysis (3 queries)**

   - Performance against specific teams, best/worst matchups
   - Example: "Against which teams has Dominic Calvert-Lewin scored the fewest points?"

5. **Goalkeeper-Specific (3 queries)**

   - Clean sheets, saves, consistency

6. **Team-Level Analysis (3 queries)**

   - Position distribution, average stats by position

7. **Miscellaneous (1 query)**
   - Edge cases, complex aggregations

**Example Prompts:**

```json
[
  "What are the total points for Mohamed Salah in gameweek 10 of the 2022 season?",
  "Compare Erling Haaland and Harry Kane by total points.",
  "Who are the top 5 players by total points?",
  "Against which teams has Dominic Calvert-Lewin scored the fewest points?"
]
```

---

### **validate_tests.json** — Ground Truth Answers

Manual gold-standard answers for each test prompt, used to compute accuracy metrics.

**Structure:**

```json
{
  "What are the total points for Mohamed Salah in gameweek 10 of the 2022 season?": 2,
  "Compare Erling Haaland and Harry Kane by total points.": "272 vs 455",
  "Who are the top 5 players by total points?": "Ollie Watkins, Erling Haaland, Mohamed Salah, Harry Kane, and Heung-Min Son",
  ...
}
```

**Accuracy Scoring:**

- LLM output is compared against ground truth
- Binary classification: `accurate=1` or `accurate=0`
- Aggregated across all experiments for average accuracy per LLM/retrieval mode

---

### **results.json** — Comprehensive Experiment Results

Large JSON array (**7,500+ lines**) containing detailed metrics for all 540 trials.

**Fields per Trial:**

| Field                | Type         | Description                                                          |
| -------------------- | ------------ | -------------------------------------------------------------------- |
| `prompt`             | string       | Test question                                                        |
| `llm`                | string       | "DeepSeek", "Llama", "Gemma"                                         |
| `retrieval_mode`     | string       | "Baseline (Cypher)", "Embeddings", "Hybrid", "LLM-generated Cypher"  |
| `embedding_model`    | string\|null | "all-MiniLM-L6-v2", "all-mpnet-base-v2" (null for Cypher-only modes) |
| `retrieval_time_sec` | float        | Time to fetch context (seconds)                                      |
| `response_time_sec`  | float        | Time for LLM to generate answer (seconds)                            |
| `answer`             | string       | LLM-generated response                                               |
| `input_tokens`       | float        | Tokens sent to LLM                                                   |
| `output_tokens`      | float        | Tokens generated by LLM                                              |
| `total_tokens`       | float        | Sum of input + output                                                |
| `accurate`           | int          | 1 if matches ground truth, 0 otherwise                               |
| `cost`               | float        | $ cost of trial                                                      |

**Example Entry:**

```json
{
  "prompt": "What are the total points for Mohamed Salah in gameweek 10 of the 2022 season?",
  "llm": "DeepSeek",
  "retrieval_mode": "Baseline (Cypher)",
  "embedding_model": null,
  "retrieval_time_sec": 0.009,
  "response_time_sec": 1.822,
  "answer": "Mohamed Salah scored 2 points in Gameweek 10 of the 2022-23 season.",
  "input_tokens": 269.1,
  "output_tokens": 33.8,
  "total_tokens": 302.9,
  "accurate": 1,
  "cost": 0.000047
}
```

---

### **viz.py** — Result Visualization & Analysis

Generates automated plots and summary statistics from `results.json`.

**Key Functions:**

- **`load_data() → DataFrame`**

  - Reads `results.json` into pandas DataFrame

- **`aggregate_by_llm(df) → DataFrame`**

  - Groups by LLM model
  - Computes mean: cost, accuracy, output_tokens, response_time

- **`aggregate_by_retrieval_mode(df) → DataFrame`**

  - Groups by retrieval strategy
  - Computes mean: accuracy, retrieval_time, input_tokens

- **`aggregate_by_embedding_model(df) → DataFrame`**

  - Groups by embedding model (filters for embedding-based retrievals)
  - Computes mean: accuracy, input_tokens, retrieval_time

- **`plot_bar(df, x, y, title, filename) → None`**

  - Generates bar charts comparing categories

- **`main() → None`**
  - Aggregates results by dimension
  - Saves `plots/summary.json` with aggregate metrics
  - Generates PNG visualizations for each metric

**Usage:**

```bash
python -m experiments.viz
# Outputs:
# - experiments/plots/summary.json (aggregate metrics)
# - experiments/plots/llm_*.png (LLM comparisons)
# - experiments/plots/retrieval_mode_*.png (retrieval strategy comparisons)
# - experiments/plots/embedding_model_*.png (embedding model comparisons)
```

**Generated Plots:**

| Plot                                     | Compares                   | Metrics                                  |
| ---------------------------------------- | -------------------------- | ---------------------------------------- |
| `llm_cost.png`                           | DeepSeek vs Llama vs Gemma | Average cost per trial                   |
| `llm_accurate.png`                       | LLM accuracy               | Accuracy on test set                     |
| `llm_response_time_sec.png`              | LLM latency                | Response time (seconds)                  |
| `llm_output_tokens.png`                  | Token output volume        | Tokens generated                         |
| `retrieval_mode_accurate.png`            | Retrieval strategies       | Accuracy: Cypher vs Embeddings vs Hybrid |
| `retrieval_mode_retrieval_time_sec.png`  | Retrieval latency          | Time to fetch context                    |
| `retrieval_mode_input_tokens.png`        | Token consumption          | Input tokens by strategy                 |
| `embedding_model_accurate.png`           | Embedding models           | Accuracy: MiniLM vs MPNet                |
| `embedding_model_retrieval_time_sec.png` | Embedding latency          | Semantic search speed                    |

---

### **cost_modify.py** — Cost Calculation & Normalization

Updates `results.json` with accurate pricing based on actual LLM API rates.

**Pricing Models:**

1. **DeepSeek (Token-Based)**

   - Input: $0.14 / 1M tokens
   - Output: $0.28 / 1M tokens
   - Cost = `(input_tokens × 0.14 + output_tokens × 0.28) / 1_000_000`

2. **Llama & Gemma (Compute-Time-Based)**
   - Hugging Face Inference API: $0.00012 / second
   - Cost = `response_time_sec × 0.00012`

**Usage:**

```bash
python -m experiments.cost_modify
# Recalculates all costs in results.json
```

---

### **plots/** — Generated Visualizations

Directory containing:

- **PNG charts** for each metric/comparison
- **summary.json** — Aggregate metrics in JSON format

**Example summary.json structure:**

```json
{
  "llm": [
    {
      "llm": "DeepSeek",
      "cost": 0.0000523,
      "accurate": 0.87,
      "output_tokens": 42.3,
      "response_time_sec": 1.95
    },
    ...
  ],
  "retrieval_mode": [
    {
      "retrieval_mode": "Baseline (Cypher)",
      "accurate": 0.92,
      "retrieval_time_sec": 0.008,
      "input_tokens": 250.5
    },
    ...
  ],
  "embedding_model": [
    {
      "embedding_model": "all-MiniLM-L6-v2",
      "accurate": 0.85,
      "input_tokens": 780.3,
      "retrieval_time_sec": 1.23
    },
    ...
  ]
}
```

---

## 🚀 Running Experiments

### Complete Evaluation (All 540 Trials)

```bash
# Execute experiments
python -m experiments.run_experiments

# Generate visualizations
python -m experiments.viz

# Update costs based on actual API rates
python -m experiments.cost_modify
```

**Expected runtime:** 2-6 hours (depending on LLM API latency)

---

## 📈 Key Metrics Explained

### **Accuracy (`accurate`)**

- Binary: 1 = matches ground truth, 0 = incorrect
- Computed by comparing LLM output to `validate_tests.json`
- Aggregated across all trials for average accuracy

### **Latency Metrics**

- **`retrieval_time_sec`** — Time to fetch context from Neo4j (Cypher/Vector)
- **`response_time_sec`** — Time for LLM to generate answer (API call duration)
- **Total time** = retrieval + response

### **Token Metrics**

- **`input_tokens`** — Tokens in the prompt sent to LLM (query + context + system prompt)
- **`output_tokens`** — Tokens generated by LLM
- **`total_tokens`** — Sum of input + output
- Used for cost calculation (token-based LLMs like DeepSeek)

### **Cost (`cost`)**

- Actual USD cost of running the trial
- DeepSeek: token-based ($0.14/$0.28 per million)
- Llama/Gemma: compute-time-based ($0.00012/sec on HF)

---

## 💡 Insights from Results

After running the full evaluation, you can answer questions like:

1. **Which LLM is best?**

   - Filter by LLM, compare accuracy + cost

2. **What's the fastest retrieval strategy?**

   - Compare retrieval_time_sec across modes

3. **Does vector search improve accuracy?**

   - Compare Baseline (Cypher) vs Embeddings vs Hybrid

4. **Which embedding model is better?**

   - Compare all-MiniLM vs all-MPNet (speed vs quality trade-off)

5. **Cost-performance trade-off?**
   - Plot cost vs accuracy for each LLM

---

## 🔧 Extending Experiments

### Add a New Test Prompt

1. Edit `tests.json`:

   ```json
   [
     ...existing prompts...,
     "Your new question here?"
   ]
   ```

2. Add ground truth answer to `validate_tests.json`:

   ```json
   {
     ...existing answers...,
     "Your new question here?": "Expected answer"
   }
   ```

3. Re-run experiments:
   ```bash
   python -m experiments.run_experiments
   ```

### Modify Pricing

Edit `cost_modify.py`:

```python
if llm == "DeepSeek":
    price_in = 0.20 / 1_000_000  # Updated rate
    price_out = 0.40 / 1_000_000
```

Then re-run cost calculation:

```bash
python -m experiments.cost_modify
```

---

## 📊 Analysis Tips

### Using the Results

```python
import json
import pandas as pd

# Load results
with open("experiments/results.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Question 1: Average accuracy by LLM
print(df.groupby("llm")["accurate"].mean())

# Question 2: Cheapest trial
print(df.nsmallest(1, "cost"))

# Question 3: Fastest retrieval mode
print(df.groupby("retrieval_mode")["retrieval_time_sec"].mean())

# Question 4: Cost per accuracy point
df["cost_per_accuracy"] = df["cost"] / (df["accurate"] + 0.01)
print(df.nsmallest(5, "cost_per_accuracy")[["llm", "retrieval_mode", "cost", "accurate"]])
```

---

## ⚠️ Notes

- **Large file:** `results.json` is ~7,500 lines; best analyzed with pandas/dataframe tools
- **Long runtime:** Full 540 trials can take 2-6 hours depending on API latency
- **API costs:** Actual costs accumulate; use `cost_modify.py` to track total spending
- **Accuracy assumes ground truth:** `validate_tests.json` must be manually curated for new queries
- **Plots are overwritten:** Running `viz.py` regenerates all PNG files (old ones deleted)

---

**Last Updated:** December 2025  
**Status:** Active Evaluation Framework  
**Related:** See [main README](../README.md#-experiments--evaluation) for system overview
