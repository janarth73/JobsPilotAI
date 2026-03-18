import requests, hashlib, re, time

SKILLS = ["python","java","javascript","typescript","react","angular","vue","node.js",
          "django","flask","fastapi","sql","postgresql","mongodb","aws","azure","docker",
          "kubernetes","git","machine learning","tensorflow","pytorch","pandas","rest api",
          "golang","rust","php","ruby","scala","devops","terraform","ci/cd"]

def clean(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ''

def get_skills(tags, title):
    combined = title.lower() + ' ' + ' '.join(tags).lower()
    return ','.join([s for s in SKILLS if s in combined])

def make_id(title, company):
    return 'ro_' + hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

def scrape(keywords, locations=None, max_jobs=20):
    jobs = []
    try:
        r = requests.get("https://remoteok.com/api",
                         headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"},
                         timeout=15)
        if r.status_code != 200:
            print(f"RemoteOK status: {r.status_code}")
            return []
        listings = [d for d in r.json() if isinstance(d, dict) and d.get('position')]
        for kw in keywords:
            matched = [j for j in listings
                       if kw.lower() in j.get('position','').lower()
                       or kw.lower() in ' '.join(j.get('tags',[])).lower()]
            for item in matched[:max_jobs]:
                title   = clean(item.get('position',''))
                company = clean(item.get('company',''))
                if not title: continue
                desc    = clean(re.sub('<.*?>', '', item.get('description','')))
                jobs.append({
                    'job_id':      make_id(title, company),
                    'title':       title,
                    'company':     company,
                    'location':    'Remote',
                    'salary':      clean(item.get('salary','')),
                    'experience':  '',
                    'description': desc[:2000],
                    'skills':      get_skills(item.get('tags',[]), title),
                    'apply_url':   item.get('url','') or item.get('apply_url',''),
                    'source':      'remoteok',
                    'posted_date': item.get('date','')[:10] if item.get('date') else '',
                    'match_score': 0.0,
                })
        time.sleep(1)
    except Exception as e:
        print(f"RemoteOK error: {e}")
    return jobs
