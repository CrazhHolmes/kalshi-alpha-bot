# Kalshi Alpha Bot

Nightly automated scanner that:
1. Pulls open markets from Kalshi Demo environment  
2. Scores them by alpha potential  
3. Uses Claude to research each pick  
4. Emails the top 3 opportunities to your inbox  

## Setup

1. **Create a Kalshi Demo account**  
   https://demo.kalshi.co/  

2. **Generate a Demo API key** (`sk_demo_…`) from the Demo account’s **API Keys** page.  

3. **Get a free Claude API key**  
   https://console.anthropic.com  

4. **Create a Tutanota mailbox** (you already have `ottomation@tutamail.com`).  

## Secrets (GitHub → Settings → Secrets → Actions)

| Secret name | Value |
|-------------|-------|
| `KALSHI_KEY` | Demo API key (`sk_demo_…`) |
| `CLAUDE_KEY` | Anthropic API key |
| `EMAIL_USER` | `ottomation@tutamail.com` |
| `EMAIL_PASS` | Tutanota password |
| `RECIPIENT`  | `ottomation@tutamail.com` (or another address you want the picks sent to) |

## Running

- **Manual test**:  
  1. Go to **Actions** → “Nightly Alpha Scan (Demo)”.  
  2. Click **Run workflow**, choose the `main` branch, and click **Run workflow** again.  

- **Automatic**:  
  The workflow is scheduled to run every day at **02:00 UTC** (10 PM EST).  

## Cost

| Service | Monthly cost |
|---------|--------------|
| Claude (free tier) | 5 000 tokens ≈ 10‑15 market analyses (free) |
| GitHub Actions | 2 000 min free tier (enough for nightly runs) |
| Tutanota | Free plan covers the email sending |
| **Total** | **USD 0** |

## How it works (high‑level)

1. **Fetch markets** from `https://demo-api.kalshi.co/trade-api/v2/markets`.  
2. **Alpha scoring**:  
   $$\text{score} = \frac{\text{payout} \times \text{volume}}{\text{current\_price} + 0.01}$$  
3. **Research**: each of the top‑3 markets is sent to Claude with a prompt asking for a three‑sentence summary.  
4. **Email**: a plain‑text email with market details, the alpha score, and Claude’s summary is sent via Tutanota’s SMTP (`smtp.tutanota.com:587`).  

## License

MIT License – feel free to fork, modify, and reuse.  

---  

*If you run into any issues, check the Action logs for authentication errors (API key vs. demo key, SMTP credentials) and verify that the secrets are correctly set.*  
