# alpha_scorer.py
import os, json, requests, smtplib
from email.message import EmailMessage

KALSHI_KEY = os.getenv("KALSHI_KEY")
HF_TOKEN    = os.getenv("HF_TOKEN")
BREVO_SMTP_KEY = os.getenv("BREVO_SMTP_KEY")
RECIPIENT   = os.getenv("RECIPIENT")

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
    prompt = f"Summarize: {question}"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}
    
    url = "https://router.huggingface.co/google/flan-t5-small"
    
    resp = requests.post(url, json=payload, headers=headers)
    
    if resp.status_code == 429:
        return "(Rate limited)"
    if resp.status_code != 200:
        print(f"DEBUG: HF error {resp.status_code}")
        return "(Research unavailable)"
    
    result = resp.json()
    if isinstance(result, list) and len(result) > 0:
        return result[0].get("generated_text", "").strip()
    return str(result)

def send_email(picks, recipient):
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
    
    # Brevo SMTP with your key
    with smtplib.SMTP("smtp-relay.brevo.com", 587) as smtp:
        smtp.login(BREVO_SMTP_KEY, "")
        smtp.send_message(msg)
    
    print("DEBUG: Email sent!")

# ------------------------------------------------------------------
if __name__ == "__main__":
    markets = fetch_markets()
    scored = sorted([(m, alpha_score(m)) for m in markets], key=lambda x: x[1], reverse=True)[:3]
    print(f"DEBUG: Top 3 selected")
    send_email(scored, RECIPIENT)
    print("DEBUG: Done!")
