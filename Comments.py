import requests
from bs4 import BeautifulSoup
from youtube_comment_downloader import YoutubeCommentDownloader
import feedparser
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from News import runs
analyzer = SentimentIntensityAnalyzer()


# -------------------------------------------
# Helper: Sentiment Score
# -------------------------------------------



# -------------------------------------------
# 3. GOOGLE NEWS
# -------------------------------------------
def fetch_google_news(company, limit=100):
    url = f"https://news.google.com/rss/search?q={company}"
    feed = feedparser.parse(url)

    return [(entry.title + " " + entry.summary) for entry in feed.entries[:limit]]


# -------------------------------------------
# 4. HACKER NEWS
# -------------------------------------------
def fetch_hackernews(company):
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={company}"
        data = requests.get(url).json()
        return [hit["title"] or "" for hit in data["hits"]]
    except:
        return [] 


# -------------------------------------------
# MAIN PIPELINE
# -------------------------------------------
def run(company):
    print(f"🔍 Collecting data for: {company}")

    data = {
        "news": fetch_google_news(company),
        "hackernews": fetch_hackernews(company),
    }

    all_rows = []

    for source, items in data.items():
        print(f"✔ {source}: {len(items)}")

        for text in items:
            all_rows.append({
                "source": source,
                "text": text,
                
            })

    if not all_rows:
        print("\n❌ No data collected.")
        return

    df = pd.DataFrame(all_rows)

    csv_file = f"{company}_sentiment.csv"
    

    df.to_csv(csv_file, index=False)
    

    print(f"\n📁 CSV saved: {csv_file}")
    

    
    return all_rows


# -------------------------------------------
# USER INPUT
# -------------------------------------------


import requests

def sentiment(Company,year):
    Comp=Company.replace(" ", "-")
    Texts=runs(Comp,year)
    print(Texts)
    url = "http://127.0.0.1:5001/predict"
    headers = {
        "X-API-KEY": "FinovaProjectApiKey7036", # Your Secret Key
        "Content-Type": "application/json"
    }
    if Texts is None:
        return None
    sentences = [row["text"] for row in Texts]
    payload = {
        "sentences": sentences
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        res=response.json()["normalized_score"]
        print("API Response:", res)
    else:
        print(f"Failed with status {response.status_code}: {response.text}")
    return res
