



# ==============================
# REQUIRED LIBRARIES
# ==============================

# requests → used to call APIs from the internet
import requests

# feedparser → used to read Google News RSS feeds
import feedparser

# pandas → used to store and save data in CSV/JSON format
import pandas as pd

# datetime & time → used to handle year-based filtering
from datetime import datetime
import time




# ==============================
# GOOGLE NEWS SCRAPING (YEAR-WISE)
# ==============================

def fetch_google_news(company, year, limit=50):
    """
    This function collects news ONLY from the selected year
    using Google News RSS feed
    """
    y=int(year)
    ye=str(y+1)
    # Start and end date of selected year
    start_date = f"{year}-04-01"
    end_date = f"{ye}-03-31"

    # Google News RSS URL with date filtering
    url = (
        f"https://news.google.com/rss/search?"
        f"q={company}+after:{start_date}+before:{end_date}"
    )

    # Reading RSS feed
    feed = feedparser.parse(url)

    results = []

    # Looping through each news article
    for entry in feed.entries[:limit]:
        published_date = datetime(*entry.published_parsed[:6])

        results.append({
            "source": "google_news",
            "text": entry.title,
            "link": entry.link,  # ✅ ADD THIS
            "date": published_date
        })

    return results


# ==============================
# HACKER NEWS SCRAPING (YEAR-WISE)
# ==============================

def fetch_hackernews(company, year):
    """
    This function collects Hacker News posts
    only from the selected year using timestamp filter
    """

    # Convert year start & end dates into UNIX timestamp
    start_timestamp = int(time.mktime(time.strptime(f"{year}-01-01", "%Y-%m-%d")))
    end_timestamp = int(time.mktime(time.strptime(f"{year}-12-31", "%Y-%m-%d")))

    # Hacker News API URL with time filter
    url = (
        f"https://hn.algolia.com/api/v1/search?"
        f"query={company}&numericFilters="
        f"created_at_i>={start_timestamp},created_at_i<={end_timestamp}"
    )

    # Calling API
    response = requests.get(url).json()

    results = []

    # Loop through each result
    for hit in response.get("hits", []):
        if hit.get("title"):
            
            # Use original article link if available
            link = hit.get("url")
            
            # If original link not available, use HN discussion link
            if not link:
                link = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"

            results.append({
                "source": "hacker_news",
                "text": hit["title"],
                "link": link,  # ✅ ADD THIS
                "date": datetime.fromtimestamp(hit["created_at_i"])
            })

    return results


# ==============================
# MAIN PIPELINE FUNCTION
# ==============================

def runs(company, year):
    """
    This function controls the complete workflow:
    data collection → sentiment analysis → file saving
    """

    print(f"\n🔍 Collecting {year} news for: {company}")

    all_data = []

    # Collecting data from Google News
    google_news = fetch_google_news(company, year)

    # Collecting data from Hacker News
    hacker_news = fetch_hackernews(company, year)

    # Combine both sources
    for item in google_news + hacker_news:
        all_data.append({
            "source": item["source"],
            "text": item["text"],
            "link": item["link"],  # ✅ ADD THIS
            "date": item["date"].strftime("%Y-%m-%d"),
            "year": year,
        })

    # If no data found
    if not all_data:
        print("❌ No data found for this year")
        return

    # Convert data into DataFrame
    df = pd.DataFrame(all_data)

    # File names
    csv_file = f"COMPANY_sentiment_{year}.csv"

    # Save files
    df.to_csv(csv_file, index=False)


    print(f"📁 CSV saved: {csv_file}")
    return all_data


