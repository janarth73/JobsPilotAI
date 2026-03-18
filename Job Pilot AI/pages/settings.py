import streamlit as st
import yaml, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(ROOT, 'config.yaml')

def load():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)

def save(cfg):
    with open(CFG_PATH, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False)

def show():
    st.title("⚙️ Settings")
    cfg = load()

    t1, t2 = st.tabs(["🔍 Scraper", "🗄️ Database"])

    # ── Scraper ────────────────────────────────────────────────────────────
    with t1:
        with st.form("scraper_cfg"):
            st.subheader("Default Keywords & Locations")
            kw = st.text_area("Keywords (one per line)",
                              "\n".join(cfg['filters']['keywords']), height=140)
            lc = st.text_area("Locations (one per line)",
                              "\n".join(cfg['filters']['locations']), height=120)
            mx = st.slider("Max jobs per scrape", 5, 100,
                           cfg['filters'].get('max_jobs', 20))
            if st.form_submit_button("💾 Save", type="primary"):
                cfg['filters']['keywords']  = [k.strip() for k in kw.split('\n') if k.strip()]
                cfg['filters']['locations'] = [l.strip() for l in lc.split('\n') if l.strip()]
                cfg['filters']['max_jobs']  = mx
                save(cfg)
                st.success("✅ Saved!")

        st.divider()
       
    # ── Database ───────────────────────────────────────────────────────────
    with t2:
        from db.models import get_session, Job
        from sqlalchemy import func
        s       = get_session()
        total   = s.query(func.count(Job.id)).scalar() or 0
        applied = s.query(func.count(Job.id)).filter(Job.is_applied == True).scalar() or 0
        new_j   = s.query(func.count(Job.id)).filter(Job.status == 'new').scalar() or 0
        s.close()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Jobs",   total)
        c2.metric("Applied",      applied)
        c3.metric("New / Unseen", new_j)

        st.divider()
        st.subheader("Maintenance")
        days = st.slider("Purge unapplied jobs older than (days)", 15, 30, 20)
        if st.button("🗑️ Purge Old Jobs", type="secondary"):
            from datetime import datetime, timedelta
            s2  = get_session()
            cut = datetime.utcnow() - timedelta(days=days)
            n   = s2.query(Job).filter(
                Job.scraped_at < cut, Job.is_applied == False).delete()
            s2.commit(); s2.close()
            st.success(f"✅ Deleted {n} old unapplied jobs.")

        st.divider()
        st.subheader("Reset Database")
        st.warning("This will permanently delete all scraped jobs and applications.")
        confirm = st.checkbox("I understand — delete everything")
        if confirm:
            if st.button("⚠️ Reset Database", type="secondary"):
                s3 = get_session()
                s3.query(Job).delete()
                s3.commit(); s3.close()
                st.success("✅ Database cleared.")
                st.rerun()
