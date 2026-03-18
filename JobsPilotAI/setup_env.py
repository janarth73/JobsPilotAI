"""
Run this script once to create your .env file securely.
Usage: python setup_env.py
"""
import os

ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')

def create_env():
    print("\n" + "="*50)
    print("  JobScraper Pro — Secure API Key Setup")
    print("="*50)

    if os.path.exists(ENV_PATH):
        print("\n.env file already exists!")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Cancelled.")
            return

    print("\nPaste your API keys below.")
    print("Press Enter to skip any key.\n")

    jsearch_key = input("JSearch API Key (from rapidapi.com): ").strip()
    groq_key    = input("Groq API Key (from console.groq.com): ").strip()

    lines = [
        "# JobScraper Pro — API Keys",
        "# DO NOT share this file or upload to GitHub",
        "",
    ]
    if jsearch_key:
        lines.append(f"JSEARCH_API_KEY={jsearch_key}")
    if groq_key:
        lines.append(f"GROQ_API_KEY={groq_key}")

    with open(ENV_PATH, 'w') as f:
        f.write('\n'.join(lines))

    print(f"\n✅ .env file created at: {ENV_PATH}")
    print("✅ Your keys are now stored securely.")
    print("\n⚠️  Never share .env or upload it to GitHub!")
    print("="*50)

if __name__ == '__main__':
    create_env()
