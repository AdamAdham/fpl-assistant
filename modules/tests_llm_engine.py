# modules/tests_llm_engine.py

import os
import json
import time
from typing import Any, Dict
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

BASE_SYSTEM_PROMPT = """
You are an elite Fantasy Premier League (FPL) analyst. Your job is to answer
the user's question using ONLY the data provided in the context below.

Rules:
- Do NOT guess or hallucinate.
- If the context does not contain the answer, say so.
- Keep output concise, analytical, and actionable.
- At the end of every response, suggest one relevant suggested follow-up question the user might ask.

Now read the context carefully.
"""


# --------------------------------------------------------------------
# Small token estimator for HF models (router does NOT return tokens)
# --------------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()) * 1.3)  # rough approx


# --------------------------------------------------------------------
# DEEPSEEK
# --------------------------------------------------------------------
def deepseek_generate_answer(user_query: str, context_data: Dict[str, Any]) -> Dict:
    if user_query is None:
        raise ValueError("user_query must be provided")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not found in environment")

    endpoint = os.getenv("DEEPSEEK_API_URL")
    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    system_prompt = BASE_SYSTEM_PROMPT.strip()
    user_prompt = (
        f'User query: "{user_query}"\n\n'
        f"Context:\n{context_json}\n\n"
        "Answer using ONLY the provided context. If the context does not contain the answer, say so."
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.time()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return {
            "answer": f"DeepSeek request failed: {exc}",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0,
            "time_sec": time.time() - t0,
        }

    data = resp.json()
    try:
        answer = data["choices"][0]["message"]["content"].strip()
    except Exception:
        answer = resp.text.strip()

    # Token metadata from API (DeepSeek returns this!)
    usage = data.get("usage", {})
    input_toks = usage.get("prompt_tokens", 0)
    output_toks = usage.get("completion_tokens", 0)
    total_toks = usage.get("total_tokens", input_toks + output_toks)

    # DeepSeek price per 1M tokens (example – adjust per your plan)
    price_in = 0.14 / 1_000_000
    price_out = 0.28 / 1_000_000
    cost = input_toks * price_in + output_toks * price_out

    return {
        "answer": answer,
        "input_tokens": input_toks,
        "output_tokens": output_toks,
        "total_tokens": total_toks,
        "cost": float(f"{cost:.2e}"),
        "time_sec": time.time() - t0,
    }


# --------------------------------------------------------------------
# HuggingFace router (Llama / Gemma) – NO TOKEN DATA PROVIDED
# --------------------------------------------------------------------

HF_ENDPOINT = "https://router.huggingface.co/v1/chat/completions"


def _hf_chat_completion(model: str, system_prompt: str, user_prompt: str) -> Dict:
    api_key = os.getenv("HF_TOKEN")
    if not api_key:
        raise RuntimeError("HF_TOKEN not found in environment")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.time()
    try:
        resp = requests.post(HF_ENDPOINT, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        answer = data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return {
            "answer": f"HF request failed: {exc}",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0,
            "time_sec": time.time() - t0,
        }

    # HF router DOES NOT send token usage → estimate
    input_toks = estimate_tokens(system_prompt + user_prompt)
    output_toks = estimate_tokens(answer)
    total_toks = input_toks + output_toks

    return {
        "answer": answer,
        "input_tokens": input_toks,
        "output_tokens": output_toks,
        "total_tokens": total_toks,
        "cost": 0,  # free HF tier
        "time_sec": time.time() - t0,
    }


def gemma_generate_answer(user_query: str, context_data: Dict[str, Any]) -> Dict:
    if user_query is None:
        raise ValueError("user_query must be provided")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    user_prompt = (
        f'User query: "{user_query}"\n\n'
        f"Context:\n{context_json}\n\n"
        "Answer using ONLY this context. If context lacks the answer, say so."
    )

    return _hf_chat_completion(
        model="google/gemma-2-2b-it",
        system_prompt=BASE_SYSTEM_PROMPT.strip(),
        user_prompt=user_prompt,
    )


def llama_generate_answer(user_query: str, context_data: Dict[str, Any]) -> Dict:
    if user_query is None:
        raise ValueError("user_query must be provided")

    try:
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    except Exception:
        context_json = str(context_data)

    user_prompt = (
        f'User query: "{user_query}"\n\n'
        f"Context:\n{context_json}\n\n"
        "Answer using ONLY this context. If context lacks the answer, say so."
    )

    return _hf_chat_completion(
        model="meta-llama/Llama-3.2-1B-Instruct",
        system_prompt=BASE_SYSTEM_PROMPT.strip(),
        user_prompt=user_prompt,
    )
