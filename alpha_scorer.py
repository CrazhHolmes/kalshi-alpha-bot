# alpha_scorer.py
import os, json, requests, smtplib, textwrap
from email.message import EmailMessage

KALSHI_KEY = os.getenv("KALSHI_KEY")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECIPIENT   = os.getenv("RECIPIENT")

# Strip whitespace from API keys (prevents header errors)
if KALSHI_KEY:
    KALSHI_KEY = KALSHI_KEY.strip()
if CLAUDE_KEY:
    CLAUDE_KEY = CLAUDE_KEY.strip()
if EMAIL_PASS:
    EMAIL_PASS = EMAIL_PASS.strip()

# ------------------------------------------------------------------
# 1️⃣ Pull markets from Kalshi Demo
def fetch_markets():
    url = "https://demo-api.kalshi.co/trade-api/v2/markets"
    headers = {"Authorization": f"Bearer {KALSHI_KEY}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get("markets", [])

# 2️⃣ Simple alpha score
def alpha_score(mkt):
    price = mkt.get("current_price", 0.5)
    payout = mkt.get("payout", 1.0)
    volume = mkt.get("volume", 0)
    return (payout * volume) / (price + 0.01)

# 3️⃣ Ask Claude for 3-sentence research
def get_research(question):
    prompt = f"""Summarize the key facts, recent news and major risks for this prediction market question in three short sentences:\n\n"{question}"\n\nKeep it concise and neutral."""
    headers = {"x-api-key": CLAUDE_KEY,
               "Content-Type": "application/json",
               "anthropic-version": "2023-06-01"}
    payload = {"model": "claude-3-haiku-20240307",
               "max_tokens": 200,
               "temperature": 0.0,
               "messages": [{"role":"user","content":prompt}]}
    resp = requests.post("https://api.anthropic.com/v1/messages",
                         json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

# 4️⃣ Send email via Tutanota
def send_email(picks):
    msg = EmailMessage()
    msg["Subject"] = "🤑 Tonight's Kalshi Alpha Picks (Demo)"
    msg["From"]    = EMAIL_USER
    msg["To"]      = RECIPIENT

    body = "Here are the three contracts the bot thinks are most mis-priced:\n\n"
    for i, (mkt, score) in enumerate(picks, 1):
        q   = mkt["question"]
        slug = mkt.get("slug", "")
        url = f"https://demo.kalshi.co/market/{slug}"
        price = mkt.get("current_price", 0)
        payout = mkt.get("payout", 1.0)
        research = get_research(q)
        body += f"""
{i}. {q}
   • Current price: ${price:.2f}
   • Payout if correct: ${payout:.2f}
   • Alpha score: {score:.2f}
   • Research: {research}
   • Link: {url}
"""
    msg.set_content(body)

    with smtplib.SMTP("smtp.tutanota.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

# ------------------------------------------------------------------
if __name__ == "__main__":
    markets = fetch_markets()
    scored   = [(m, alpha_score(m)) for m in markets]
    scored.sort(key=lambda x: x[1], reverse=True)
    top3 = scored[:3]
    send_email(top3)
