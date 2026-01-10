import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

def get_client_from(provider: str = "cerebras"):
    if provider == "google":
        from google import genai
        return genai.Client(api_key=os.environ["GEMINI_API_KEY"]), "gemini-2.0-flash"
    elif provider == "cerebras":
        from langchain_cerebras import ChatCerebras
        return ChatCerebras(
            model="llama-3.3-70b",
            api_key=os.environ.get("CEREBRAS_API_KEY")
        ), "llama-3.3-70b"

class LLMClient:
    def __init__(self, provider="cerebras"):
        self.client, self.model = get_client_from(provider)
        self.provider = provider

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from model output.
        Handles:
        - raw JSON
        - ```json ... ```
        - ``` ... ```
        """
        text = text.strip()

        # If wrapped in ```json ``` or ``` ```
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()

        # Otherwise assume it's raw JSON
        return text

    def generate_json(self, system_prompt: str, user_prompt: str, retries: int = 3) -> dict:
        last_error = None

        for attempt in range(retries + 1):
            if self.provider == "google":
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=f"""
SYSTEM:
{system_prompt}

USER:
{user_prompt}

IMPORTANT:
- You must respond ONLY with valid JSON
- No markdown
- No ``` fences
- No commentary
- Output must be directly parsable by json.loads
"""
                )
                raw_text = response.text.strip()
                
            elif self.provider == "cerebras":
                # LangChain ChatCerebras uses messages format
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
{user_prompt}

IMPORTANT:
- You must respond ONLY with valid JSON
- No markdown
- No ``` fences
- No commentary
- Output must be directly parseable by json.loads
"""}
                ]
                response = self.client.invoke(messages)
                raw_text = response.content.strip()

            cleaned = self._extract_json(raw_text)

            try:
                return json.loads(cleaned)

            except json.JSONDecodeError as e:
                last_error = f"Attempt {attempt + 1}: {e}\nRaw:\n{raw_text}"

                # Strengthen instruction on retry
                user_prompt = f"""
Your previous response was INVALID JSON and could not be parsed.

Error:
{e}

You must now respond with ONLY valid JSON. No backticks. No markdown.

Original task:
{user_prompt}
"""

        # After all retries fail → hard failure (but clean)
        raise ValueError(
            f"Model failed to produce valid JSON after {retries + 1} attempts.\n"
            f"Last error:\n{last_error}"
        )
