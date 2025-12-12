import json
from pathlib import Path

RESULTS_PATH = Path(__file__).parent / "results.json"


def update_costs():
    # DeepSeek prices (per token)
    price_in = 0.14 / 1_000_000
    price_out = 0.28 / 1_000_000

    # HF inference provider cost for CPU models (Gemma, Llama small)
    CPU_PRICE_PER_SEC = 0.00012  # $0.00012 per second

    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:

        llm = entry.get("llm")
        rt = entry.get("response_time_sec", 0) or 0

        # -------------------------------
        # DeepSeek cost (token-based)
        # -------------------------------
        if llm == "DeepSeek":
            input_tokens = entry.get("input_tokens", 0) or 0
            output_tokens = entry.get("output_tokens", 0) or 0
            try:
                cost = input_tokens * price_in + output_tokens * price_out
            except Exception:
                cost = 0
            entry["cost"] = float(f"{cost:.6f}")
            continue

        # -------------------------------
        # Gemma & Llama cost (compute-time-based)
        # -------------------------------
        if llm in ("Gemma", "Llama"):
            try:
                cost = rt * CPU_PRICE_PER_SEC
            except Exception:
                cost = 0
            entry["cost"] = float(f"{cost:.6f}")
            continue

        # Default fallback
        entry["cost"] = 0.0

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    update_costs()
