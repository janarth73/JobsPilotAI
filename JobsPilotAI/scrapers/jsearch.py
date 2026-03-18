import requests, hashlib, re, time, os
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
API_KEY  = os.getenv("JSEARCH_API_KEY", "")
BASE_URL = "https://jsearch.p.rapidapi.com/search"
HEADERS  = {
    "X-RapidAPI-Key":  API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}

SKILLS = ["python","java","javascript","typescript","react","angular","vue","node.js",
          "django","flask","fastapi","spring","sql","mysql","postgresql","mongodb",
          "redis","aws","azure","gcp","docker","kubernetes","git","linux",
          "machine learning","deep learning","tensorflow","pytorch","pandas",
          "numpy","scikit-learn","rest api","graphql","microservices","c++","c#",
          "golang","rust","php","ruby","scala","agile","scrum","ci/cd","spark",
          "hadoop","tableau","power bi","nlp","computer vision","devops","terraform"]

def clean(text):
    return re.sub(r'\s+', ' ', str(text).strip()) if text else ''

def get_skills(text):
    t = text.lower()
    return ','.join([s for s in SKILLS if s in t])

def make_id(title, company, source):
    return 'js_' + hashlib.md5(f"{title}{company}{source}".encode()).hexdigest()[:12]

def scrape(keywords, locations, max_jobs=20):
    if not API_KEY:
        raise ValueError(
            "JSearch API key not found. "
            "Add JSEARCH_API_KEY=your_key to your .env file."
        )

    all_jobs = []
    for kw in keywords:
        for loc in locations:
            try:
                params = {
                    "query":       f"{kw} in {loc}",
                    "page":        "1",
                    "num_pages":   "1",
                    "date_posted": "week",
                    "country":     "in" if any(x in loc.lower() for x in
                                   ["india","bangalore","chennai","mumbai",
                                    "hyderabad","delhi","pune","remote"]) else "us",
                }
                r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)

                if r.status_code == 401:
                    raise ValueError("Invalid JSearch API key — check your .env file")
                if r.status_code == 429:
                    raise ValueError("JSearch rate limit reached (200 req/month on free plan)")
                if r.status_code != 200:
                    print(f"JSearch {r.status_code} for {kw}/{loc}")
                    continue

                for item in r.json().get('data', [])[:max_jobs]:
                    title   = clean(item.get('job_title',''))
                    company = clean(item.get('employer_name',''))
                    if not title: continue

                    loc_str = clean(' '.join(filter(None,[
                        item.get('job_city',''), item.get('job_state',''),
                        item.get('job_country','')
                    ]))) or loc
                    desc    = clean(item.get('job_description',''))
                    pub     = clean(item.get('job_publisher','')).lower()
                    source  = pub if pub in ['linkedin','indeed','glassdoor','ziprecruiter'] else 'jsearch'
                    smin    = item.get('job_min_salary')
                    smax    = item.get('job_max_salary')
                    curr    = item.get('job_salary_currency','')
                    per     = item.get('job_salary_period','')
                    salary  = f"{curr} {smin}-{smax}/{per}" if smin and smax else ''
                    quals   = item.get('job_highlights',{}).get('Qualifications',[])
                    exp     = next((clean(q) for q in quals if 'year' in q.lower()), '')
                    skills  = get_skills(' '.join(quals)) or get_skills(desc)

                    all_jobs.append({
                        'job_id':      make_id(title, company, source),
                        'title':       title,
                        'company':     company,
                        'location':    loc_str,
                        'salary':      salary,
                        'experience':  exp,
                        'description': desc[:2000],
                        'skills':      skills,
                        'apply_url':   item.get('job_apply_link') or item.get('job_google_link',''),
                        'source':      source,
                        'posted_date': clean(item.get('job_posted_at_datetime_utc','')[:10]),
                        'match_score': 0.0,
                    })
                time.sleep(0.5)
            except ValueError:
                raise
            except Exception as e:
                print(f"JSearch error [{kw}/{loc}]: {e}")
    return all_jobs
