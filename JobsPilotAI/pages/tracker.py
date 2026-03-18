import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import get_session, Job, ApplicationLog
from datetime import datetime

ITEMS_PER_PAGE = 30

def show():
    st.title("📊 Application Tracker")

    s       = get_session()
    applied = s.query(Job).filter(Job.is_applied == True).all()
    s.close()

    # ── Metrics ────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Applied",      len(applied))
    c2.metric("Under Review", sum(1 for j in applied if j.status == 'under_review'))
    c3.metric("Interview",    sum(1 for j in applied if j.status == 'interview'))
    c4.metric("Offer",        sum(1 for j in applied if j.status == 'offer'))
    c5.metric("Rejected",     sum(1 for j in applied if j.status == 'rejected'))

    st.divider()

    if not applied:
        st.info("No applications yet. Go to 🚀 Apply Jobs and start applying!")
        return

    # ── Status update ──────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Update Application Status")
        options = {f"{j.title} @ {j.company} [{j.source}]": j for j in applied}
        sel     = st.selectbox("Select application", list(options.keys()))
        if sel:
            job = options[sel]
            uc1, uc2, uc3 = st.columns([2, 2, 1])
            statuses = ["applied","under_review","interview","offer","rejected"]
            cur_idx  = statuses.index(job.status) if job.status in statuses else 0
            new_status = uc1.selectbox("Status", statuses, index=cur_idx)
            note       = uc2.text_input("Note (optional)")
            with uc3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Update", type="primary"):
                    s2 = get_session()
                    j2 = s2.query(Job).filter(Job.id == job.id).first()
                    if j2:
                        j2.status = new_status
                        s2.add(ApplicationLog(job_id=job.id,
                                              action=f"status → {new_status}", note=note))
                        s2.commit()
                    s2.close()
                    st.success(f"✅ Updated to {new_status}")
                    st.rerun()

    st.divider()

    # ── Filter + pagination ────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    status_filter  = fc1.multiselect("Filter by status",
        ["applied","under_review","interview","offer","rejected"], default=[])
    source_filter  = fc2.multiselect("Filter by platform",
        ["linkedin","indeed","naukri","remoteok","jsearch"], default=[])
    search_filter  = fc3.text_input("Search title / company", placeholder="e.g. Python, Razorpay")

    # Apply filters
    filtered = applied
    if status_filter:
        filtered = [j for j in filtered if j.status in status_filter]
    if source_filter:
        filtered = [j for j in filtered if (j.source or '') in source_filter]
    if search_filter:
        kw = search_filter.lower()
        filtered = [j for j in filtered if
                    kw in (j.title or '').lower() or kw in (j.company or '').lower()]

    total_filtered = len(filtered)
    total_pages    = max(1, (total_filtered + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if 'tracker_page' not in st.session_state:
        st.session_state['tracker_page'] = 1
    if st.session_state['tracker_page'] > total_pages:
        st.session_state['tracker_page'] = 1

    start     = (st.session_state['tracker_page'] - 1) * ITEMS_PER_PAGE
    end       = start + ITEMS_PER_PAGE
    page_jobs = filtered[start:end]

    # ── Pagination controls ────────────────────────────────────────────────
    pc1, pc2, pc3 = st.columns([3, 2, 1])
    with pc1:
        st.markdown(
            f"**{total_filtered} applications** · "
            f"Showing {start+1}–{min(end,total_filtered)} · "
            f"Page {st.session_state['tracker_page']} of {total_pages}"
        )
    with pc2:
        nav1, nav2, nav3, nav4 = st.columns(4)
        if nav1.button("⏮", key="tr_first", disabled=st.session_state['tracker_page']==1):
            st.session_state['tracker_page'] = 1; st.rerun()
        if nav2.button("◀",  key="tr_prev",  disabled=st.session_state['tracker_page']==1):
            st.session_state['tracker_page'] -= 1; st.rerun()
        if nav3.button("▶",  key="tr_next",  disabled=st.session_state['tracker_page']==total_pages):
            st.session_state['tracker_page'] += 1; st.rerun()
        if nav4.button("⏭",  key="tr_last",  disabled=st.session_state['tracker_page']==total_pages):
            st.session_state['tracker_page'] = total_pages; st.rerun()
    with pc3:
        st.download_button(
            "⬇ CSV",
            data=pd.DataFrame([{
                "Title":   j.title, "Company": j.company,
                "Platform":j.source, "Status": j.status,
                "Applied": j.applied_at.strftime("%Y-%m-%d") if j.applied_at else "—",
                "Match %": f"{int(j.match_score*100)}%",
                "URL":     j.apply_url
            } for j in filtered]).to_csv(index=False),
            file_name="applications.csv",
            mime="text/csv"
        )

    # ── Table ──────────────────────────────────────────────────────────────
    status_colors = {
        "applied":      ("#1e3a5f","#60a5fa"),
        "under_review": ("#3b2500","#fb923c"),
        "interview":    ("#2d1b69","#a78bfa"),
        "offer":        ("#1a3320","#4ade80"),
        "rejected":     ("#3b0f0f","#f87171"),
    }

    # Header
    st.markdown("""
<div style="display:grid;grid-template-columns:2.5fr 1.5fr 1fr 1fr 1fr 1fr;
padding:8px 12px;border-bottom:1px solid #1f2937;margin-top:8px">
  <span style="font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase">Job</span>
  <span style="font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase">Company</span>
  <span style="font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase">Platform</span>
  <span style="font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase">Match</span>
  <span style="font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase">Applied</span>
  <span style="font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase">Status</span>
</div>
""", unsafe_allow_html=True)

    for job in page_jobs:
        pct   = int(job.match_score * 100)
        mc    = "#4ade80" if pct >= 70 else "#fbbf24" if pct >= 40 else "#f87171"
        sbg, stxt = status_colors.get(job.status or 'applied', ("#1f2937","#9ca3af"))
        date  = job.applied_at.strftime("%d %b %Y") if job.applied_at else "—"

        src_badges = {
            "linkedin":"#1e3a5f;color:#60a5fa","indeed":"#1a3320;color:#4ade80",
            "naukri":"#3b2500;color:#fb923c","remoteok":"#2d1b69;color:#a78bfa",
            "jsearch":"#1e3a30;color:#34d399","glassdoor":"#1e3a2a;color:#6ee7b7",
        }
        src = (job.source or '').lower()
        sb  = src_badges.get(src, "#1f2937;color:#9ca3af")

        st.markdown(f"""
<div style="display:grid;grid-template-columns:2.5fr 1.5fr 1fr 1fr 1fr 1fr;
padding:10px 12px;border-bottom:1px solid #1a2332;align-items:center">
  <span style="font-size:13px;font-weight:500;color:#f3f4f6">{job.title or '—'}</span>
  <span style="font-size:12px;color:#9ca3af">{job.company or '—'}</span>
  <span><span style="background:{sb};padding:2px 8px;border-radius:20px;font-size:10px;font-weight:500">{src.capitalize()}</span></span>
  <span style="font-size:13px;font-weight:600;color:{mc}">{pct}%</span>
  <span style="font-size:12px;color:#9ca3af">{date}</span>
  <span><span style="background:{sbg};color:{stxt};padding:2px 8px;border-radius:20px;font-size:10px;font-weight:500">{(job.status or 'applied').replace('_',' ').title()}</span></span>
</div>
""", unsafe_allow_html=True)

    # ── Bottom pagination ──────────────────────────────────────────────────
    st.markdown("---")
    bn1, bn2, bn3, bn4 = st.columns(4)
    if bn1.button("⏮ First", key="tr_first_b", disabled=st.session_state['tracker_page']==1):
        st.session_state['tracker_page'] = 1; st.rerun()
    if bn2.button("◀ Prev",  key="tr_prev_b",  disabled=st.session_state['tracker_page']==1):
        st.session_state['tracker_page'] -= 1; st.rerun()
    if bn3.button("Next ▶",  key="tr_next_b",  disabled=st.session_state['tracker_page']==total_pages):
        st.session_state['tracker_page'] += 1; st.rerun()
    if bn4.button("Last ⏭",  key="tr_last_b",  disabled=st.session_state['tracker_page']==total_pages):
        st.session_state['tracker_page'] = total_pages; st.rerun()
