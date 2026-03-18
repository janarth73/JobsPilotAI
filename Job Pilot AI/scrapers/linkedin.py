"""
LinkedIn direct scraping is blocked by LinkedIn (returns 999).
Use JSearch API instead — it fetches real LinkedIn jobs via API.
This file is kept for reference only.
"""

def scrape(keywords, locations, max_jobs=20):
    raise ValueError(
        "LinkedIn blocks direct scraping (HTTP 999). "
        "Use JSearch platform instead — it fetches real LinkedIn jobs via API."
    )
