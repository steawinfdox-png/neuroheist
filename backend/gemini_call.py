import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from google.genai import types
from gemini_model import GeminiInfo
import json

load_dotenv()

# Initialize the Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(treatment: str, summary: str, retries: int = 3) -> str:
    prompt = f"""
You are a neuroscience research analyst.

For the following brain tumor reduction treatment:

Treatment: {treatment}

Treatment summary:
{summary}

Using ONLY the treatment summary and the brain information below, provide information about the treatment and estimate a tumor reduction factor.

Brain information:

Total Brain Volume: {brain_vol}

Tumor Brain Volume: {tumor_vol}

Tumor/Brain Ratio: {ratio}


Return ONLY valid JSON matching exactly this structure:

{{
    "treatment_name": "string",
    "treatment_description": "string",
    "tumor_factor": 0.43
}}

Rules:
- treatment_name must be the name of the treatment.
- treatment_description must be a concise description of how the treatment works, based only on the provided treatment summary.
- tumor_factor must be a decimal number between 0 and 1 representing the estimated tumor volume reduction.
- For example, 0.43 means a 43% tumor volume reduction.
- tumor_factor cannot be 0.0.
- Do not include a percent sign.
- Do not include any fields other than treatment_name, treatment_description, and tumor_factor.
- Do not include explanations outside the JSON.
- Do not return markdown or code fences.
- Return valid JSON only.
"""

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model = "gemini-3.8-flash",
                contents=prompt,
                config = types.GenerateContentConfig(
                    response_mime_type = "application/json",
                    response_schema = GeminiInfo
                )
            )
            return json.loads(response.text)

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