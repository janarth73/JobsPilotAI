"""
Simple authentication system for JobScraper Pro.
Credentials stored in .env file — no database needed.
"""
import streamlit as st
import os, hashlib, time
from dotenv import load_dotenv

ROOT = os.path.dirname(__file__)
load_dotenv(os.path.join(ROOT, '.env'))

# ── Load credentials from .env ─────────────────────────────────────────────
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_HASH = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()

# Extra users (comma separated in .env)
# EXTRA_USERS=john:pass123,jane:pass456
EXTRA_USERS = {}
extra_raw = os.getenv("EXTRA_USERS", "")
if extra_raw:
    for pair in extra_raw.split(","):
        if ":" in pair:
            u, p = pair.strip().split(":", 1)
            EXTRA_USERS[u.strip()] = hashlib.sha256(p.strip().encode()).hexdigest()

# Admin-only pages
ADMIN_ONLY_PAGES = ["settings"]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    ph = hash_password(password)
    if username == ADMIN_USER and ph == ADMIN_HASH:
        return "admin"
    if username in EXTRA_USERS and ph == EXTRA_USERS[username]:
        return "user"
    return None

def is_admin():
    return st.session_state.get("role") == "admin"

def is_logged_in():
    return st.session_state.get("logged_in", False)

def logout():
    st.session_state["logged_in"]   = False
    st.session_state["username"]    = ""
    st.session_state["role"]        = ""
    st.session_state["active_page"] = "dashboard"

def show_login_page():
    """Render the login page."""
    st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0d1117!important}
.block-container{padding:0!important;max-width:100%!important;background:#0d1117!important}
#MainMenu,footer,header{display:none!important}
[data-testid="stToolbar"],[data-testid="stSidebarNav"]{display:none!important}
</style>
""", unsafe_allow_html=True)

    # Center card
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
<div style="margin-top:60px;text-align:center;margin-bottom:32px">
  <div style="font-size:42px;font-weight:800;color:#60a5fa;line-height:1.1">
    💼 JobScraper<br>Pro
  </div>
  <div style="font-size:14px;color:#6b7280;margin-top:8px">
    AI-Powered Job Hunter
  </div>
</div>
""", unsafe_allow_html=True)

        with st.form("login_form"):
                st.markdown("#### Welcome back")
                username  = st.text_input("Username", placeholder="Enter username")
                password  = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("🔐 Login", type="primary", use_container_width=False)

                if submitted:
                    if not username or not password:
                        st.error("Please enter username and password.")
                    else:
                        role = verify_user(username, password)
                        if role:
                            st.session_state["logged_in"]   = True
                            st.session_state["username"]    = username
                            st.session_state["role"]        = role
                            st.session_state["active_page"] = "dashboard"
                            st.success(f"Welcome back, {username}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

        st.markdown("""
<div style="text-align:center;margin-top:24px;font-size:12px;color:#374151">
  Secure local authentication · Data stays on your machine
</div>
""", unsafe_allow_html=True)

def check_page_access(page_key):
    """Returns True if current user can access this page."""
    if page_key in ADMIN_ONLY_PAGES and not is_admin():
        st.warning("⚠️ This page is for admins only.")
        st.info("Contact your admin for access.")
        return False
    return True
