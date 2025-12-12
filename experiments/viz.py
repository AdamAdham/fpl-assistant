# viz.py
import json
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

RESULTS_PATH = Path(__file__).parent / "results.json"
PLOTS_DIR = Path(__file__).parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

def load_data():
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df

def aggregate_by_llm(df):
    metrics = ["cost", "accurate", "output_tokens", "response_time_sec"]
    agg_df = df.groupby("llm")[metrics].mean().reset_index()
    return agg_df

def aggregate_by_retrieval_mode(df):
    metrics = ["accurate", "retrieval_time_sec", "input_tokens"]
    agg_df = df.groupby("retrieval_mode")[metrics].mean().reset_index()
    return agg_df

def aggregate_by_embedding_model(df):
    metrics = ["accurate", "input_tokens", "retrieval_time_sec"]
    agg_df = df[df["embedding_model"].notnull()].groupby("embedding_model")[metrics].mean().reset_index()
    return agg_df

def plot_bar(df, x, y, title, filename):
    plt.figure(figsize=(10,6))
    sns.barplot(data=df, x=x, y=y)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def main():
    df = load_data()
    
    # Aggregate
    llm_agg = aggregate_by_llm(df)
    retrieval_agg = aggregate_by_retrieval_mode(df)
    embedding_agg = aggregate_by_embedding_model(df)
    
    # Save summaries to JSON
    summary = {
        "llm": llm_agg.to_dict(orient="records"),
        "retrieval_mode": retrieval_agg.to_dict(orient="records"),
        "embedding_model": embedding_agg.to_dict(orient="records")
    }
    with open(PLOTS_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    
    # Save plots
    for metric in ["cost", "accurate", "output_tokens", "response_time_sec"]:
        if metric in llm_agg.columns:
            plot_bar(
                llm_agg, "llm", metric,
                f"LLM comparison on {metric}",
                PLOTS_DIR / f"llm_{metric}.png"
            )
    
    for metric in ["accurate", "retrieval_time_sec", "input_tokens"]:
        if metric in retrieval_agg.columns:
            plot_bar(
                retrieval_agg, "retrieval_mode", metric,
                f"Retrieval Mode comparison on {metric}",
                PLOTS_DIR / f"retrieval_mode_{metric}.png"
            )
    
    for metric in ["accurate", "input_tokens", "retrieval_time_sec"]:
        if metric in embedding_agg.columns:
            plot_bar(
                embedding_agg, "embedding_model", metric,
                f"Embedding Model comparison on {metric}",
                PLOTS_DIR / f"embedding_model_{metric}.png"
            )

if __name__ == "__main__":
    main()
