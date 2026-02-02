# alpha_scorer.py
import os, json, requests, smtplib
from email.message import EmailMessage

KALSHI_KEY = os.getenv("KALSHI_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECIPIENT   = os.getenv("RECIPIENT")
HF_TOKEN    = os.getenv("HF_TOKEN")  # Free Hugging Face token

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
    """Free Hugging Face model for research summary"""
    prompt = f"""Summarize this prediction market question in 2-3 short sentences: "{question}" """
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 100, "temperature": 0.3}
    }
    
    url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3-8B-Instruct"
    
    resp = requests.post(url, json=payload, headers=headers)
    
    if resp.status_code == 429:
        print("DEBUG: HF rate limited, skipping research")
        return "(Rate limited - skipping research)"
    
    if resp.status_code != 200:
        print(f"DEBUG: HF error {resp.status_code}: {resp.text[:200]}")
        return "(Research unavailable)"
    
    result = resp.json()
    if isinstance(result, list) and len(result) > 0:
        return result[0].get("generated_text", "").strip()
    return str(result)

def send_email(picks):
    body = "🤑 Tonight's Kalshi Alpha Picks (Demo)\n\n"
    
    for i, (mkt, score) in enumerate(picks, 1):
        q = mkt.get("title", "Unknown")
        slug = mkt.get("ticker", mkt.get("event_ticker", ""))
        url = f"https://demo.kalshi.co/market/{slug}"
        price = mkt.get("last_price", 0)
        
        # Get free research from Hugging Face
        research = get_research(q)
        
        body += f"""{i}. {q}
   Price: ${price:.2f} | Payout: $1.00
   Alpha: {score:.2f}
   Research: {research}
   Link: {url}

"""

    msg = EmailMessage()
    msg["Subject"] = "🤑 Kalshi Alpha Picks"
    msg["From"] = EMAIL_USER
    msg["To"] = RECIPIENT
    msg.set_content(body)
    
    print(f"DEBUG: Sending email to {RECIPIENT}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
    print("DEBUG: Email sent!")

# ------------------------------------------------------------------
if __name__ == "__main__":
    markets = fetch_markets()
    scored = sorted([(m, alpha_score(m)) for m in markets], key=lambda x: x[1], reverse=True)[:3]
    print(f"DEBUG: Top 3 selected")
    send_email(scored)
    print("DEBUG: Done!")
