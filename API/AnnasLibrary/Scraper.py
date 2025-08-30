from http.client import HTTPException
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
# envpath = Path(__file__).resolve().parent.parent / ".env"

load_dotenv()
session = requests.Session()
def Download(url: str):
    url = os.getenv("BASE_URL") + url
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml").find_all("ul", class_="list-inside mb-4 ml-1")
    res = soup[-1].find_all("li")[0].find("a")["href"]
    res = os.getenv("BASE_URL") + res
    session.close()
    return res

def Search(query: str):
    base_url = os.getenv("BASE_URL")
    search_url = base_url + "/search?q=" + query
    try:
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    results = soup.find("div", class_="js-aarecord-list-outer").find_all("a", class_="custom-a block mr-2 sm:mr-4 hover:opacity-80")

    res = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all download tasks to the thread pool
        future_to_download = {executor.submit(Download, i.get("href")): i for i in results}

        # Collect the results as they are completed
        for future in as_completed(future_to_download):
            item = future_to_download[future]
            try:
                download_link = future.result()
                res.append({
                    "title": item.find("div", class_="font-bold text-violet-900 line-clamp-[5]")["data-content"],
                    "img": item.find("img")["src"],
                    "path": item.get("href"),
                    "download": download_link
                })
            except Exception as e:
                print(f"Error while downloading {item.get('href')}: {e}")

    session.close()
    return res