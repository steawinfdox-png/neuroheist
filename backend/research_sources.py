from dotenv import load_dotenv
from tavily import TavilyClient
from summarizer import summarize
from gemini_call import ask_gemini
import os

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

target_domains = [
    "ncbi.nlm.nih.gov",
    "nature.com",
    "biorxiv.org",
    "sciencedirect.com",
    "frontiersin.org",
    "oup.com",
    "nih.gov",
    "cdc.gov",
    "who.int",
    ".edu",
    ".gov"
]


def generate_query(treatment: str):
    return f"{treatment}'s average tumor reduction percentage on brain tumor size"


def research_topic(treatment: str):

    query = generate_query(treatment)

    response = tavily.search(
        query=query,
        include_domains=target_domains,
        include_domains_mode="filter",
        max_results=3
    )

    results = response["results"]

    # Extract ONLY the content from each result
    contents = [
        result["content"]
        for result in results
        if result.get("content")
    ]

    # Combine all research content into one string
    combined_content = "\n\n--- NEXT SOURCE ---\n\n".join(contents)

    # ONE Groq API call
    summary = summarize(combined_content)
    answer = ask_gemini(treatment, summary)

    return answer
