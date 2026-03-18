import streamlit as st
import sys, os, importlib.util, yaml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import get_session, Job

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(ROOT, 'config.yaml')

def load_scraper(name):
    path = os.path.join(ROOT, 'scrapers', f'{name}.py')
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_config():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)

def save_config(cfg):
    with open(CFG_PATH, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False)

def save_jobs(jobs, session):
    saved = dupes = 0
    for j in jobs:
        if not session.query(Job).filter(Job.job_id == j['job_id']).first():
            session.add(Job(**j))
            saved += 1
        else:
            dupes += 1
    session.commit()
    return saved, dupes

SCRAPER_MAP = {
    "LinkedIn (RSS — Free)":                   "linkedin_rss",
    "JSearch — LinkedIn + Indeed + Glassdoor": "jsearch",
    "Naukri":                                  "naukri",
    "RemoteOK":                                "remoteok",
    "WeWorkRemotely":                          "github_jobs",
}

POPULAR_KWS = [
    "Python Developer","Java Developer","React Developer",
    "Data Scientist","Machine Learning Engineer","DevOps Engineer",
    "Full Stack Developer","Backend Developer","Frontend Developer",
    "Software Engineer","Data Analyst","Cloud Engineer",
    "Node.js Developer","Django Developer","AI Engineer"
]

POPULAR_LOCS = [
    "Bangalore","Chennai","Mumbai","Hyderabad","Pune",
    "Delhi","Noida","Gurgaon","Remote","Coimbatore",
    "Madurai","Ahmedabad","Kochi","Indore","Salem"
]

def show():
    st.title("🔍 Scrape Jobs")
    cfg = load_config()

    saved_kws  = cfg['filters'].get('keywords', [])
    saved_locs = cfg['filters'].get('locations', [])

    # ── Quick Add Keywords (ABOVE inputs) ──────────────────────────────────
    with st.expander("⚡ Quick Add Keywords", expanded=True):
        st.caption("Click to instantly add popular keywords")
        kw_cols = st.columns(5)
        for i, kw in enumerate(POPULAR_KWS):
            if kw_cols[i % 5].button(kw, key=f"qkw_{i}",
                                      type="primary" if kw in saved_kws else "secondary"):
                if kw not in saved_kws:
                    saved_kws.append(kw)
                    cfg['filters']['keywords'] = saved_kws
                    save_config(cfg)
                    st.rerun()
                else:
                    saved_kws.remove(kw)
                    cfg['filters']['keywords'] = saved_kws
                    save_config(cfg)
                    st.rerun()

    # ── Quick Add Locations (ABOVE inputs) ────────────────────────────────
    with st.expander("📍 Quick Add Locations", expanded=True):
        st.caption("Click to instantly add popular India locations")
        lc_cols = st.columns(5)
        for i, loc in enumerate(POPULAR_LOCS):
            if lc_cols[i % 5].button(loc, key=f"qloc_{i}",
                                       type="primary" if loc in saved_locs else "secondary"):
                if loc not in saved_locs:
                    saved_locs.append(loc)
                    cfg['filters']['locations'] = saved_locs
                    save_config(cfg)
                    st.rerun()
                else:
                    saved_locs.remove(loc)
                    cfg['filters']['locations'] = saved_locs
                    save_config(cfg)
                    st.rerun()

    st.divider()

    # ── Keywords & Locations text areas ───────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        keywords_input = st.text_area(
            "Keywords (one per line)",
            value="\n".join(saved_kws),
            height=130,
            help="Edit manually or use Quick Add above"
        )
    with c2:
        locations_input = st.text_area(
            "Locations (one per line)",
            value="\n".join(saved_locs),
            height=130,
            help="Edit manually or use Quick Add above"
        )

    kws  = [k.strip() for k in keywords_input.split('\n') if k.strip()]
    locs = [l.strip() for l in locations_input.split('\n') if l.strip()]

    # Show pills
    if kws:
        pills = " ".join([
            f'<span style="background:#1e3a5f;color:#60a5fa;padding:2px 10px;'
            f'border-radius:20px;font-size:11px;margin:2px;display:inline-block">{k}</span>'
            for k in kws])
        st.markdown(f"**Keywords:** {pills}", unsafe_allow_html=True)
    if locs:
        pills = " ".join([
            f'<span style="background:#1e3a30;color:#34d399;padding:2px 10px;'
            f'border-radius:20px;font-size:11px;margin:2px;display:inline-block">{l}</span>'
            for l in locs])
        st.markdown(f"**Locations:** {pills}", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    max_jobs = st.slider("Max jobs per search", 5, 50, 25)

    sc1, sc2 = st.columns([3,1])
    with sc2:
        if st.button("💾 Save Defaults"):
            cfg['filters']['keywords']  = kws
            cfg['filters']['locations'] = locs
            save_config(cfg)
            st.success("✅ Saved!")

    # ── Platforms ─────────────────────────────────────────────────────────
    st.markdown("**Select Platforms**")
    r1c1, r1c2, r1c3 = st.columns(3)
    r2c1, r2c2       = st.columns(2)
    p_li  = r1c1.checkbox("LinkedIn (RSS — Free)",                    value=True,  key="p_li_rss")
    p_js  = r1c2.checkbox("JSearch — LinkedIn+Indeed+Glassdoor",      value=False, key="p_jsearch")
    p_nk  = r1c3.checkbox("Naukri",                                    value=True,  key="p_naukri")
    p_ro  = r2c1.checkbox("RemoteOK",                                  value=True,  key="p_remoteok")
    p_wwr = r2c2.checkbox("WeWorkRemotely",                            value=False, key="p_wwr")

    selected = []
    if p_li:  selected.append("LinkedIn (RSS — Free)")
    if p_js:  selected.append("JSearch — LinkedIn+Indeed+Glassdoor")
    if p_nk:  selected.append("Naukri")
    if p_ro:  selected.append("RemoteOK")
    if p_wwr: selected.append("WeWorkRemotely")

    st.markdown("---")
    go = st.button("🚀 Start Scraping", type="primary", disabled=not selected)

    if go:
        if not kws:  st.error("Enter at least one keyword."); return
        if not locs: st.error("Enter at least one location."); return

        cfg['filters']['keywords']  = kws
        cfg['filters']['locations'] = locs
        save_config(cfg)
        st.session_state['scrape_keywords']  = kws
        st.session_state['scrape_locations'] = locs

        all_jobs = []
        progress = st.progress(0, text="Starting...")
        step     = 1.0 / len(selected)

        for i, platform in enumerate(selected):
            progress.progress(i * step, text=f"Scraping {platform}...")
            try:
                mod  = load_scraper(SCRAPER_MAP[platform])
                jobs = mod.scrape(kws, locs, max_jobs)
                all_jobs.extend(jobs)
                if jobs:
                    if "JSearch" in platform:
                        from collections import Counter
                        src = Counter(j['source'] for j in jobs)
                        bd  = " | ".join(f"{s.capitalize()}: {c}" for s,c in src.items())
                        st.success(f"✅ {platform}: {len(jobs)} jobs — {bd}")
                    else:
                        st.success(f"✅ {platform}: {len(jobs)} jobs found")
                else:
                    st.warning(f"⚠️ {platform}: 0 jobs found")
            except ValueError as e:
                st.error(f"❌ {platform}: {e}")
            except Exception as e:
                st.error(f"❌ {platform} failed: {e}")

        progress.progress(0.9, text="Auto-scoring against resume...")
        resume = st.session_state.get('resume')
        if resume and resume.get('text') and all_jobs:
            from processor.matcher import score_match
            for j in all_jobs:
                j['match_score'] = score_match(
                    resume['text'], j.get('description',''), j.get('skills',''))
            st.info(f"🎯 Auto-scored {len(all_jobs)} jobs against your resume")
        elif not resume:
            st.caption("💡 Upload resume in Resume & AI page to auto-score jobs")

        progress.progress(0.95, text="Saving to database...")
        if all_jobs:
            s = get_session()
            saved, dupes = save_jobs(all_jobs, s)
            s.close()
            progress.progress(1.0, text="Done!")
            st.success(
                f"✅ Done! **{len(all_jobs)}** found · "
                f"**{saved}** new saved · **{dupes}** duplicates")
        else:
            progress.empty()
            st.error("No jobs found. Try different keywords or locations.")
