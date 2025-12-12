# experiments/run_experiments.py

import json
import time
import itertools
from pathlib import Path

# Import the same internal functions main.py uses
from config.settings import MODEL_OPTIONS, EMBEDDING_MODEL_OPTIONS
from config.template_library import CYPHER_TEMPLATE_LIBRARY, local_intent_classify
from modules.preprocessing import extract_entities
from modules.cypher_retriever import retrieve_data_via_cypher
from modules.vector_retriever import vector_search
from modules.llm_helper import classify_with_deepseek, create_query_with_deepseek
from modules.tests_llm_engine import (
    deepseek_generate_answer,
    llama_generate_answer,
    gemma_generate_answer,
)
from modules.db_manager import neo4j_graph


TESTS_PATH = Path("experiments/tests.json")
RESULTS_PATH = Path("experiments/results.json")


# ------------------------------
# Helper: call LLM + record tokens & cost
# ------------------------------
def call_llm(model_key, query, context):
    """
    Wraps all model calls and forces each response to return:
    {
        "answer": "...",
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int,
        "cost": float
    }

    This requires your llm_engine.py to return token metadata.
    If not, you must update it to return this format.
    """

    if model_key == "A":
        return deepseek_generate_answer(query, context)
    elif model_key == "B":
        return llama_generate_answer(query, context)
    else:
        return gemma_generate_answer(query, context)


# ------------------------------
# Retrieval selector
# ------------------------------
def run_retrieval(mode, intents, entities, k, embedding_model=None):
    if mode == "Baseline (Cypher)":
        results = []
        for intent in intents:
            res = retrieve_data_via_cypher(intent, entities, limit=k)
            results.append(res)
        return results

    elif mode == "Embeddings (Vector)":
        return vector_search(entities, top_k=k, model_choice=embedding_model)

    elif mode == "Hybrid":
        cypher_results = [
            retrieve_data_via_cypher(intent, entities, limit=k) for intent in intents
        ]
        vector_results = vector_search(entities, top_k=k, model_choice=embedding_model)
        return {"cypher": cypher_results, "vector": vector_results}

    elif mode == "LLM-generated Cypher":
        cypher_query = create_query_with_deepseek(query)
        results = neo4j_graph.execute_query(cypher_query)
        return {"cypher_query": cypher_query, "results": results}

    else:
        raise ValueError("Unknown retrieval mode")


# ------------------------------
# Experiment Runner
# ------------------------------
def run_all():
    with open(TESTS_PATH, "r") as f:
        test_prompts = json.load(f)

    llm_keys = list(MODEL_OPTIONS.keys())
    retrieval_modes = [
        "Baseline (Cypher)",
        "Embeddings (Vector)",
        "Hybrid",
        "LLM-generated Cypher",
    ]
    embedding_keys = list(EMBEDDING_MODEL_OPTIONS.keys())

    results = []

    # For progress output
    total_runs = 0

    for prompt in test_prompts:
        print(f"\n=== Running prompt: {prompt} ===")

        # Intent detection (same as in main.py)
        try:
            intents = classify_with_deepseek(
                prompt, list(CYPHER_TEMPLATE_LIBRARY.keys())
            )
        except:
            intents = local_intent_classify(prompt)

        if isinstance(intents, str):
            intents = [x.strip() for x in intents.split(",") if x.strip()]
        intents = intents[:3]

        entities = extract_entities(prompt)

        for llm_key in llm_keys:
            for mode in retrieval_modes:

                # Modes requiring embedding model
                if mode in ["Embeddings (Vector)", "Hybrid"]:
                    embedding_list = embedding_keys
                else:
                    embedding_list = [None]

                for embedding_key in embedding_list:
                    total_runs += 1
                    print(f" → LLM={llm_key}, Mode={mode}, Embedding={embedding_key}")

                    # ------------------------------
                    # Retrieval
                    # ------------------------------
                    start_t = time.time()
                    try:
                        context = run_retrieval(
                            mode,
                            intents,
                            entities,
                            k=5,
                            embedding_model=(
                                EMBEDDING_MODEL_OPTIONS[embedding_key]
                                if embedding_key
                                else None
                            ),
                        )
                    except Exception as e:
                        context = {"error": str(e)}

                    retrieval_time = time.time() - start_t

                    # ------------------------------
                    # LLM call
                    # ------------------------------
                    try:
                        llm_result = call_llm(llm_key, prompt, context)
                    except Exception as e:
                        llm_result = {
                            "answer": f"LLM error: {e}",
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "total_tokens": 0,
                            "cost": 0,
                        }

                    # ------------------------------
                    # Log result
                    # ------------------------------
                    results.append(
                        {
                            "prompt": prompt,
                            "llm": llm_key,
                            "retrieval_mode": mode,
                            "embedding_model": (
                                embedding_key if embedding_key else None
                            ),
                            "retrieval_time_sec": retrieval_time,
                            "response_time_sec": llm_result.get("time_sec"),
                            "answer": llm_result.get("answer"),
                            "input_tokens": llm_result.get("input_tokens"),
                            "output_tokens": llm_result.get("output_tokens"),
                            "total_tokens": llm_result.get("total_tokens"),
                            "cost": llm_result.get("cost"),
                        }
                    )

    # ------------------------------
    # Save results
    # ------------------------------
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=4)

    print("\n\n=== Experiments complete ===")
    print(f"Total runs: {total_runs}")
    print(f"Results saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    run_all()
