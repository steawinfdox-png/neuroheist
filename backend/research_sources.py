"""Research retrieval plus local Gemma inference; PubMed needs no secret."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from gemini_call import ask_gemini
from summarizer import summarize


def _fetch(url, data=None):
    headers = {"User-Agent": "NeuroLens-local-demo/1.0", "Accept": "application/json, application/xml"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(1048577)
        if len(body) > 1048576:
            raise ValueError("Research service response exceeded the size limit.")
        return body
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError("Research retrieval is unavailable. Check the internet connection and try again.") from error


def generate_query(treatment: str, focused=True):
    treatment_terms = treatment
    if "stereotactic radiosurgery" in treatment.casefold():
        treatment_terms = '"stereotactic radiosurgery" OR radiosurgery'
    diseases = '(brain OR intracranial) AND (tumor OR tumour OR metastases OR metastasis OR glioma OR glioblastoma OR meningioma OR schwannoma)'
    measurements = ('"volume reduction" OR "volume decreased" OR "tumor shrinkage" OR "volumetric reduction"'
                    if focused else '"tumor volume" OR "tumour volume" OR volumetric OR "tumor shrinkage"')
    return f'({treatment_terms}) AND ({diseases}) AND ({measurements}) NOT ("arteriovenous malformation" OR AVM)'


def _pubmed_sources(treatment):
    ids = []
    for focused in (True, False):
        params = urllib.parse.urlencode({
            "db": "pubmed", "term": generate_query(treatment, focused=focused), "retmode": "json",
            "retmax": 8, "sort": "relevance", "tool": "neurolens_local_demo",
        })
        search = json.loads(_fetch("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + params))
        ids = search.get("esearchresult", {}).get("idlist", [])[:8]
        if ids:
            break
    if not ids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "xml", "tool": "neurolens_local_demo"})
    tree = ET.fromstring(_fetch("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + params))
    sources = []
    for article in tree.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID", "")
        title_node = article.find(".//ArticleTitle")
        title = "".join(title_node.itertext()) if title_node is not None else "Untitled"
        abstract = "\n".join("".join(node.itertext()) for node in article.findall(".//Abstract/AbstractText"))
        if abstract and pmid:
            sources.append({"id": "PMID:" + pmid, "title": title, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "content": abstract[:6000]})
    return sources


def _tavily_sources(treatment, api_key):
    result = json.loads(_fetch("https://api.tavily.com/search", {
        "api_key": api_key, "query": generate_query(treatment),
        "include_domains": ["pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov", "nature.com", "sciencedirect.com", "frontiersin.org", "oup.com", "nih.gov"],
        "max_results": 5,
    }))
    return [{"id": "WEB:" + str(index + 1), "title": item.get("title", "Research source"),
             "url": item.get("url", ""), "content": item["content"][:6000]}
            for index, item in enumerate(result.get("results", [])) if item.get("content")]


def research_topic(treatment: str):
    if not isinstance(treatment, str) or not treatment.strip() or len(treatment) > 200:
        raise ValueError("Provide a treatment name with at most two hundred characters.")
    treatment = treatment.strip()
    sources = []
    provider = "pubmed"
    # Preserve the project's intended Tavily search when a key is configured.
    # Public PubMed is an explicit keyless fallback; LLM inference stays local.
    if os.getenv("TAVILY_API_KEY"):
        try:
            sources = _tavily_sources(treatment, os.environ["TAVILY_API_KEY"])
            provider = "tavily"
        except RuntimeError:
            pass
    if not sources:
        sources = _pubmed_sources(treatment)
        provider = "pubmed"
    if not sources:
        raise ValueError("No research abstracts were found for this treatment. Try a more specific treatment name.")
    content = "\n\n--- NEXT SOURCE ---\n\n".join(
        f"Source: {source['id']}\nTitle: {source['title']}\nURL: {source['url']}\nAbstract: {source['content']}"
        for source in sources
    )[:24000]
    summary = summarize(content)
    result = json.loads(ask_gemini(treatment, summary))
    result["sources"] = [{"id": source["id"], "title": source["title"], "url": source["url"]}
                         for source in sources if source["id"] == result["source_id"]]
    result["retrieval_provider"] = provider
    return json.dumps(result)
