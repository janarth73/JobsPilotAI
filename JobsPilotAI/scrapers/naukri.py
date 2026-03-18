import requests, hashlib, re, time, random, json
from bs4 import BeautifulSoup

def clean(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ''

def make_id(title, company):
    return 'nk_' + hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

SKILLS = ["python","java","javascript","react","angular","django","flask","fastapi",
          "sql","mysql","postgresql","mongodb","aws","azure","docker","kubernetes",
          "git","machine learning","tensorflow","pytorch","pandas","rest api","node.js"]

def get_skills(text):
    return ','.join([s for s in SKILLS if s in text.lower()])

def scrape(keywords, locations, max_jobs=20):
    all_jobs = []
    for kw in keywords:
        for loc in locations:
            jobs = _try_api(kw, loc, max_jobs)
            if not jobs:
                jobs = _try_html(kw, loc, max_jobs)
            all_jobs.extend(jobs)
            time.sleep(random.uniform(1, 2))
    return all_jobs

def _try_api(kw, loc, max_jobs):
    jobs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.naukri.com/",
            "appid": "109", "systemid": "109",
        }
        url = "https://www.naukri.com/jobapi/v3/search"
        params = {"noOfResults": max_jobs, "urlType": "search_by_keyword",
                  "searchType": "adv", "keyword": kw, "location": loc, "pageNo": 1}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        items = data.get('jobDetails') or data.get('jobs') or []
        for item in items:
            title   = clean(item.get('title',''))
            company = clean(item.get('companyName',''))
            if not title: continue
            ph = item.get('placeholders', [])
            location_str = clean(ph[0].get('label', loc)) if ph else loc
            apply_url = item.get('jdURL','') or item.get('applyRedirectURL','')
            if apply_url and not apply_url.startswith('http'):
                apply_url = 'https://www.naukri.com' + apply_url
            skills_raw = item.get('tagsAndSkills','') or item.get('skills','')
            skills_str = ','.join(skills_raw) if isinstance(skills_raw, list) else clean(skills_raw)
            jobs.append({
                'job_id': make_id(title, company),
                'title': title, 'company': company,
                'location': location_str,
                'salary': clean(item.get('salary','')),
                'experience': clean(item.get('experience','')),
                'description': clean(item.get('jobDescription', f"{title} at {company}")),
                'skills': skills_str or get_skills(title),
                'apply_url': apply_url, 'source': 'naukri',
                'posted_date': clean(item.get('footerPlaceholderLabel','')),
                'match_score': 0.0,
            })
    except Exception as e:
        print(f"Naukri API error: {e}")
    return jobs

def _try_html(kw, loc, max_jobs):
    jobs = []
    try:
        kw_slug  = re.sub(r'[^a-z0-9]+', '-', kw.lower()).strip('-')
        loc_slug = re.sub(r'[^a-z0-9]+', '-', loc.lower()).strip('-')
        url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                   "Accept-Language": "en-US,en;q=0.9"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')

        # Try JSON-LD embedded data first
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '[]')
                if not isinstance(data, list): data = [data]
                for item in data[:max_jobs]:
                    title   = clean(item.get('title',''))
                    org     = item.get('hiringOrganization', {})
                    company = clean(org.get('name','') if isinstance(org, dict) else '')
                    jloc    = item.get('jobLocation', {})
                    addr    = jloc.get('address', {}) if isinstance(jloc, dict) else {}
                    location_str = clean(addr.get('addressLocality', loc) if isinstance(addr, dict) else loc)
                    if not title: continue
                    jobs.append({
                        'job_id': make_id(title, company),
                        'title': title, 'company': company,
                        'location': location_str, 'salary': '', 'experience': '',
                        'description': clean(item.get('description','')),
                        'skills': get_skills(title),
                        'apply_url': item.get('url',''), 'source': 'naukri',
                        'posted_date': '', 'match_score': 0.0,
                    })
            except Exception:
                continue

        # HTML card fallback
        if not jobs:
            cards = (soup.find_all('article', class_='jobTuple') or
                     soup.find_all('div', class_='srp-jobtuple-wrapper') or
                     soup.find_all('div', attrs={'data-job-id': True}))
            for card in cards[:max_jobs]:
                try:
                    t = card.find('a', class_='title') or card.find('a', attrs={'title': True})
                    title = clean(t.text if t else '')
                    if not title: continue
                    c = card.find('a', class_='subTitle') or card.find('a', class_='companyName')
                    company = clean(c.text if c else '')
                    href = t.get('href','') if t else ''
                    if href and not href.startswith('http'):
                        href = 'https://www.naukri.com' + href
                    jobs.append({
                        'job_id': make_id(title, company),
                        'title': title, 'company': company, 'location': loc,
                        'salary': '', 'experience': '',
                        'description': f"{title} at {company}",
                        'skills': get_skills(title),
                        'apply_url': href, 'source': 'naukri',
                        'posted_date': '', 'match_score': 0.0,
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"Naukri HTML error: {e}")
    return jobs
