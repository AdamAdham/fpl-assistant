from modules.llm_engine import gemma_generate_answer, llama_generate_answer

user_query = "What is the capital of France?"
context_data = "France is a country in Europe. Its capital is Paris."


# Your existing code for context_data and user_query
try:
    answer_gemma = gemma_generate_answer(user_query, context_data)
except Exception as e:
    answer_gemma = f"Error generating answer with Gemma: {e}"

try:
    answer_llama = llama_generate_answer(user_query, context_data)
except Exception as e:
    answer_llama = f"Error generating answer with LLaMA2: {e}"

print("Answer from Gemma LLM:", answer_gemma)
print("Answer from LLaMA2 LLM:", answer_llama)
