"""Generate sample transactions against the fraud detection API."""

import argparse
import os
import random
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

SAMPLE_USERS = ["user_101", "user_202", "user_303"]
CHANNELS = ["banking", "upi", "ecommerce", "credit_card", "insurance", "payment_gateway"]
COUNTRIES = ["IN", "US", "SG", "AE"]
DEVICES = ["device_a", "device_b", "device_c", "device_new"]


def build_payload(user_id: str, amount: float, channel: str, device_id: str, country: str) -> dict:
    return {
        "user_id": user_id,
        "amount": amount,
        "currency": "INR",
        "channel": channel,
        "merchant_id": f"merchant_{random.randint(1, 50)}",
        "device_id": device_id,
        "ip_address": f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "country_code": country,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Send sample transactions to the fraud API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--count", type=int, default=10, help="Number of transactions to send")
    parser.add_argument("--endpoint", choices=["score", "check"], default="check", help="API endpoint to use")
    parser.add_argument("--api-key", default=os.getenv("API_KEY", ""), help="X-API-Key for /score endpoint")
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/api/v1/transactions/{args.endpoint}"
    headers = {"Content-Type": "application/json"}
    if args.endpoint == "score":
        if not args.api_key:
            raise SystemExit("API key required for /score. Pass --api-key or set API_KEY in .env")
        headers["X-API-Key"] = args.api_key

    with httpx.Client(timeout=10.0) as client:
        for index in range(args.count):
            user_id = random.choice(SAMPLE_USERS)
            amount = round(random.uniform(500, 25000), 2)
            channel = random.choice(CHANNELS)
            device_id = random.choice(DEVICES)
            country = random.choice(COUNTRIES)

            payload = build_payload(user_id, amount, channel, device_id, country)
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            print(
                f"[{index + 1}/{args.count}] user={user_id} amount={amount} "
                f"decision={result['decision']} risk={result['risk_score']} "
                f"rules={[r['rule_id'] for r in result['rules_triggered']]}"
            )


if __name__ == "__main__":
    main()
