# alpha_scorer.py
import os, json, requests

KALSHI_KEY = os.getenv("KALSHI_KEY")
HF_TOKEN    = os.getenv("HF_TOKEN")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
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
    prompt = f"""Summarize this prediction market question in 2 sentences: "{question}" """
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 80}}
    
    url = "https://router.huggingface.co/meta-llama/Llama-3-8B-Instruct"
    
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

    # Send via Brevo API
    url = "https://api.brevo.com/v3/smtp/email"
    
    data = {
        "sender": {
            "name": "Kalshi Bot",
            "email": "bot@example.com"
        },
        "to": [
            {
                "email": recipient,
                "name": "Architect"
            }
        ],
        "subject": "🤑 Kalshi Alpha Picks",
        "textContent": body
    }
    
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"DEBUG: Sending email to {recipient} via Brevo")
    
    resp = requests.post(url, json=data, headers=headers)
    
    if resp.status_code == 201:
        print("DEBUG: Email sent successfully!")
    else:
        print(f"DEBUG: Brevo error {resp.status_code}: {resp.text}")

# ------------------------------------------------------------------
if __name__ == "__main__":
    markets = fetch_markets()
    scored = sorted([(m, alpha_score(m)) for m in markets], key=lambda x: x[1], reverse=True)[:3]
    print(f"DEBUG: Top 3 selected")
    send_email(scored, RECIPIENT)
    print("DEBUG: Done!")
