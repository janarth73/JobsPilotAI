import smtplib, yaml, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_cfg():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    with open(path) as f:
        return yaml.safe_load(f).get('email', {})

def send_digest(jobs):
    cfg = load_cfg()
    if not cfg.get('sender_email') or not cfg.get('sender_password'):
        return False, "Email not configured"
    try:
        rows = ''.join(f"""<tr>
          <td style="padding:8px;border-bottom:1px solid #eee">{j.get('title','')} — {j.get('company','')}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:center">{int(j.get('match_score',0)*100)}%</td>
          <td style="padding:8px;border-bottom:1px solid #eee"><a href="{j.get('apply_url','#')}">Apply</a></td>
        </tr>""" for j in jobs)
        html = f"""<html><body style="font-family:sans-serif;max-width:700px;margin:auto">
          <h2 style="color:#1d4ed8">New Job Matches ({len(jobs)})</h2>
          <table width="100%" cellspacing="0" style="border-collapse:collapse">
            <tr style="background:#f3f4f6"><th align="left" style="padding:8px">Job</th>
            <th style="padding:8px">Match</th><th align="left" style="padding:8px">Link</th></tr>
            {rows}
          </table></body></html>"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Job Alert: {len(jobs)} new matches found"
        msg['From'] = cfg['sender_email']
        msg['To'] = cfg['recipient_email']
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port']) as s:
            s.starttls()
            s.login(cfg['sender_email'], cfg['sender_password'])
            s.sendmail(cfg['sender_email'], cfg['recipient_email'], msg.as_string())
        return True, "Sent"
    except Exception as e:
        return False, str(e)
