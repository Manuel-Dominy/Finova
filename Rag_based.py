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
    doc = fitz.open(pdf_path)
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
#perplexity call
import requests
import json
PPLX_API_KEY=""
def call_llm(prompt):
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

    return json.loads(data["choices"][0]["message"]["content"])
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
    score = 0
    for k, w in WEIGHTS.items():
        score += llm_output[k]["score"] * 10 * w
    return round(score, 2)
#run


def run_management_analysis(pdf_path):
    management_text=extract_management_text(pdf_path)
    print(f"Management-related pages found: {len(management_text)}\n")
    pages = read_pdf_pages(pdf_path)
    mgmt_pages = extract_management_pages(pages)

    index, _ = build_faiss_index(management_text)

    context = retrieve_management_context(
        "management quality, governance, board effectiveness",
        index,
        management_text
    )

    llm_output = call_llm(build_scoring_prompt(context))
    final_score = compute_final_score(llm_output)

    return {
        "ManagementScore": final_score,
        "Breakdown": llm_output,
        "PagesUsed": sorted(set(p["page_number"] for p in mgmt_pages))
    }

#conversion csv
import csv

def save_to_csv(result, filename="management_analysis.csv"):
    Scores=[]
    with open(filename, "w", newline="", encoding="utf-8") as f:
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

    print(f"Saved CSV → {filename}")
def extract_scores_with_final(result):
    scores = {
        metric: data["score"]
        for metric, data in result["Breakdown"].items()
    }
    scores["FinalManagementScore"] = result["ManagementScore"]
    return scores

def Main():
    # Run management analysis
    hi = run_management_analysis("Vodafone.pdf")
    print(hi)

    # Save to CSV (just for storage)
    save_to_csv(hi, "Vodafone_management_analysis.csv")

    # Extract only numeric scores
    scores = extract_scores_with_final(hi)
    
    return scores

