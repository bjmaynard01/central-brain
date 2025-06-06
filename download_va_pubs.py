import os
import time
import json
import requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

BASE_URL = "https://www.va.gov/vhapublications/"
DOWNLOAD_DIR = "va_downloads"
METADATA_FILE = os.path.join(DOWNLOAD_DIR, "metadata.json")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

def get_all_pdf_links():
    driver = setup_driver()
    driver.get(BASE_URL)
    time.sleep(3)

    pdf_links = []
    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table tbody tr")
        for row in rows:
            link = row.find("a", href=True)
            if link and link["href"].endswith(".pdf"):
                pdf_url = link["href"]
                title = link.text.strip()
                if not pdf_url.startswith("http"):
                    pdf_url = BASE_URL + pdf_url.lstrip("/")
                pdf_links.append({"url": pdf_url, "title": title})
        
        # Click "Next" button if available
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            if "disabled" in next_button.get_attribute("class"):
                break
            next_button.click()
            time.sleep(2)
        except:
            break

    driver.quit()
    return pdf_links

def load_downloaded_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

def download_file(url, path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    downloaded = load_downloaded_metadata()
    links = get_all_pdf_links()

    for entry in tqdm(links, desc="Downloading PDFs"):
        filename = os.path.basename(entry["url"])
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if filename in downloaded:
            continue
        try:
            download_file(entry["url"], filepath)
            downloaded[filename] = {
                "url": entry["url"],
                "title": entry["title"],
                "path": filepath
            }
            save_metadata(downloaded)
        except Exception as e:
            print(f"Failed to download {entry['url']}: {e}")

if __name__ == "__main__":
    main()
