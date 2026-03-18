"""
Run this file on YOUR machine to diagnose scraper issues.
Command: python test_scrapers.py
"""
import requests, json
from bs4 import BeautifulSoup

print("=" * 50)
print("TEST 1: Internet Connection")
print("=" * 50)
try:
    r = requests.get("https://httpbin.org/get", timeout=5)
    print(f"Internet: OK (status {r.status_code})")
except Exception as e:
    print(f"Internet: FAILED — {e}")

print("\n" + "=" * 50)
print("TEST 2: JSearch API (LinkedIn+Indeed+Glassdoor)")
print("=" * 50)
API_KEY = input("Paste your JSearch API key: ").strip()
try:
    headers = {
        "X-RapidAPI-Key":  API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    r = requests.get(
        "https://jsearch.p.rapidapi.com/search",
        headers=headers,
        params={"query": "Python Developer in Bangalore", "page": "1", "num_pages": "1"},
        timeout=15
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        jobs = r.json().get('data', [])
        print(f"Jobs found: {len(jobs)}")
        for j in jobs[:3]:
            print(f"  - {j.get('job_title')} @ {j.get('employer_name')} [{j.get('job_publisher')}]")
    elif r.status_code == 401:
        print("INVALID API KEY")
    elif r.status_code == 429:
        print("RATE LIMIT — free quota exhausted")
    else:
        print(f"ERROR: {r.text[:300]}")
except Exception as e:
    print(f"FAILED: {e}")

print("\n" + "=" * 50)
print("TEST 3: RemoteOK")
print("=" * 50)
try:
    r = requests.get("https://remoteok.com/api",
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    jobs = [d for d in r.json() if isinstance(d, dict) and d.get('position')]
    print(f"Status: {r.status_code} | Jobs: {len(jobs)}")
    if jobs:
        print(f"Sample: {jobs[0].get('position')} @ {jobs[0].get('company')}")
except Exception as e:
    print(f"FAILED: {e}")

print("\n" + "=" * 50)
print("TEST 4: Naukri API")
print("=" * 50)
try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.naukri.com/",
        "appid": "109", "systemid": "109",
    }
    params = {"noOfResults": 5, "urlType": "search_by_keyword",
              "searchType": "adv", "keyword": "Python Developer",
              "location": "Bangalore", "pageNo": 1}
    r = requests.get("https://www.naukri.com/jobapi/v3/search",
                     params=params, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
        jobs = data.get('jobDetails') or data.get('jobs') or []
        print(f"Jobs found: {len(jobs)}")
        if jobs:
            print(f"Sample: {jobs[0].get('title')} @ {jobs[0].get('companyName')}")
        else:
            print(f"Keys in response: {list(data.keys())}")
    except:
        print(f"Not JSON. Response: {r.text[:300]}")
except Exception as e:
    print(f"FAILED: {e}")

print("\n" + "=" * 50)
print("TEST 5: WeWorkRemotely RSS")
print("=" * 50)
try:
    r = requests.get("https://weworkremotely.com/remote-jobs.rss",
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(r.content, 'lxml-xml')
    items = soup.find_all('item')
    print(f"Status: {r.status_code} | Jobs: {len(items)}")
    if items:
        print(f"Sample: {items[0].find('title').text[:60] if items[0].find('title') else 'N/A'}")
except Exception as e:
    print(f"FAILED: {e}")

print("\nDone. Share the output above to diagnose issues.")
