import streamlit as st
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_KEY_FILE = os.path.join(ROOT, '.groq_key')
ENV_PATH      = os.path.join(ROOT, '.env')

def save_groq_key(key):
    with open(GROQ_KEY_FILE, 'w') as f:
        f.write(key.strip())

def load_groq_key():
    # Priority 1: .groq_key file
    if os.path.exists(GROQ_KEY_FILE):
        key = open(GROQ_KEY_FILE).read().strip()
        if key: return key
    # Priority 2: .env file
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
        key = os.getenv('GROQ_API_KEY', '')
        if key: return key
    except Exception:
        pass
    return ''

def show():
    st.title("📄 Resume & AI Tailor")
    st.caption("Upload your resume · Analyze job matches · Tailor with AI · Generate cover letters")

    # Load Groq key silently from .env or .groq_key file
    saved_key = load_groq_key()
    if not st.session_state.get('groq_key'):
        st.session_state['groq_key'] = saved_key

    if not saved_key:
        st.warning("⚠️ Groq API key not found. Add GROQ_API_KEY to your .env file.")

    st.divider()

    # ── STEP 2: Upload Resume ─────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### Step 1 — Upload Resume")
        st.caption("Supports PDF and DOCX (Word) files")

        uploaded = st.file_uploader("Upload Resume",
            type=["pdf", "docx"],
            help="Upload as PDF or Word .docx",
            label_visibility="collapsed")

        if uploaded:
            ext = uploaded.name.lower().split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            with st.spinner(f"Parsing {ext.upper()} resume..."):
                from processor.matcher import parse_resume
                result = parse_resume(tmp_path)
            os.unlink(tmp_path)

            if result.get('error'):
                st.error(f"Failed to parse: {result['error']}")
            else:
                st.session_state['resume'] = result
                st.session_state['candidate_name'] = (
                    uploaded.name
                    .replace('.pdf','').replace('.docx','')
                    .replace('_',' ').replace('-',' ').title()
                )
                st.success(f"✅ Parsed — {result['word_count']} words from {ext.upper()}")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Detected Skills**")
                    skills = result.get('skills', [])
                    if skills:
                        st.write(", ".join([f"`{s}`" for s in skills]))
                    else:
                        st.info("No standard skills detected.")
                with c2:
                    st.markdown("**Text Preview**")
                    st.text_area("preview", result['text'][:800], height=160,
                                 label_visibility="collapsed")

        elif st.session_state.get('resume'):
            r = st.session_state['resume']
            st.success(f"✅ Resume loaded — {r.get('word_count',0)} words")
            skills = r.get('skills', [])
            if skills:
                st.write(", ".join([f"`{s}`" for s in skills]))
            st.caption("Upload a new file to replace.")
        else:
            st.info("👆 Upload your PDF or DOCX resume above.")

    st.divider()

    # ── RESCORE ───────────────────────────────────────────────────────────
    resume = st.session_state.get('resume')
    with st.container(border=True):
        st.markdown("#### 🔄 Rescore All Jobs")
        st.caption("Recalculates match % for every job using your resume")
        if resume:
            rc1, rc2, rc3 = st.columns([3, 1, 1])
            rc1.markdown(f"Resume: **{resume.get('word_count',0)} words** · **{len(resume.get('skills',[]))} skills**")
            with rc2:
                if st.button("🔄 Rescore Now", type="primary", key="rescore_btn"):
                    from db.models import get_session, Job
                    from processor.matcher import score_match
                    with st.spinner("Rescoring..."):
                        s    = get_session()
                        jobs = s.query(Job).all()
                        for j in jobs:
                            j.match_score = score_match(
                                resume['text'], j.description or '', j.skills or '')
                        s.commit(); s.close()
                    st.success(f"✅ Rescored {len(jobs)} jobs!")
            with rc3:
                try:
                    from db.models import get_session, Job
                    from sqlalchemy import func
                    s     = get_session()
                    total = s.query(func.count(Job.id)).scalar() or 0
                    s.close()
                    st.metric("Jobs in DB", total)
                except Exception:
                    pass
        else:
            st.warning("Upload your resume first.")

    st.divider()

    # ── STEP 3: Select Job ────────────────────────────────────────────────
    groq_key = st.session_state.get('groq_key', '')

    with st.container(border=True):
        st.markdown("#### Step 2 — Select Job & AI Actions")

        if not resume:
            st.warning("⚠️ Upload your resume in Step 1 first."); return
        if not groq_key:
            st.warning("⚠️ Groq API key not configured. Add GROQ_API_KEY to your .env file."); return

        from db.models import get_session, Job
        session = get_session()
        jobs    = session.query(Job).order_by(Job.match_score.desc()).limit(100).all()
        session.close()

        if not jobs:
            st.warning("No jobs yet. Go to 🔍 Scrape Jobs first."); return

        job_options    = {
            f"{j.title} @ {j.company} [{j.source}]  —  {int(j.match_score*100)}% match": j
            for j in jobs
        }
        selected_label = st.selectbox("Select job:", list(job_options.keys()))
        selected_job   = job_options[selected_label]
        st.session_state['_selected_job_label'] = selected_label

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Match", f"{int(selected_job.match_score*100)}%")
        c2.metric("Company",       (selected_job.company or "—")[:20])
        c3.metric("Source",        (selected_job.source or "—").capitalize())

        if selected_job.description:
            with st.expander("📋 View Job Description"):
                st.write(selected_job.description[:2000])
        else:
            st.warning("This job has no description — AI tailoring may be less accurate.")

    st.markdown("---")

    # ── AI Action Buttons ─────────────────────────────────────────────────
    if not resume or not groq_key: return

    from db.models import get_session, Job
    session  = get_session()
    jobs     = session.query(Job).order_by(Job.match_score.desc()).limit(100).all()
    session.close()
    if not jobs: return

    job_options  = {
        f"{j.title} @ {j.company} [{j.source}]  —  {int(j.match_score*100)}% match": j
        for j in jobs
    }
    sel_label    = st.session_state.get('_selected_job_label', list(job_options.keys())[0])
    selected_job = job_options.get(sel_label, list(job_options.values())[0])

    b1, b2, b3, b4 = st.columns(4)

    if b1.button("🔍 Analyze Match", key="analyze_btn"):
        with st.spinner("AI analyzing your match..."):
            try:
                from processor.ai_tailor import analyze_match, set_key
                set_key(groq_key)
                result = analyze_match(
                    resume['text'],
                    selected_job.description or selected_job.title,
                    selected_job.skills or ''
                )
                st.session_state['last_analysis'] = result
                st.session_state.pop('tailored_resume', None)
                st.session_state.pop('cover_letter', None)
                st.session_state.pop('interview_prep', None)
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    if b2.button("✨ Tailor Resume", type="primary", key="tailor_btn"):
        with st.spinner("AI tailoring your resume (~20 seconds)..."):
            try:
                from processor.ai_tailor import tailor_resume, set_key
                set_key(groq_key)
                tailored = tailor_resume(
                    resume['text'],
                    selected_job.title or '',
                    selected_job.company or '',
                    selected_job.description or selected_job.title,
                    selected_job.skills or ''
                )
                st.session_state['tailored_resume']  = tailored
                st.session_state['tailored_for_job'] = selected_job
                st.session_state.pop('last_analysis', None)
                st.session_state.pop('cover_letter', None)
                st.session_state.pop('interview_prep', None)
                st.success("✅ Resume tailored!")
            except Exception as e:
                st.error(f"Tailoring failed: {e}")

    if b3.button("📝 Cover Letter", key="cover_btn"):
        with st.spinner("Writing cover letter..."):
            try:
                from processor.ai_tailor import generate_cover_letter, set_key
                set_key(groq_key)
                letter = generate_cover_letter(
                    resume['text'],
                    selected_job.title or '',
                    selected_job.company or '',
                    selected_job.description or ''
                )
                st.session_state['cover_letter']     = letter
                st.session_state['cover_letter_job'] = selected_job
                st.session_state.pop('last_analysis', None)
                st.session_state.pop('tailored_resume', None)
                st.session_state.pop('interview_prep', None)
            except Exception as e:
                st.error(f"Cover letter failed: {e}")

    if b4.button("🎯 Interview Prep", key="interview_btn"):
        with st.spinner("Preparing interview guide..."):
            try:
                from processor.ai_tailor import generate_interview_prep, set_key
                set_key(groq_key)
                prep = generate_interview_prep(
                    resume['text'],
                    selected_job.title or '',
                    selected_job.company or '',
                    selected_job.description or ''
                )
                st.session_state['interview_prep']     = prep
                st.session_state['interview_prep_job'] = selected_job
                st.session_state.pop('last_analysis', None)
                st.session_state.pop('tailored_resume', None)
                st.session_state.pop('cover_letter', None)
            except Exception as e:
                st.error(f"Interview prep failed: {e}")

    # ── Analysis Output ───────────────────────────────────────────────────
    if st.session_state.get('last_analysis'):
        analysis = st.session_state['last_analysis']
        st.divider()
        st.markdown("### 🔍 Match Analysis")

        score     = analysis.get('match_score', 0)
        ats_score = analysis.get('ats_score', 0)
        color     = "green" if score >= 70 else "orange" if score >= 40 else "red"

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Overall Match",   f"{score}%")
        mc2.metric("ATS Score",       f"{ats_score}%")
        mc3.metric("Keyword Density", analysis.get('keyword_density','—').title())

        rec = analysis.get('recommendation','')
        if "Strong" in rec:
            st.success(f"✅ {rec}")
        elif "Good" in rec:
            st.info(f"💡 {rec}")
        elif "Weak" in rec:
            st.warning(f"⚠️ {rec}")
        else:
            st.error(f"❌ {rec}")

        a1, a2 = st.columns(2)
        with a1:
            st.markdown("**✅ Matching Skills**")
            for s in analysis.get('matching_skills', []): st.markdown(f"- {s}")
            st.markdown("**⭐ Strengths**")
            for s in analysis.get('strengths', []):       st.markdown(f"- {s}")
            st.markdown("**🎯 Matching Experience**")
            for s in analysis.get('matching_experience', []): st.markdown(f"- {s}")
        with a2:
            st.markdown("**❌ Missing Skills**")
            for s in analysis.get('missing_skills', []):  st.markdown(f"- {s}")
            st.markdown("**⚠️ Gaps**")
            for g in analysis.get('gaps', []):             st.markdown(f"- {g}")
            st.markdown("**⚡ Quick Wins**")
            for q in analysis.get('quick_wins', []):       st.markdown(f"- {q}")

    # ── Tailored Resume Output ────────────────────────────────────────────
    if st.session_state.get('tailored_resume'):
        tailored = st.session_state['tailored_resume']
        job      = st.session_state.get('tailored_for_job')
        st.divider()
        st.markdown(f"### ✨ Tailored Resume — {job.company if job else ''}")

        if tailored.get('match_improvements'):
            st.info(f"**What AI improved:** {tailored['match_improvements']}")
        if tailored.get('keywords_added'):
            kw_pills = " ".join([
                f'<span style="background:#1e3a5f;color:#60a5fa;padding:2px 8px;'
                f'border-radius:20px;font-size:11px">{k}</span>'
                for k in tailored['keywords_added']
            ])
            st.markdown(f"**Keywords added:** {kw_pills}", unsafe_allow_html=True)

        with st.expander("👁 Preview Tailored Resume", expanded=True):
            if tailored.get('summary'):
                st.markdown("**📋 Professional Summary**")
                st.info(tailored['summary'])
            if tailored.get('skills'):
                st.markdown("**🛠 Skills**")
                st.write("  •  ".join(tailored['skills']))
            for exp in tailored.get('experience', []):
                st.markdown(f"**💼 {exp.get('title','')} @ {exp.get('company','')}**")
                st.caption(exp.get('duration',''))
                for b in exp.get('bullets', []): st.markdown(f"- {b}")
            for edu in tailored.get('education', []):
                st.markdown(f"**🎓 {edu.get('degree','')}** — {edu.get('institution','')} {edu.get('year','')}")

        candidate_name = st.session_state.get('candidate_name', 'Candidate')
        job_slug       = (job.company or 'job').replace(' ','_') if job else 'job'
        d1, d2         = st.columns(2)
        with d1:
            try:
                from processor.resume_builder import build_docx
                st.download_button(
                    "⬇️ Download DOCX",
                    data=build_docx(tailored, candidate_name),
                    file_name=f"resume_{job_slug}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=False)
            except Exception as e:
                st.warning(f"DOCX error: {e}")
        with d2:
            try:
                from processor.resume_builder import build_pdf
                pdf_data = build_pdf(tailored, candidate_name)
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_data,
                    file_name=f"resume_{job_slug}.pdf",
                    mime="application/pdf",
                    use_container_width=False)
            except Exception as e:
                st.warning(f"PDF error: {e}. Install with: pip install fpdf2")

    # ── Cover Letter Output ───────────────────────────────────────────────
    if st.session_state.get('cover_letter'):
        job    = st.session_state.get('cover_letter_job')
        letter = st.session_state['cover_letter']
        st.divider()
        st.markdown("### 📝 Cover Letter")
        st.text_area("", letter, height=300, label_visibility="collapsed")
        st.download_button(
            "⬇️ Download Cover Letter (.txt)",
            data=letter,
            file_name=f"cover_letter_{(job.company or 'job').replace(' ','_') if job else 'job'}.txt",
            mime="text/plain")

    # ── Interview Prep Output ─────────────────────────────────────────────
    if st.session_state.get('interview_prep'):
        prep = st.session_state['interview_prep']
        job  = st.session_state.get('interview_prep_job')
        st.divider()
        st.markdown(f"### 🎯 Interview Prep — {job.company if job else ''}")

        tab1, tab2, tab3, tab4 = st.tabs(["❓ Questions", "📚 Topics", "🤔 Ask Them", "🏢 Research"])

        with tab1:
            for q in prep.get('likely_questions', []):
                with st.expander(f"❓ {q.get('question','')}"):
                    st.markdown("**Suggested Answer:**")
                    st.info(q.get('suggested_answer',''))
                    st.caption(f"💡 Interviewer assesses: {q.get('tips','')}")

        with tab2:
            st.markdown("**Technical topics to revise:**")
            for t in prep.get('technical_topics', []):
                st.markdown(f"- 📖 {t}")

        with tab3:
            st.markdown("**Smart questions to ask the interviewer:**")
            for q in prep.get('questions_to_ask', []):
                st.markdown(f"- 💬 {q}")

        with tab4:
            st.markdown("**Company research points:**")
            for r in prep.get('company_research', []):
                st.markdown(f"- 🏢 {r}")
            if prep.get('salary_insight'):
                st.divider()
                st.markdown("**💰 Salary negotiation tip:**")
                st.info(prep['salary_insight'])
