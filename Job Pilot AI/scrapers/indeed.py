import requests, hashlib, re, time, random
from bs4 import BeautifulSoup

def clean(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ''

def make_id(title, company):
    return 'in_' + hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

SKILLS = ["python","java","javascript","react","django","flask","sql","mysql",
          "postgresql","mongodb","aws","azure","docker","kubernetes","git",
          "machine learning","tensorflow","pandas","rest api","node.js","angular"]

def get_skills(text):
    return ','.join([s for s in SKILLS if s in text.lower()])

def scrape(keywords, locations, max_jobs=20):
    all_jobs = []
    for kw in keywords:
        for loc in locations:
            all_jobs.extend(_scrape(kw, loc, max_jobs))
            time.sleep(random.uniform(1, 2))
    return all_jobs

def _scrape(kw, loc, max_jobs):
    jobs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml",
        }
        params = {"q": kw, "l": loc, "fromage": "7", "limit": max_jobs}
        r = requests.get("https://www.indeed.com/jobs", params=params, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')

        cards = (soup.find_all('div', class_='job_seen_beacon') or
                 soup.find_all('td', class_='resultContent') or
                 soup.find_all('div', attrs={'data-testid': 'slider_item'}))

        for card in cards[:max_jobs]:
            try:
                t = (card.find('h2', class_='jobTitle') or
                     card.find('a', attrs={'data-testid': 'job-title'}))
                title = clean(t.text if t else '')
                if not title: continue

                c = (card.find('span', attrs={'data-testid': 'company-name'}) or
                     card.find('span', class_='companyName'))
                company = clean(c.text if c else 'Unknown')

                l = (card.find('div', attrs={'data-testid': 'text-location'}) or
                     card.find('div', class_='companyLocation'))
                location = clean(l.text if l else loc)

                s = card.find('div', attrs={'data-testid': 'attribute_snippet_testid'})
                salary = clean(s.text if s else '')

                a = card.find('a', class_='jcs-JobTitle') or card.find('a', href=re.compile(r'/rc/clk'))
                href = a['href'] if a else ''
                if href and not href.startswith('http'):
                    href = 'https://www.indeed.com' + href

                jobs.append({
                    'job_id': make_id(title, company),
                    'title': title, 'company': company, 'location': location,
                    'salary': salary, 'experience': '',
                    'description': f"{title} at {company} in {location}",
                    'skills': get_skills(f"{title} {kw}"),
                    'apply_url': href, 'source': 'indeed',
                    'posted_date': '', 'match_score': 0.0,
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Indeed error: {e}")
    return jobs
