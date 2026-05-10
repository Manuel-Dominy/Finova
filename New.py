import os
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def safe_get(session, url, headers, retries=5):
    for attempt in range(retries):
        try:
            r = session.get(url, headers=headers, timeout=20, stream=True)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            print(f"⚠ Attempt {attempt+1}/{retries} failed:", e)
            time.sleep(2)
    return None


def download_annual_report(ticker: str, financial_year: str) -> str | None:
    base_url = f"https://www.screener.in/company/{ticker}/"
    print(base_url)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.screener.in/"
    }

    session = requests.Session()

    # 1️⃣ Fetch company page safely
    response = safe_get(session, base_url, headers)
    if response is None:
        print("❌ Could not fetch company page")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 2️⃣ Find matching PDF
    pdf_url = None
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]

        if ".pdf" in href.lower() and financial_year in text:
            pdf_url = urljoin(base_url, href)  # handles relative links
            break

    if not pdf_url:
        print(f"❌ No annual report found for FY {financial_year}")
        return None

    # 3️⃣ Prepare folder
    folder = os.path.join(os.getcwd(), financial_year)
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(
        folder,
        f"{ticker}_annual_report_{financial_year}.pdf"
    )

    # 4️⃣ Download safely
    # 4️⃣ Download safely with retry during streaming
    max_download_retries = 5

    for attempt in range(max_download_retries):
        try:
            pdf_response = session.get(
                pdf_url,
                headers=headers,
                stream=True,
                timeout=120
            )
            pdf_response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in pdf_response.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)

            print("✅ PDF saved:", file_path)
            return file_path

        except requests.exceptions.ChunkedEncodingError:
            print(f"⚠ Stream interrupted (Attempt {attempt+1})")
            if os.path.exists(file_path):
                os.remove(file_path)
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"⚠ Download failed (Attempt {attempt+1}):", e)
            if os.path.exists(file_path):
                os.remove(file_path)
            time.sleep(3)

    print("❌ PDF download failed after retries")
    return None