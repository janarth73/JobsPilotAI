import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="JobScraper Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Auth check ─────────────────────────────────────────────────────────────
from auth import is_logged_in, show_login_page, logout, is_admin, check_page_access

if not is_logged_in():
    show_login_page()
    st.stop()

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}

#MainMenu,footer,header{visibility:hidden!important;display:none!important}
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
[data-testid="stSidebarNav"],[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"],[data-testid="stSidebar"]{display:none!important}

[data-testid="stAppViewContainer"]{background:#0d1117!important}
.block-container{padding:0!important;max-width:100%!important;background:#0d1117!important}

[data-testid="stMetric"]{background:#111827!important;border:1px solid #1f2937!important;border-radius:10px!important;padding:14px!important}
[data-testid="stMetricLabel"] p{color:#6b7280!important;font-size:11px!important;text-transform:uppercase}
[data-testid="stMetricValue"]{color:#f9fafb!important;font-size:26px!important;font-weight:700!important}
[data-testid="stMetricDelta"] *{font-size:11px!important}

.stButton>button{background:#1e3a5f!important;color:#60a5fa!important;border:1px solid #2563eb!important;border-radius:8px!important;font-size:13px!important;font-weight:500!important}
.stButton>button:hover{background:#2563eb!important;color:#fff!important}
.stButton>button[kind="primary"]{background:#2563eb!important;color:#fff!important;border-color:#2563eb!important}
.stButton>button[kind="primary"]:hover{background:#1d4ed8!important}

.stTextInput input,.stTextArea textarea{background:#1f2937!important;color:#f3f4f6!important;border:1px solid #374151!important;border-radius:8px!important}
.stSelectbox>div>div,.stMultiSelect>div>div{background:#1f2937!important;border:1px solid #374151!important;border-radius:8px!important;color:#f3f4f6!important}
.stCheckbox label{color:#d1d5db!important;font-size:13px!important}
[data-testid="stFileUploader"]{background:#1f2937!important;border:1px dashed #374151!important;border-radius:10px!important}
[data-testid="stDownloadButton"] button{background:#1e3a5f!important;color:#60a5fa!important;border:1px solid #2563eb!important}
div[data-testid="stForm"]{background:#111827!important;border:1px solid #1f2937!important;border-radius:12px!important;padding:16px!important}
[data-testid="stExpander"]{background:#111827!important;border:1px solid #1f2937!important;border-radius:10px!important}
[data-testid="stExpander"] summary{color:#d1d5db!important}
[data-testid="stAlert"]{background:#1f2937!important;border:1px solid #374151!important;color:#d1d5db!important;border-radius:10px!important}
[data-testid="stDataFrame"]{border-radius:10px!important;border:1px solid #1f2937!important}
[data-testid="stSlider"]>div>div{background:#374151!important}
[data-testid="stTabs"] [data-baseweb="tab"]{color:#9ca3af!important}
[data-testid="stTabs"] [aria-selected="true"]{color:#60a5fa!important;border-bottom-color:#60a5fa!important}

h1,h2,h3{color:#f9fafb!important}
p,li{color:#d1d5db!important}
hr{border-color:#1f2937!important}
.stMarkdown p{color:#d1d5db!important}

.job-table-wrap{background:#111827;border:1px solid #1f2937;border-radius:12px;overflow:hidden;margin-bottom:20px}
.job-table-header{display:grid;grid-template-columns:2fr 1.2fr 1fr 1.2fr 1fr;padding:10px 20px;border-bottom:1px solid #1f2937}
.job-table-header span{font-size:11px;font-weight:600;color:#4b5563;text-transform:uppercase;letter-spacing:.08em}
.job-row{display:grid;grid-template-columns:2fr 1.2fr 1fr 1.2fr 1fr;padding:14px 20px;border-bottom:1px solid #1a2332;align-items:center;transition:background .1s}
.job-row:last-child{border-bottom:none}
.job-row:hover{background:#1a2332}
.job-title{font-size:14px;font-weight:500;color:#f3f4f6}
.job-company{font-size:13px;color:#9ca3af}
.platform-badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500}
.pb-linkedin{background:#1e3a5f;color:#60a5fa}
.pb-naukri{background:#3b2500;color:#fb923c}
.pb-indeed{background:#1a3320;color:#4ade80}
.pb-jsearch{background:#1e3a30;color:#34d399}
.pb-remoteok{background:#2d1b69;color:#a78bfa}
.pb-glassdoor{background:#1e3a2a;color:#6ee7b7}
.match-wrap{display:flex;align-items:center;gap:10px}
.match-bar-bg{width:60px;height:4px;background:#374151;border-radius:2px;overflow:hidden}
.match-bar-fill{height:4px;border-radius:2px}
.match-pct{font-size:13px;font-weight:600}
.pct-green{color:#4ade80}.pct-yellow{color:#fbbf24}.pct-red{color:#f87171}
.apply-btn{background:#1e3a5f;color:#60a5fa;border:1px solid #2563eb;border-radius:7px;padding:5px 14px;font-size:12px;font-weight:500;cursor:pointer}
.apply-btn:hover{background:#2563eb;color:#fff}
.chart-card{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:20px}
.chart-title{font-size:15px;font-weight:600;color:#f3f4f6;margin-bottom:16px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.bar-lbl{width:80px;font-size:12px;color:#6b7280;text-align:right;flex-shrink:0}
.bar-track{flex:1;height:16px;background:#1f2937;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px}
.bar-val{width:28px;font-size:11px;color:#9ca3af;text-align:right}
.pipeline-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1f2937;font-size:13px}
.pipeline-row:last-child{border-bottom:none}
.pip-dot{width:8px;height:8px;border-radius:50%;margin-right:10px;flex-shrink:0}
.pip-left{display:flex;align-items:center;color:#d1d5db}
.pip-val{font-weight:600;color:#f9fafb;font-size:14px}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "dashboard"

PAGES = [
    ("dashboard", "🔷", "Dashboard"),
    ("scrape",    "🔍", "Scrape Jobs"),
    ("resume",    "📄", "Resume & AI"),
    ("apply",     "🚀", "Apply Jobs"),
    ("tracker",   "📊", "Tracker"),
    ("settings",  "⚙️", "Settings"),
]

# ── Live stats ─────────────────────────────────────────────────────────────
try:
    from db.models import get_session, Job
    from sqlalchemy import func
    s       = get_session()
    total   = s.query(func.count(Job.id)).scalar() or 0
    applied = s.query(func.count(Job.id)).filter(Job.is_applied == True).scalar() or 0
    s.close()
except Exception:
    total = applied = 0

# ── Top Navbar ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#0d1117;border-bottom:1px solid #1f2937;
display:flex;align-items:center;padding:0 20px;height:52px;
position:sticky;top:0;z-index:999;gap:8px">
  <div style="font-size:15px;font-weight:700;color:#60a5fa;
  margin-right:24px;white-space:nowrap">💼 JobScraper Pro</div>
</div>
""", unsafe_allow_html=True)

# Nav buttons
nav_cols = st.columns(len(PAGES) + 3)
for i, (key, icon, label) in enumerate(PAGES):
    # Hide Settings for non-admins
    if key == "settings" and not is_admin():
        continue
    with nav_cols[i]:
        active = st.session_state["active_page"] == key
        if st.button(f"{icon} {label}", key=f"nav_{key}",
                     type="primary" if active else "secondary"):
            st.session_state["active_page"] = key
            st.rerun()

# User info + logout on right
with nav_cols[len(PAGES)]:
    username = st.session_state.get("username","")
    role     = st.session_state.get("role","")
    badge    = "👑 Admin" if role == "admin" else "👤 User"
    st.markdown(f"""
<div style="text-align:right;font-size:11px;color:#6b7280;padding-top:6px">
  {badge}<br><b style="color:#9ca3af">{username}</b>
</div>""", unsafe_allow_html=True)

with nav_cols[len(PAGES)+1]:
    if st.button("🚪 Logout", key="logout_btn"):
        logout()
        st.rerun()

with nav_cols[len(PAGES)+2]:
    if st.button("➕ Scrape", key="quick_scrape", type="primary"):
        st.session_state["active_page"] = "scrape"
        st.rerun()

st.markdown("<hr style='border-color:#1f2937;margin:0 0 20px 0'>", unsafe_allow_html=True)

# ── Page routing ───────────────────────────────────────────────────────────
current = st.session_state.get("active_page", "dashboard")

# Block non-admins from settings
if not check_page_access(current):
    st.stop()

if   current == "dashboard": from pages.dashboard import show; show()
elif current == "scrape":    from pages.scrape    import show; show()
elif current == "resume":    from pages.resume    import show; show()
elif current == "apply":     from pages.apply     import show; show()
elif current == "tracker":   from pages.tracker   import show; show()
elif current == "settings":  from pages.settings  import show; show()
