# alpha_scorer.py
import os, json, requests, smtplib, textwrap
from email.message import EmailMessage

KALSHI_KEY = os.getenv("KALSHI_KEY")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECIPIENT   = os.getenv("RECIPIENT")

# Strip whitespace
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
    markets = data.get("markets", [])
    print(f"DEBUG: Found {len(markets)} markets")
    return markets

# 2️⃣ Simple alpha score
def alpha_score(mkt):
    price = mkt.get("last_price", 0.5)  # Demo API uses "last_price"
    payout = 1.0
    volume = mkt.get("volume", 0)
    return (payout * volume) / (price + 0.01)

# 3️⃣ Ask Claude for 3-sentence research
def get_research(question):
    prompt = f"""Summarize the key facts, recent news and major risks for this prediction market question in three short sentences: "{question}" """
    
    headers = {
        "x-api-key": CLAUDE_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "haiku-3-20250514",
        "max_tokens": 150,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    print(f"DEBUG: Sending to Claude (key starts with {CLAUDE_KEY[:10]}...)")
    
    resp = requests.post("https://api.anthropic.com/v1/messages",
                         json=payload, headers=headers)
    
    print(f"DEBUG: Claude response status = {resp.status_code}")
    print(f"DEBUG: Claude response body = {resp.text[:300]}")
    
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
        q = mkt.get("title", "Unknown market")
        slug = mkt.get("ticker", mkt.get("event_ticker", ""))
        url = f"https://demo.kalshi.co/market/{slug}"
        price = mkt.get("last_price", 0)
        
        try:
            research = get_research(q)
        except Exception as e:
            research = f"Error getting research: {e}"
        
        body += f"""
{i}. {q}
   • Current price: ${price:.2f}
   • Payout if correct: $1.00
   • Alpha score: {score:.2f}
   • Research: {research}
   • Link: {url}
"""
    msg.set_content(body)

    print(f"DEBUG: Sending email to {RECIPIENT}")
    with smtplib.SMTP("smtp.tutanota.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
    print(f"DEBUG: Email sent!")

# ------------------------------------------------------------------
if __name__ == "__main__":
    try:
        markets = fetch_markets()
        scored = [(m, alpha_score(m)) for m in markets]
        scored.sort(key=lambda x: x[1], reverse=True)
        top3 = scored[:3]
        print(f"DEBUG: Top 3 selected")
        send_email(top3)
        print("DEBUG: All done!")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
