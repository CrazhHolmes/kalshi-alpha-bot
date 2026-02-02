# alpha_scorer.py
import os, json, requests, smtplib
from email.message import EmailMessage

KALSHI_KEY = os.getenv("KALSHI_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
BREVO_SMTP_KEY = os.getenv("BREVO_SMTP_KEY")
RECIPIENT = os.getenv("RECIPIENT")

print(f"DEBUG: KALSHI_KEY = {KALSHI_KEY[:10] if KALSHI_KEY else 'None'}...")
print(f"DEBUG: HF_TOKEN = {HF_TOKEN[:10] if HF_TOKEN else 'None'}...")
print(f"DEBUG: BREVO_SMTP_KEY = {BREVO_SMTP_KEY[:20] if BREVO_SMTP_KEY else 'None'}...")
print(f"DEBUG: RECIPIENT = {RECIPIENT}")

if KALSHI_KEY:
    KALSHI_KEY = KALSHI_KEY.strip()

# ------------------------------------------------------------------
def fetch_markets():
    url = "https://demo-api.kalshi.co/trade-api/v2/markets"
    headers = {"Authorization": f"Bearer {KALSHI_KEY}"}
    markets = requests.get(url, headers=headers).json().get("markets", [])
    print(f"DEBUG: Found {len(markets)} markets")
    return markets

def alpha_score(mkt):
    price = mkt.get("last_price", 0.5)
    volume = mkt.get("volume", 0)
    return (1.0 * volume) / (price + 0.01)

def get_research(question):
    # Skip research for now - HF models aren't working reliably
    return "(Research disabled for now)"

def send_email(picks, recipient):
    if not BREVO_SMTP_KEY:
        print("ERROR: BREVO_SMTP_KEY not set!")
        return
    
    body = "🤑 Tonight's Kalshi Alpha Picks (Demo)\n\n"
    
    for i, (mkt, score) in enumerate(picks, 1):
        q = mkt.get("title", "Unknown")
        slug = mkt.get("ticker", mkt.get("event_ticker", ""))
        url = f"https://demo.kalshi.co/market/{slug}"
        price = mkt.get("last_price", 0)
        research = get_research(q)
        
        body += f"""{i}. {q}
   Price: ${price:.2f} | Alpha: {score:.2f}
   Research: {research}
   Link: {url}

"""

    msg = EmailMessage()
    msg["Subject"] = "🤑 Kalshi Alpha Picks"
    msg["From"] = "Kalshi Bot <bot@kalshi.bot>"
    msg["To"] = recipient
    msg.set_content(body)
    
    print(f"DEBUG: Sending email to {recipient}")
    
    try:
        with smtplib.SMTP("smtp-relay.brevo.com", 587) as smtp:
            smtp.starttls()
            smtp.login(BREVO_SMTP_KEY, "")
            smtp.send_message(msg)
        print("DEBUG: Email sent!")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

# ------------------------------------------------------------------
if __name__ == "__main__":
    markets = fetch_markets()
    scored = sorted([(m, alpha_score(m)) for m in markets], key=lambda x: x[1], reverse=True)[:3]
    print(f"DEBUG: Top 3 selected")
    send_email(scored, RECIPIENT)
    print("DEBUG: Done!")
