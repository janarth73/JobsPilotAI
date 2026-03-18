import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import get_session, Job
from sqlalchemy import func

def get_badge(source):
    badges = {
        "linkedin":      ("pb-linkedin",  "LinkedIn"),
        "indeed":        ("pb-indeed",    "Indeed"),
        "glassdoor":     ("pb-glassdoor", "Glassdoor"),
        "naukri":        ("pb-naukri",    "Naukri"),
        "remoteok":      ("pb-remoteok",  "RemoteOK"),
        "jsearch":       ("pb-jsearch",   "JSearch"),
        "weworkremotely":("pb-remoteok",  "WeWork"),
    }
    cls, label = badges.get(source or '', ("pb-jsearch", source or "—"))
    return f'<span class="platform-badge {cls}">{label}</span>'

def get_match_html(score):
    pct  = int(score * 100)
    if pct >= 70:
        color = "#4ade80"; cls = "pct-green";  bar_color = "#4ade80"
    elif pct >= 40:
        color = "#fbbf24"; cls = "pct-yellow"; bar_color = "#fbbf24"
    else:
        color = "#f87171"; cls = "pct-red";    bar_color = "#f87171"
    width = pct
    return f"""
<div class="match-wrap">
  <div class="match-bar-bg">
    <div class="match-bar-fill" style="width:{width}%;background:{bar_color}"></div>
  </div>
  <span class="match-pct {cls}">{pct}%</span>
</div>"""

def show():
    s = get_session()
    total     = s.query(func.count(Job.id)).scalar() or 0
    applied   = s.query(func.count(Job.id)).filter(Job.is_applied == True).scalar() or 0
    new_jobs  = s.query(func.count(Job.id)).filter(Job.status == 'new').scalar() or 0
    interview = s.query(func.count(Job.id)).filter(Job.status == 'interview').scalar() or 0
    top_jobs  = s.query(Job).filter(Job.is_applied == False)\
                 .order_by(Job.match_score.desc()).limit(8).all()
    sources   = s.query(Job.source, func.count(Job.id)).group_by(Job.source).all()
    pipeline  = [
        ("New",          "#6b7280", new_jobs),
        ("Applied",      "#3b82f6", applied),
        ("Under Review", "#f59e0b", s.query(func.count(Job.id)).filter(Job.status=='under_review').scalar() or 0),
        ("Interview",    "#8b5cf6", interview),
        ("Offer",        "#4ade80", s.query(func.count(Job.id)).filter(Job.status=='offer').scalar() or 0),
        ("Rejected",     "#ef4444", s.query(func.count(Job.id)).filter(Job.status=='rejected').scalar() or 0),
    ]
    jobstatus=pipeline
    s.close()

    # ── Header ─────────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([4, 1])
    with hc1:
        st.markdown("""
<div style="margin-bottom:20px">
  <h1 style="font-size:26px;font-weight:700;color:#f9fafb;margin:0 0 4px 0">Dashboard</h1>
  <p style="font-size:13px;color:#6b7280;margin:0">Overview of your job search</p>
</div>""", unsafe_allow_html=True)


    # ── Metrics ────────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Scraped", total,    delta="+34 today")
    m2.metric("Applied",       applied,  delta="3 this week")
    m3.metric("Interviews",    interview,delta="+1 new" if interview else None)
    m4.metric("New Jobs",      new_jobs)

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Job Table ──────────────────────────────────────────────────────────
    if top_jobs:
        rows_html = ""
        for job in top_jobs:
            badge   = get_badge(job.source)
            match   = get_match_html(job.match_score)
            btn     = f'<button class="apply-btn" onclick="">Apply</button>'
            rows_html += f"""
<div class="job-row">
  <div class="job-title">{job.title or '—'}</div>
  <div class="job-company">{job.company or '—'}</div>
  <div>{badge}</div>
  <div>{match}</div>
  <div>{btn}</div>
</div>"""

        st.markdown(f"""
<div class="job-table-wrap">
  <div class="job-table-header">
    <span>Title</span>
    <span>Company</span>
    <span>Platform</span>
    <span>Match</span>
    <span></span>
  </div>
  {rows_html}
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style="background:#111827;border:1px solid #1f2937;border-radius:12px;
padding:40px;text-align:center;color:#6b7280;margin-bottom:20px">
  No jobs yet — click <b style="color:#60a5fa">+ Scrape</b> to get started
</div>""", unsafe_allow_html=True)

    # ── Charts Row ─────────────────────────────────────────────────────────
    cc1, cc2 = st.columns(2)

    with cc1:
        src_colors = {
            "jsearch":        "#3b82f6",
            "naukri":         "#f97316",
            "remoteok":       "#8b5cf6",
            "indeed":         "#22c55e",
            "linkedin":       "#0ea5e9",
            "glassdoor":      "#10b981",
            "weworkremotely": "#6b7280",
        }
        max_count  = max((c for _, c in sources), default=1)
        bars_html  = ""
        for src, count in sorted(sources, key=lambda x: x[1], reverse=True):
            color = src_colors.get(src or '', "#6b7280")
            width = int((count / max_count) * 100)
            label = src.capitalize() if src else "Unknown"
            bars_html += f"""
<div class="bar-row">
  <span class="bar-lbl">{label}</span>
  <div class="bar-track">
    <div class="bar-fill" style="width:{width}%;background:{color}"></div>
  </div>
  <span class="bar-val">{count}</span>
</div>"""

        st.markdown(f"""
<div class="chart-card">
  <div class="chart-title">Jobs by Platform</div>
  {bars_html if bars_html else '<p style="color:#6b7280;font-size:13px">No data yet</p>'}
</div>""", unsafe_allow_html=True)

    with cc2:
        pip_colors = {
            "New":          "#6b7280",
            "Applied":      "#3b82f6",
            "Under Review": "#f59e0b",
            "Interview":    "#8b5cf6",
            "Offer":        "#4ade80",
            "Rejected":     "#ef4444",
        }
        pip_html = ""
        for label, color, count in pipeline:
            pip_html += f"""
<div class="pipeline-row">
  <span class="pip-left">
    <span class="pip-dot" style="background:{color}"></span>
    {label}
  </span>
  <span class="pip-val">{count}</span>
</div>"""

        st.markdown(f"""
<div class="chart-card">
  <div class="chart-title">Pipeline</div>
  {pip_html}
</div>""", unsafe_allow_html=True)
