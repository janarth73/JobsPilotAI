import requests, hashlib, re, time, random, json
from bs4 import BeautifulSoup

def clean(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ''

def make_id(title, company):
    return 'lr_' + hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

SKILLS = ["python","java","javascript","typescript","react","angular","vue","node.js",
          "django","flask","fastapi","spring","sql","mysql","postgresql","mongodb",
          "redis","aws","azure","gcp","docker","kubernetes","git","linux",
          "machine learning","deep learning","tensorflow","pytorch","pandas",
          "numpy","scikit-learn","rest api","graphql","microservices","c++","c#",
          "golang","rust","php","ruby","scala","agile","scrum","ci/cd","devops",
          "terraform","ansible","spark","hadoop","tableau","power bi","nlp"]

def get_skills(text):
    t = text.lower()
    return ','.join([s for s in SKILLS if s in t])

def scrape(keywords, locations, max_jobs=25):
    all_jobs = []
    headers  = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://www.linkedin.com/",
    }

    for kw in keywords:
        for loc in locations:
            jobs = []

            # ── Method 1: LinkedIn public job search (no login) ────────────
            try:
                params = {
                    "keywords":  kw,
                    "location":  loc,
                    "f_TPR":     "r86400",   # last 24 hours
                    "position":  1,
                    "pageNum":   0,
                    "start":     0,
                    "trk":       "public_jobs_jobs-search-bar_search-submit",
                }
                url = "https://www.linkedin.com/jobs/search"
                r   = requests.get(url, params=params, headers=headers, timeout=15)

                if r.status_code == 200 and "job" in r.text.lower():
                    soup  = BeautifulSoup(r.text, 'lxml')
                    cards = (
                        soup.find_all('div', class_='base-card') or
                        soup.find_all('li',  class_='jobs-search__results-list') or
                        soup.find_all('div', class_='job-search-card')
                    )

                    for card in cards[:max_jobs]:
                        try:
                            t_tag = (
                                card.find('h3', class_='base-search-card__title') or
                                card.find('h3', class_='job-search-card__title') or
                                card.find('a',  class_='base-card__full-link')
                            )
                            title = clean(t_tag.text if t_tag else '')
                            if not title: continue

                            c_tag = (
                                card.find('h4', class_='base-search-card__subtitle') or
                                card.find('a',  class_='hidden-nested-link') or
                                card.find('h4', class_='job-search-card__company-name')
                            )
                            company = clean(c_tag.text if c_tag else 'Unknown')

                            l_tag = (
                                card.find('span', class_='job-search-card__location') or
                                card.find('span', class_='base-search-card__metadata')
                            )
                            location = clean(l_tag.text if l_tag else loc)

                            a_tag = (
                                card.find('a', class_='base-card__full-link') or
                                card.find('a', href=re.compile(r'/jobs/view/'))
                            )
                            apply_url = ''
                            if a_tag and a_tag.get('href'):
                                apply_url = a_tag['href'].split('?')[0]

                            d_tag = card.find('time')
                            posted = clean(d_tag.get('datetime','') if d_tag else '')

                            s_tag = card.find('span', class_='job-search-card__salary-info')
                            salary = clean(s_tag.text if s_tag else '')

                            jobs.append({
                                'job_id':      make_id(title, company),
                                'title':       title,
                                'company':     company,
                                'location':    location,
                                'salary':      salary,
                                'experience':  '',
                                'description': f"{title} at {company} in {location}. Role: {kw}",
                                'skills':      get_skills(f"{title} {kw}"),
                                'apply_url':   apply_url,
                                'source':      'linkedin',
                                'posted_date': posted,
                                'match_score': 0.0,
                            })
                        except Exception:
                            continue

            except Exception as e:
                print(f"LinkedIn method 1 error [{kw}/{loc}]: {e}")

            # ── Method 2: LinkedIn JSON-LD embedded data ───────────────────
            if not jobs:
                try:
                    url  = f"https://www.linkedin.com/jobs/search?keywords={requests.utils.quote(kw)}&location={requests.utils.quote(loc)}"
                    r    = requests.get(url, headers=headers, timeout=15)
                    soup = BeautifulSoup(r.text, 'lxml')

                    for script in soup.find_all('script', type='application/ld+json'):
                        try:
                            data  = json.loads(script.string or '{}')
                            items = []
                            if isinstance(data, list):
                                items = data
                            elif data.get('@type') == 'JobPosting':
                                items = [data]
                            elif data.get('@type') == 'ItemList':
                                items = [e.get('item',{}) for e in data.get('itemListElement',[])]

                            for item in items[:max_jobs]:
                                title   = clean(item.get('title',''))
                                org     = item.get('hiringOrganization',{})
                                company = clean(org.get('name','') if isinstance(org,dict) else '')
                                jloc    = item.get('jobLocation',{})
                                addr    = jloc.get('address',{}) if isinstance(jloc,dict) else {}
                                location= clean(addr.get('addressLocality',loc) if isinstance(addr,dict) else loc)
                                desc    = clean(re.sub('<.*?>','',item.get('description','')))
                                sal     = item.get('baseSalary',{})
                                salary  = ''
                                if isinstance(sal,dict):
                                    val = sal.get('value',{})
                                    if isinstance(val,dict):
                                        salary = f"{sal.get('currency','')} {val.get('minValue','')} - {val.get('maxValue','')}"

                                if not title: continue
                                jobs.append({
                                    'job_id':      make_id(title, company),
                                    'title':       title,
                                    'company':     company,
                                    'location':    location,
                                    'salary':      salary,
                                    'experience':  '',
                                    'description': desc[:1000] or f"{title} at {company}",
                                    'skills':      get_skills(f"{title} {desc}"),
                                    'apply_url':   item.get('url',''),
                                    'source':      'linkedin',
                                    'posted_date': clean(item.get('datePosted','')[:10]),
                                    'match_score': 0.0,
                                })
                        except Exception:
                            continue
                except Exception as e:
                    print(f"LinkedIn method 2 error [{kw}/{loc}]: {e}")

            # ── Method 3: LinkedIn public RSS feed ─────────────────────────
            if not jobs:
                try:
                    rss_url = (
                        f"https://www.linkedin.com/jobs/search?keywords="
                        f"{requests.utils.quote(kw)}&location={requests.utils.quote(loc)}"
                        f"&f_TPR=r86400&count={max_jobs}"
                    )
                    r    = requests.get(rss_url, headers={
                        "User-Agent": "LinkedInBot/1.0",
                        "Accept":     "application/rss+xml, application/xml, text/xml"
                    }, timeout=15)
                    soup = BeautifulSoup(r.content, 'lxml-xml')
                    items= soup.find_all('item')

                    for item in items[:max_jobs]:
                        title   = clean(item.find('title').text if item.find('title') else '')
                        company = clean(item.find('company').text if item.find('company') else 'Unknown')
                        link    = clean(item.find('link').text if item.find('link') else '')
                        desc    = clean(re.sub('<.*?>','', item.find('description').text if item.find('description') else ''))
                        loc_tag = item.find('location') or item.find('jobLocation')
                        location= clean(loc_tag.text if loc_tag else loc)
                        pubdate = clean(item.find('pubDate').text[:10] if item.find('pubDate') else '')

                        if not title: continue
                        jobs.append({
                            'job_id':      make_id(title, company),
                            'title':       title,
                            'company':     company,
                            'location':    location,
                            'salary':      '',
                            'experience':  '',
                            'description': desc[:1000] or f"{title} at {company}",
                            'skills':      get_skills(f"{title} {desc}"),
                            'apply_url':   link,
                            'source':      'linkedin',
                            'posted_date': pubdate,
                            'match_score': 0.0,
                        })
                except Exception as e:
                    print(f"LinkedIn RSS error [{kw}/{loc}]: {e}")

            # ── Method 4: LinkedIn jobs via Google cache ───────────────────
            if not jobs:
                try:
                    search_url = (
                        f"https://www.linkedin.com/jobs/search?keywords="
                        f"{requests.utils.quote(kw)}&location={requests.utils.quote(loc)}&start=0"
                    )
                    r = requests.get(search_url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
                        "Accept": "text/html"
                    }, timeout=15)
                    soup  = BeautifulSoup(r.text, 'lxml')
                    cards = soup.find_all('div', attrs={'data-entity-urn': True})

                    for card in cards[:max_jobs]:
                        t_tag = card.find(['h3','h2','a'])
                        title = clean(t_tag.text if t_tag else '')
                        if not title: continue
                        c_tag = card.find(['h4','span'], class_=re.compile('company|employer'))
                        company = clean(c_tag.text if c_tag else 'Unknown')
                        a_tag = card.find('a', href=True)
                        url_  = a_tag['href'] if a_tag else ''
                        jobs.append({
                            'job_id':      make_id(title, company),
                            'title':       title,
                            'company':     company,
                            'location':    loc,
                            'salary':      '',
                            'experience':  '',
                            'description': f"{title} at {company}",
                            'skills':      get_skills(title),
                            'apply_url':   url_,
                            'source':      'linkedin',
                            'posted_date': '',
                            'match_score': 0.0,
                        })
                except Exception as e:
                    print(f"LinkedIn method 4 error [{kw}/{loc}]: {e}")

            all_jobs.extend(jobs)
            print(f"LinkedIn [{kw}/{loc}]: {len(jobs)} jobs found")
            time.sleep(random.uniform(2, 4))

    return all_jobs
