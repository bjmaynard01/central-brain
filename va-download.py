import requests
from bs4 import BeautifulSoup
import os

# URL of the VA Search page
BASE_URL = "https://www.va.gov/vapubs/Search_action.cfm"

# Output directory
OUTPUT_DIR = "va_documents"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Start session for efficiency
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Step 1: Get the search results page
response = session.get(BASE_URL)
soup = BeautifulSoup(response.text, "html.parser")

# Step 2: Extract viewPublication links
view_pub_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "viewPublication.asp?Pub_ID=" in href:
        full_url = requests.compat.urljoin(BASE_URL, href)
        view_pub_links.append(full_url)

print(f"Found {len(view_pub_links)} publication pages.")

# Step 3 & 4: Visit each publication page and download media
for pub_page in view_pub_links:
    try:
        print(f"Checking: {pub_page}")
        r = session.get(pub_page)
        sub_soup = BeautifulSoup(r.text, "html.parser")

        # Step 3: Look for the real PDF download link
        found = False
        for a in sub_soup.find_all("a", href=True):
            href = a['href']
            if "action=getpdf" in href and href.lower().endswith('.pdf'):
                file_url = requests.compat.urljoin(pub_page, href)
                filename = file_url.split("Pub_ID=")[-1].split("&")[0] + ".pdf"
                filepath = os.path.join(OUTPUT_DIR, f"va_pub_{filename}")

                print(f" → Downloading: {file_url}")
                file_response = session.get(file_url)
                with open(filepath, "wb") as f:
                    f.write(file_response.content)
                print(f" ✅ Saved to {filepath}")
                found = True
                break

        if not found:
            print(" ⚠️ PDF link not found on this page.")

    except Exception as e:
        print(f" ❌ Error processing {pub_page}: {e}")