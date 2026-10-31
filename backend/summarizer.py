from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarize(content: str):
    prompt = f"""
    You are a neuroscience research analyzer. Summarize the following research into a condensed paragraph
    of simple sentences containing only concrete numbers detailing the treatment's reduction of brain tumor
    size. No filler, no context, no intro, no transitions: the sentences can only be chosen if they contain
    numbers.
    Here is the research:
    {content}
    """
    completion = groq.chat.completions.create(
        model = "openai/gpt-oss-120b",
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature = 0.2,
        max_completion_tokens=300,
        reasoning_effort="low",
        stream=False
    )
    response = completion.choices[0].message.content
    return response