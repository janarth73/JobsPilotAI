import requests, os, re, json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

def set_key(key: str):
    global GROQ_API_KEY
    GROQ_API_KEY = key.strip()

def _call_groq(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    key = GROQ_API_KEY
    if not key:
        raise ValueError(
            "Groq API key not found. "
            "Add GROQ_API_KEY=your_key to your .env file "
            "or paste it in the Resume & AI page."
        )
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model":       GROQ_MODEL,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": 0.3,
    }
    r = requests.post(GROQ_URL, headers=headers, json=body, timeout=45)
    if r.status_code == 401:
        raise ValueError("Invalid Groq API key — check your .env file")
    if r.status_code == 429:
        raise ValueError("Groq rate limit reached — wait a moment and try again")
    if r.status_code != 200:
        raise ValueError(f"Groq API error {r.status_code}: {r.text[:300]}")
    return r.json()['choices'][0]['message']['content'].strip()

def _parse_json(raw: str) -> dict:
    """Safely parse JSON from AI response."""
    raw = re.sub(r'```json|```', '', raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    raise ValueError("AI returned invalid JSON. Please try again.")

def tailor_resume(resume_text: str, job_title: str, company: str,
                  job_description: str, job_skills: str) -> dict:
    system = """You are a senior professional resume writer with 15 years of experience
helping candidates land jobs at top companies. Your task is to strategically tailor
a resume to perfectly match a specific job description.

CRITICAL RULES:
- NEVER invent or fabricate any experience, skills, or achievements
- ONLY use information that exists in the candidate's original resume
- Rewrite bullet points to use the job description's exact language and keywords
- Quantify achievements where numbers already exist in the resume
- Add missing keywords from the JD naturally within existing experience
- Make the summary laser-focused on this specific role
- Return ONLY valid JSON — absolutely no markdown, no explanation text"""

    prompt = f"""
ROLE: {job_title} at {company}

JOB DESCRIPTION:
{job_description[:3500]}

REQUIRED SKILLS FROM JD: {job_skills}

CANDIDATE'S ORIGINAL RESUME:
{resume_text[:3500]}

Now create a perfectly tailored resume. Analyze:
1. Which of the candidate's skills directly match the JD requirements
2. Which experience bullets can be reworded to echo the JD language
3. What keywords from the JD are missing and can be naturally added
4. What the hiring manager for THIS specific role cares about most

Return this exact JSON structure:
{{
  "summary": "A powerful 2-3 sentence professional summary that positions the candidate perfectly for {job_title} at {company}. Must mention the company name and key matching skills. Make it compelling and specific.",
  "skills": ["list", "of", "skills", "ordered", "by", "relevance", "to", "this", "job"],
  "experience": [
    {{
      "title": "Exact job title from resume",
      "company": "Exact company from resume",
      "duration": "Exact dates from resume",
      "bullets": [
        "Rewritten achievement bullet using {company}'s language and keywords — include metrics if available",
        "Another strong achievement bullet that maps to a JD requirement",
        "Third bullet showing impact relevant to this role"
      ]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University name",
      "year": "Graduation year"
    }}
  ],
  "keywords_added": ["keyword1 from JD", "keyword2 from JD", "keyword3"],
  "match_improvements": "2-3 sentences explaining specifically what was changed and why — mention the score improvement expected"
}}
"""
    raw     = _call_groq(prompt, system, max_tokens=3000)
    return _parse_json(raw)


def analyze_match(resume_text: str, job_description: str, job_skills: str) -> dict:
    system = """You are an expert ATS (Applicant Tracking System) analyst and career coach.
Analyze how well a resume matches a job description with deep insight.
Be specific, honest, and actionable. Return ONLY valid JSON."""

    prompt = f"""
Perform a deep ATS analysis of this resume against the job description.

JOB DESCRIPTION:
{job_description[:2500]}

REQUIRED SKILLS: {job_skills}

CANDIDATE RESUME:
{resume_text[:2500]}

Provide a thorough analysis. Return this exact JSON:
{{
  "match_score": <integer 0-100 based on skills overlap, experience relevance, keyword density>,
  "ats_score": <integer 0-100 based on keywords an ATS system would find>,
  "matching_skills": ["exact skills found in BOTH resume and JD"],
  "missing_skills": ["skills required by JD but NOT in resume"],
  "matching_experience": ["specific experience bullets that are highly relevant"],
  "strengths": ["3-4 specific strengths of this candidate for this role"],
  "gaps": ["2-3 specific gaps or weaknesses for this role"],
  "keyword_density": "<low/medium/high> — how many JD keywords appear in resume",
  "recommendation": "<one of: Strong Match — Apply Now / Good Match — Apply with Tailoring / Weak Match — Significant Gaps / Not Recommended>",
  "quick_wins": ["specific change 1 to improve score fast", "specific change 2", "specific change 3"]
}}
"""
    raw = _call_groq(prompt, system, max_tokens=1200)
    return _parse_json(raw)


def generate_cover_letter(resume_text: str, job_title: str,
                          company: str, job_description: str) -> str:
    system = """You are an expert cover letter writer who crafts compelling,
personalized cover letters that get candidates noticed. Your letters are:
- Specific to the company and role (never generic)
- Focused on value the candidate brings, not what they want
- Professional but warm in tone
- Under 300 words with strong opening and closing
- Free of clichés like 'I am writing to apply' or 'team player'"""

    prompt = f"""
Write a compelling cover letter for this application.

POSITION: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
{job_description[:2000]}

CANDIDATE BACKGROUND:
{resume_text[:2000]}

Write a 3-paragraph cover letter that:

Paragraph 1 (Hook): Open with something specific about {company} — their product,
mission, recent news, or why this role is exciting. Show you've done research.
Do NOT start with "I am writing to apply".

Paragraph 2 (Value): Pick 2-3 of the candidate's most relevant achievements that
directly match the JD requirements. Be specific — use numbers and impact if available.
Show how their background solves {company}'s specific needs.

Paragraph 3 (Close): Express genuine enthusiasm, reference next steps,
and end with a confident call to action.

Write ONLY the letter body — no subject line, no date, no address headers.
Keep it under 300 words. Make it sound human, not AI-generated.
"""
    return _call_groq(prompt, system, max_tokens=700)


def generate_interview_prep(resume_text: str, job_title: str,
                            company: str, job_description: str) -> dict:
    system = """You are an expert interview coach who helps candidates prepare
for job interviews. Provide specific, actionable preparation advice.
Return ONLY valid JSON."""

    prompt = f"""
Prepare interview questions and answers for:
ROLE: {job_title} at {company}
JD: {job_description[:2000]}
RESUME: {resume_text[:1500]}

Return this JSON:
{{
  "likely_questions": [
    {{
      "question": "Common interview question for this role",
      "suggested_answer": "STAR-format answer using candidate's background",
      "tips": "What the interviewer is really assessing"
    }}
  ],
  "technical_topics": ["topic1 to revise", "topic2", "topic3"],
  "questions_to_ask": ["Smart question to ask interviewer 1", "question 2", "question 3"],
  "company_research": ["Key thing to know about {company} 1", "key point 2"],
  "salary_insight": "Salary negotiation tip for this role level"
}}
"""
    raw = _call_groq(prompt, system, max_tokens=2000)
    return _parse_json(raw)
