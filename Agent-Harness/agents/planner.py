import os
from pathlib import Path
from openai import OpenAI
from agents.prompt import AGENT_PROMPT, SUMMARIZER_PROMPT, SKILL_READER_PROMPT
from dotenv import load_dotenv
import json
load_dotenv()
from agents.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, SPECIALIST_MAX_TOKENS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / "skills"


# class FakePlanner:
#     def decide(self, iteration_number, latest_observation=None):
#         if iteration_number == 1:
#             return {
#                 "tool_name": "list_files",
#                 "tool_input": {"directory": "."},
#             }

#         if iteration_number == 2:
#             return {
#                 "tool_name": "run_command",
#                 "tool_input": {"command": "python3 -m pytest"},
#             }

#         if iteration_number == 3:
#             return {
#                 "tool_name": "read_file",
#                 "tool_input": {"file_path": "tests/test_auth.py"},
#             }

#         if iteration_number == 4:
#             return {
#                 "tool_name": "read_file",
#                 "tool_input": {"file_path": "src/taskflow/auth.py"},
#             }

#         return {
#             "tool_name": "finish",
#             "tool_input": {
#                 "final_answer": "Auth tests expect usernames to be normalized by trimming and lowercasing before lookup."
#             },
#         }

class RealPlanner:
    def __init__(self):
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key is None:
            raise ValueError("DEEPSEEK_API_KEY is not set")

        self.client = OpenAI(
            api_key=deepseek_api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    def decide(self,iteration_number,user_question:str,latest_observation=None,recent_history=None):
        prompt = AGENT_PROMPT
        payload = {
            "iteration_number": iteration_number,
            "user_question": user_question,
            "latest_observation": latest_observation,
            "recent_history": recent_history or [],
        }
        if latest_observation is None:
            payload["latest_observation"] = "No observations yet."

        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.2,
            max_tokens=SPECIALIST_MAX_TOKENS,
            extra_body={
                "thinking": {"type": "disabled"}
            },
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)


class Summarizer:
    def __init__(self):
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key is None:
            raise ValueError("DEEPSEEK_API_KEY is not set")

        self.client = OpenAI(
            api_key=deepseek_api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    def summarize(self, payload):
        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SUMMARIZER_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.1,
            max_tokens=SPECIALIST_MAX_TOKENS,
            extra_body={
                "thinking": {"type": "disabled"}
            },
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)

class SkillSelector:
    def __init__(self):
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key is None:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        self.client = OpenAI(
            api_key=deepseek_api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    def read_skills_index(self):
        return (SKILLS_DIR / "README.md").read_text()

    def select_skill(self, user_question: str, skills_index_text: str):
        payload = {
            "user_question": user_question,
            "skills_readme_text": skills_index_text,
        }
        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SKILL_READER_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.1,
            max_tokens=SPECIALIST_MAX_TOKENS,
            extra_body={
                "thinking": {"type": "disabled"}
            },
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)

    def get_skill_description(self, skill_path: str):
        if skill_path is None:
            return None

        path = Path(skill_path)
        if skill_path.startswith("/") or ".." in path.parts:
            return None

        skill_file = SKILLS_DIR / path
        if not skill_file.exists():
            return None

        return skill_file.read_text()

