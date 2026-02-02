# test_secrets.py
import os

print("=== Secret Test ===")
print(f"KALSHI_KEY: {os.getenv('KALSHI_KEY')}")
print(f"HF_TOKEN: {os.getenv('HF_TOKEN')}")
print(f"BREVO_SMTP_KEY: {os.getenv('BREVO_SMTP_KEY')}")
print(f"RECIPIENT: {os.getenv('RECIPIENT')}")
