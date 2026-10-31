import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

# Initialize the Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(treatment: str, summary: str, retries: int = 3) -> str:
    prompt = f"""
You are analyzing research about brain tumor treatment.

Treatment:
{treatment}

Research summary:
{summary}

Estimate the expected tumor volume reduction from this treatment based ONLY
on the research summary.

Return ONLY valid JSON in exactly this format:

{{"reduction": 0.43}}

Rules:
- reduction must be a decimal number between 0 and 1.
- 0.43 means a 43% tumor volume reduction.
- Do not include a percent sign.
- Do not include any explanation.
- Do not include any other fields.
- Do not return markdown.
- Number cannot be 0.0
"""

    for attempt in range(retries):
        try:
            chat = client.chats.create(
                model="gemini-3.8-flash"
            )

            response = chat.send_message(prompt)

            return response.text.strip()

        except APIError as e:
            if e.code in (503, 429) and attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                print(
                    f"Service busy ({e.code}). "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                print(f"Gemini API Error: {e}")
                break

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    return '{"error": "Unable to generate response from Gemini API."}'