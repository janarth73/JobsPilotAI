"""Scrapes jobs from companies' GitHub careers pages via RSS/JSON."""
import requests, hashlib, re, time
from bs4 import BeautifulSoup

def clean(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ''

def make_id(title, company):
    return 'gh_' + hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

SKILLS = ["python","java","javascript","react","django","flask","sql","aws",
          "docker","kubernetes","git","machine learning","node.js","golang"]

def get_skills(text):
    return ','.join([s for s in SKILLS if s in text.lower()])

def scrape(keywords, locations=None, max_jobs=20):
    """Scrape jobs from WeWorkRemotely — free public site."""
    jobs = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get("https://weworkremotely.com/remote-jobs.rss", headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, 'lxml-xml')
        items = soup.find_all('item')
        for kw in keywords:
            for item in items:
                title_tag = item.find('title')
                title = clean(title_tag.text if title_tag else '')
                if kw.lower() not in title.lower(): continue
                company_tag = item.find('company') or item.find('author')
                company = clean(company_tag.text if company_tag else 'Unknown')
                link_tag = item.find('link') or item.find('guid')
                url = clean(link_tag.text if link_tag else '')
                desc_tag = item.find('description')
                desc = clean(re.sub('<.*?>', '', desc_tag.text if desc_tag else ''))
                region_tag = item.find('region')
                loc = clean(region_tag.text if region_tag else 'Remote')
                jobs.append({
                    'job_id': make_id(title, company),
                    'title': title, 'company': company, 'location': loc,
                    'salary': '', 'experience': '',
                    'description': desc[:500],
                    'skills': get_skills(f"{title} {desc}"),
                    'apply_url': url, 'source': 'weworkremotely',
                    'posted_date': clean(item.find('pubDate').text if item.find('pubDate') else ''),
                    'match_score': 0.0,
                })
                if len(jobs) >= max_jobs: break
        time.sleep(1)
    except Exception as e:
        print(f"WeWorkRemotely error: {e}")
    return jobs
