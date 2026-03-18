# Job Pilot AI

## Setup
```
pip install --only-binary=:all: -r requirements.txt
```

## Run
```
python -m streamlit run app.py
```

## Platforms supported
- Naukri (API + HTML fallback)
- Indeed (HTML scraping)
- RemoteOK (free public JSON API)
- WeWorkRemotely (free RSS feed)

## Features
- Resume upload + TF-IDF match scoring
- Application tracker with status updates
- Email notifications via Gmail SMTP
- Export applications as CSV
