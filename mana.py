from New import download_annual_report
MANAGEMENT_KEYWORDS = [
    "management discussion",
    "management discussion and analysis",
    "md&a",
    "chairman",
    "chairman's message",
    "chairman’s message",
    "ceo message",
    "ceo’s message",
    "managing director",
    "board of directors",
    "directors’ report",
    "corporate governance",
    "independent director",
    "audit committee",
    "nomination and remuneration committee",
    "leadership team",
    "key managerial personnel"
]
import fitz  # PyMuPDF

def read_pdf_pages(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except:
        return None
    pages = []

    for i in range(len(doc)):
        text = doc[i].get_text()
        pages.append({
            "page_number": i + 1,
            "text": text
        })

    return pages
def is_management_page(text):
    text = text.lower()
    return any(keyword in text for keyword in MANAGEMENT_KEYWORDS)
#extract pages
def extract_management_pages(pages):
    management_pages = []

    for page in pages:
        if is_management_page(page["text"]):
            management_pages.append(page)

    return management_pages
#clean text
def clean_text(text):
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text
#extract text
def extract_management_text(pdf_path):
    pages = read_pdf_pages(pdf_path)
    if pages is None:
        return None
    management_pages = extract_management_pages(pages)

    extracted_text = []

    for page in management_pages:
        cleaned = clean_text(page["text"])
        extracted_text.append({
            "page_number": page["page_number"],
            "text": cleaned
        })

    return extracted_text


#rag_retrievel
# Rag retrievel Layer1
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_faiss_index(management_text):
    texts = [item["text"] for item in management_text]
    embeddings = model.encode(texts, normalize_embeddings=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(np.array(embeddings))

    return index, embeddings

# Layer2
def retrieve_management_context(query, index, documents, k=6):
    query_vec = model.encode([query], normalize_embeddings=True)
    scores, ids = index.search(query_vec, k)

    context = ""
    for i, s in zip(ids[0], scores[0]):
        if s > 0.45:  # relevance threshold
            context += f"[Relevance {round(s,2)}] {documents[i]['text']}\n"
    return context
#SystemPrompt
SYSTEM_PROMPT = """
You are an equity research analyst.

Rules:
- Use ONLY the provided context
- Penalize governance failures heavily
- No assumptions
- Conservative scoring
- Scores must be integers from 0 to 10
- Output JSON only
"""
#User Prompt
def build_scoring_prompt(context):
    return f"""
Context:
{context}

Evaluate management and board performance.

Score each category from 0–10:
- Leadership
- CapitalAllocation
- Governance
- Communication
- Stability
- MarketTrust

Return JSON only:
{{
  "Leadership": {{"score": X, "reason": "..."}},
  "CapitalAllocation": {{"score": X, "reason": "..."}},
  "Governance": {{"score": X, "reason": "..."}},
  "Communication": {{"score": X, "reason": "..."}},
  "Stability": {{"score": X, "reason": "..."}},
  "MarketTrust": {{"score": X, "reason": "..."}}
}}
"""
def extract_json(text):
    """
    Extract first JSON object from messy LLM output
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise RuntimeError(f"No JSON found in LLM output:\n{text}")
    return match.group(0)
import re
#perplexity call
import requests
import json
import os

def safe_parse_json(raw_text):
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty LLM response")

    # Remove markdown code fences
    raw_text = re.sub(r"```json", "", raw_text)
    raw_text = re.sub(r"```", "", raw_text)

    # Extract JSON block
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("⚠ Invalid JSON from LLM")
        print("Raw JSON snippet:\n", json_str[:500])
        raise e



def call_llm(prompt,key):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",   # optional but recommended
            "X-Title": "MyApp"
        },
        json={
            # 🔹 Choose model here
            "model": "deepseek/deepseek-chat",
            # other examples:
            # "model": "anthropic/claude-3-haiku",
            # "model": "openai/gpt-4o-mini",

            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        },
        timeout=60
    )

    # 🔴 DEBUG STEP (VERY IMPORTANT)
    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter API Error {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            f"Non-JSON response received:\n{response.text}"
        )

    raw_text = data["choices"][0]["message"]["content"]

    print("\n🔵 RAW LLM OUTPUT:\n", raw_text, "\n")

    try:
        return safe_parse_json(raw_text)
    except Exception as e:
        print("⚠ JSON parsing failed:", e)

    # Safe fallback to prevent crash
        cleaned = extract_json(raw_text)
        return safe_parse_json(cleaned)
PPLX_API_KEY=""
def call_llm_PPL(prompt):
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {PPLX_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        },
        timeout=60
    )

    # 🔴 DEBUG STEP (VERY IMPORTANT)
    if response.status_code != 200:
        raise RuntimeError(
            f"API Error {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            f"Non-JSON response received:\n{response.text}"
        )

    data = response.json()
    raw_text = data["choices"][0]["message"]["content"]

    print("\n🔵 RAW LLM OUTPUT:\n", raw_text, "\n")

    try:
        # try direct JSON parse
        return json.loads(raw_text)
    except:
        # fallback: extract JSON substring
        cleaned = extract_json(raw_text)
        return json.loads(cleaned)

 # safer than hardcoding

def call_llm_groq(prompt,key):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        json={
            # 🔹 Choose Groq-supported model
            "model": "llama-3.3-70b-versatile",
            # other examples:
            # "model": "llama-3.1-8b-instant"
            # "model": "mixtral-8x7b-32768"

            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1200   # 🔥 IMPORTANT (avoid token overflow)
        },
        timeout=60
    )

    # 🔴 DEBUG STEP
    if response.status_code != 200:
        raise RuntimeError(
            f"Groq API Error {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            f"Non-JSON response received:\n{response.text}"
        )

    raw_text = data["choices"][0]["message"]["content"]

    print("\n🔵 RAW LLM OUTPUT:\n", raw_text, "\n")

    try:
        return safe_parse_json(raw_text)
    except Exception as e:
        print("⚠ JSON parsing failed:", e)

    # Safe fallback to prevent crash
        cleaned = extract_json(raw_text)
        return json.loads(cleaned)
    # 🔴 DEBUG STEP (VERY IMPORTANT)
#6 column analys
WEIGHTS = {
    "Leadership": 0.25,
    "CapitalAllocation": 0.20,
    "Governance": 0.20,
    "Communication": 0.15,
    "Stability": 0.10,
    "MarketTrust": 0.10
}

def compute_final_score(llm_output):
    print(llm_output)
    score = 0

    for k, w in WEIGHTS.items():
        try:
            category_score = llm_output[k]["score"]
        except (KeyError, TypeError):
            print(f"⚠️ Missing score for {k}, using 0")
            category_score = 0

        score += category_score * 10 * w
    return round(score, 2)
#run


def run_management_analysis(pdf_path):
    management_text=extract_management_text(pdf_path)
    if management_text is None:
        return None
    print(f"Management-related pages found: {len(management_text)}\n")
    if len(management_text) == 0:
        return None
    pages = read_pdf_pages(pdf_path)
    mgmt_pages = extract_management_pages(pages)

    index, _ = build_faiss_index(management_text)

    context = retrieve_management_context(
        "management quality, governance, board effectiveness",
        index,
        management_text
    )
    llm_output=None
    DKEY=[]
    API_KEYS=[]
    for key in DKEY:
            try:
                llm_output = call_llm(build_scoring_prompt(context), key)
                print(f"✅ LLM call succeeded with key: {key}")
                break  # success, exit loop
            except Exception as e:
                print(f"⚠ LLM call failed with key {key}: {e}")
                continue
    if llm_output is None:
        for key in API_KEYS:
            try:
                llm_output = call_llm_groq(build_scoring_prompt(context), key)
                print(f"✅ LLM call succeeded with key: {key}")
                break  # success, exit loop
            except Exception as e:
                print(f"⚠ LLM call failed with key {key}: {e}")
                continue
    final_score = compute_final_score(llm_output)
    if llm_output is None:
        print("⚠ All API keys failed. Using default fallback output.")
        llm_output = {
            "Leadership": {"score": 0, "reason": "All API calls failed"},
            "CapitalAllocation": {"score": 0, "reason": "All API calls failed"},
            "Governance": {"score": 0, "reason": "All API calls failed"},
            "Communication": {"score": 0, "reason": "All API calls failed"},
            "Stability": {"score": 0, "reason": "All API calls failed"},
            "MarketTrust": {"score": 0, "reason": "All API calls failed"},
        }

    return {
        "ManagementScore": final_score,
        "Breakdown": llm_output,
        "PagesUsed": sorted(set(p["page_number"] for p in mgmt_pages))
    }

#conversion csv
import csv

def save_to_csv(financial_year,result, filename="management_analysis.csv"):
    Scores=[]
    name=f"management_analysis_{financial_year}.csv"
    with open(name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(["Metric", "Score", "Reason"])

        # Breakdown scores
        for metric, data in result["Breakdown"].items():
            Scores.append(data["score"])
            writer.writerow([
                metric,
                data["score"],
                data["reason"]
            ])
        Scores.append(result["ManagementScore"])
        # Final weighted score
        writer.writerow([
            "FinalManagementScore",
            result["ManagementScore"],
            "Weighted aggregate score"
        ])

    print(f"Saved CSV → {name}")
def extract_scores_with_final(result):
    scores = {
        metric: data["score"]
        for metric, data in result["Breakdown"].items()
    }
    scores["FinalManagementScore"] = result["ManagementScore"]
    return scores
#extract
def Main(ticker: str, financial_year: str, output_csv: str = None):
    """
    Run management analysis for a given company and FY.

    Args:
        ticker (str): Screener ticker
        financial_year (str): Financial year (e.g., '2022')
        output_csv (str): Optional CSV filename. Defaults to '<ticker>_management_analysis.csv'

    Returns:
        dict: Extracted scores including final management score
    """
    # 1️⃣ Download PDF
    pdf_path = download_annual_report(ticker, financial_year)
    print(f"PDF saved at: {pdf_path}\n")

    # 2️⃣ Run management analysis
    result = run_management_analysis(pdf_path)
    print(f"Analysis Result:\n{result}\n")
    if result is None:
        return None

    # 3️⃣ Save CSV if filename provided
    if not output_csv:
        output_csv = f"management_analysis.csv"
    save_to_csv(financial_year,result, output_csv)

    # 4️⃣ Extract only numeric scores
    scores = extract_scores_with_final(result)
    print(f"Final Scores:\n{scores}\n")

    return scores


