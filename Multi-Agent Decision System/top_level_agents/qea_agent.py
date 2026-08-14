import os
from openai import OpenAI
from dotenv import load_dotenv
from .prompts import *
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

# print("API key loaded:", api_key is not None)

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

# # Test models endpoint
# models = client.models.list()

# print("\n--- Available DeepSeek Models ---")
# for model in models.data:
#     print(model.id)

# user_question = input("Enter your question: ")
# print("\n--- User Question ---")
# print(user_question)

def enrich_question(user_question):
    prompt = QUESTION_ENRICHMENT_AGENT 
    response = client.chat.completions.create(
        model = "deepseek-v4-flash",
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_question}
        ],
        temperature = 0.7,
        max_tokens = 500,
        extra_body={
            "thinking": {"type": "disabled"}
        }
    )

    return response.choices[0].message.content.strip()

# enriched_question = enrich_question(user_question)
# enriched_question = json.loads(enriched_question)
# question_list = enriched_question["questions"]

# print("\n--- Question List ---")
# for i, question in enumerate(question_list):
#     print(f"{question}")

def ask_follow_up_questions(question_list):
    print("\n--- Follow-up Questions ---")
    print("\n--- Please be as detailed and clear as possible ---")
    enriched_context = []
    for question in question_list:
        print(f"{question}")
        user_answer = input("Your answer: ")
        enriched_context.append({
            "question": question,
            "answer": user_answer
        })
    return {"enriched_context": enriched_context}

# context = ask_follow_up_questions(question_list)
