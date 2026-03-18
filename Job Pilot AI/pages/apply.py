import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import get_session, Job, ApplicationLog
from datetime import datetime

def extract_exp_years(exp_str):
    if not exp_str: return None
    nums = re.findall(r'\d+', str(exp_str))
    if nums: return int(nums[0])
    return None

def show():
    st.title("🚀 Apply Jobs")

    s        = get_session()
    all_jobs = s.query(Job).all()
    s.close()

    if not all_jobs:
        st.info("No jobs yet. Go to 🔍 Scrape Jobs first!")
        return

    # ── Stats ──────────────────────────────────────────────────────────────
    total      = len(all_jobs)
    applied    = sum(1 for j in all_jobs if j.is_applied)
    high_match = sum(1 for j in all_jobs if j.match_score >= 0.7 and not j.is_applied)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jobs",     total)
    m2.metric("Applied",        applied)
    m3.metric("High Match 70%+",high_match)
    m4.metric("Unapplied",      total - applied)

    st.divider()

    # ── Filters ────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### 🔧 Filters")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            src_filter     = st.multiselect("Platform",
                ["linkedin","indeed","glassdoor","naukri","remoteok","jsearch","weworkremotely"],
                default=[], placeholder="All platforms")
            keyword_filter = st.text_input("Search title / company", placeholder="e.g. Python, Razorpay")
        with fc2:
            min_score      = st.slider("Min Match %", 0, 100, 0, step=5)
            location_filter= st.text_input("Location contains", placeholder="e.g. Bangalore, Remote")
        with fc3:
            show_applied   = st.checkbox("Show already applied", value=False)
            sort_by        = st.selectbox("Sort by",
                ["Match Score ↓","Match Score ↑","Newest First","Company A-Z"])
            exp_filter     = st.selectbox("Experience",
                ["Any","0-1 years","1-3 years","3-5 years","5+ years"])

    # ── Pagination ─────────────────────────────────────────────────────────
    ITEMS_PER_PAGE = 30
    if 'apply_page' not in st.session_state:
        st.session_state['apply_page'] = 1

    # ── Query ──────────────────────────────────────────────────────────────
    s = get_session()
    q = s.query(Job)
    if not show_applied:  q = q.filter(Job.is_applied == False)
    if src_filter:        q = q.filter(Job.source.in_(src_filter))
    if min_score > 0:     q = q.filter(Job.match_score >= min_score / 100)
    if location_filter:   q = q.filter(Job.location.ilike(f"%{location_filter}%"))
    jobs = q.all()
    s.close()

    # In-memory filters
    if keyword_filter:
        kw   = keyword_filter.lower()
        jobs = [j for j in jobs if kw in (j.title or '').lower()
                or kw in (j.company or '').lower()
                or kw in (j.skills or '').lower()]

    if exp_filter != "Any":
        exp_ranges = {"0-1 years":(0,1),"1-3 years":(1,3),"3-5 years":(3,5),"5+ years":(5,99)}
        lo, hi = exp_ranges.get(exp_filter,(0,99))
        filtered = []
        for j in jobs:
            yrs = extract_exp_years(j.experience)
            if yrs is None or lo <= yrs <= hi:
                filtered.append(j)
        jobs = filtered

    # Sort
    if sort_by == "Match Score ↓":   jobs = sorted(jobs, key=lambda j: j.match_score, reverse=True)
    elif sort_by == "Match Score ↑": jobs = sorted(jobs, key=lambda j: j.match_score)
    elif sort_by == "Newest First":  jobs = sorted(jobs, key=lambda j: j.scraped_at or datetime.min, reverse=True)
    elif sort_by == "Company A-Z":   jobs = sorted(jobs, key=lambda j: (j.company or '').lower())

    total_filtered = len(jobs)
    total_pages    = max(1, (total_filtered + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    # Reset page if out of bounds
    if st.session_state['apply_page'] > total_pages:
        st.session_state['apply_page'] = 1

    # Paginate
    start = (st.session_state['apply_page'] - 1) * ITEMS_PER_PAGE
    end   = start + ITEMS_PER_PAGE
    page_jobs = jobs[start:end]

    # ── Results count + pagination ─────────────────────────────────────────
    rc1, rc2 = st.columns([3, 2])
    with rc1:
        st.markdown(
            f"**{total_filtered} jobs found** "
            f"· Showing {start+1}–{min(end, total_filtered)} "
            f"· Page {st.session_state['apply_page']} of {total_pages}"
        )
    with rc2:
        pc1, pc2, pc3, pc4, pc5 = st.columns(5)
        if pc1.button("⏮ First",    key="ap_first",  disabled=st.session_state['apply_page']==1):
            st.session_state['apply_page'] = 1; st.rerun()
        if pc2.button("◀ Prev",     key="ap_prev",   disabled=st.session_state['apply_page']==1):
            st.session_state['apply_page'] -= 1; st.rerun()
        pc3.markdown(f"<div style='text-align:center;font-size:12px;padding-top:8px'>{st.session_state['apply_page']}/{total_pages}</div>", unsafe_allow_html=True)
        if pc4.button("Next ▶",     key="ap_next",   disabled=st.session_state['apply_page']==total_pages):
            st.session_state['apply_page'] += 1; st.rerun()
        if pc5.button("Last ⏭",     key="ap_last",   disabled=st.session_state['apply_page']==total_pages):
            st.session_state['apply_page'] = total_pages; st.rerun()

    if not page_jobs:
        st.info("No jobs match your filters.")
        return

    # ── Job Cards ──────────────────────────────────────────────────────────
    src_colors = {
        "linkedin":"#1e3a5f","indeed":"#1a3320","glassdoor":"#1e3a2a",
        "naukri":"#3b2500","remoteok":"#2d1b69","jsearch":"#1e3a30","weworkremotely":"#1f2937",
    }
    src_text = {
        "linkedin":"#60a5fa","indeed":"#4ade80","glassdoor":"#6ee7b7",
        "naukri":"#fb923c","remoteok":"#a78bfa","jsearch":"#34d399","weworkremotely":"#9ca3af",
    }

    for job in page_jobs:
        pct    = int(job.match_score * 100)
        color  = "#4ade80" if pct >= 70 else "#fbbf24" if pct >= 40 else "#f87171"
        src    = (job.source or '').lower()
        sb_bg  = src_colors.get(src, "#1f2937")
        sb_txt = src_text.get(src, "#9ca3af")

        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                st.markdown(f"### {job.title or 'Untitled'}")
                st.markdown(
                    f"**{job.company or 'Unknown'}** · 📍 {job.location or '—'} · "
                    f"<span style='background:{sb_bg};color:{sb_txt};padding:2px 8px;"
                    f"border-radius:20px;font-size:11px'>{src.capitalize()}</span>",
                    unsafe_allow_html=True)
                details = []
                if job.salary:      details.append(f"💰 {job.salary}")
                if job.experience:  details.append(f"🕐 {job.experience}")
                if job.posted_date: details.append(f"📅 {job.posted_date}")
                if details: st.caption(" · ".join(details))
                if job.skills: st.caption(f"🛠 {job.skills[:120]}")
            with c2:
                st.markdown(f"<div style='text-align:center;font-size:20px;font-weight:700;color:{color};padding-top:8px'>{pct}%</div>", unsafe_allow_html=True)
                st.caption("match")
            with c3:
                if job.is_applied:
                    st.success("✅ Applied")
                    if job.applied_at:
                        st.caption(job.applied_at.strftime("%d %b"))
                else:
                    if st.button("Apply", key=f"apply_{job.id}", type="primary"):
                        s2 = get_session()
                        j2 = s2.query(Job).filter(Job.id == job.id).first()
                        if j2:
                            j2.is_applied = True
                            j2.applied_at = datetime.utcnow()
                            j2.status     = "applied"
                            s2.add(ApplicationLog(job_id=job.id, action="applied", note="1-click"))
                            s2.commit()
                        s2.close()
                        st.rerun()
                if job.apply_url:
                    st.link_button("Open", job.apply_url)
                if not job.is_applied and pct >= 50:
                    if st.button("✨ Tailor", key=f"tailor_{job.id}",
                                 help="Pre-select this job in Resume & AI page"):
                        st.session_state['_selected_job_label'] = (
                            f"{job.title} @ {job.company} [{job.source}]  —  {pct}% match"
                        )
                        st.session_state['active_page'] = 'resume'
                        st.rerun()

    # ── Bottom pagination ──────────────────────────────────────────────────
    st.markdown("---")
    bp1, bp2, bp3, bp4, bp5 = st.columns(5)
    if bp1.button("⏮ First", key="ap_first_b",  disabled=st.session_state['apply_page']==1):
        st.session_state['apply_page'] = 1; st.rerun()
    if bp2.button("◀ Prev",  key="ap_prev_b",   disabled=st.session_state['apply_page']==1):
        st.session_state['apply_page'] -= 1; st.rerun()
    bp3.markdown(f"<div style='text-align:center;font-size:12px;padding-top:8px'>{st.session_state['apply_page']}/{total_pages}</div>", unsafe_allow_html=True)
    if bp4.button("Next ▶",  key="ap_next_b",   disabled=st.session_state['apply_page']==total_pages):
        st.session_state['apply_page'] += 1; st.rerun()
    if bp5.button("Last ⏭",  key="ap_last_b",   disabled=st.session_state['apply_page']==total_pages):
        st.session_state['apply_page'] = total_pages; st.rerun()
