# Real-Time Fraud Detection Engine

A secure, user-friendly real-time fraud detection system with a web dashboard, API authentication, and advanced fraud rules for banking, UPI, e-commerce, and payment platforms.

## Features

- **Web dashboard** — submit transactions and see instant fraud results
- **Secure API** — API key authentication, rate limiting, security headers
- **10 fraud rules** — amount, velocity, geo, device, blocklist, and more
- **Audit log** — every check is logged for transparency
- **Live stats** — blocked, reviewed, and allowed transaction counts

## Quick start

```powershell
cd D:\RealTimeFraud
.venv\Scripts\activate
copy .env.example .env
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open the dashboard: **http://127.0.0.1:8000**

The API key is printed in the terminal on startup (development mode).

## Use the dashboard

1. Open http://127.0.0.1:8000 in your browser
2. Fill in transaction details (user ID, amount, channel, device, country)
3. Click **Check Transaction**
4. See the decision: **Allow**, **Review**, or **Block** with risk score and triggered rules

## Security

| Feature | Description |
|---------|-------------|
| API key auth | `/api/v1/transactions/score` requires `X-API-Key` header |
| Rate limiting | Prevents abuse (60 req/min API, 20 req/min dashboard) |
| Security headers | CSP, X-Frame-Options, nosniff, referrer policy |
| Input validation | Strict schema validation on all inputs |
| Audit trail | All transactions logged with source and timestamp |

Set your API key in `.env`:

```
API_KEY=your-strong-secret-key-here
```

## Fraud detection rules

| Rule | Detects |
|------|---------|
| `BLOCKLIST_MATCH` | Blocked IP or merchant |
| `HIGH_AMOUNT` | Amount above threshold (₹10,000) |
| `VELOCITY_SPIKE` | Too many transactions in 5 minutes |
| `VELOCITY_AMOUNT` | Total volume in window exceeds ₹50,000 |
| `AMOUNT_DEVIATION` | Amount much higher than user average |
| `NEW_DEVICE` | Unseen device for user |
| `GEO_ANOMALY` | Transaction from new country |
| `ROUND_AMOUNT` | Suspicious round-number high amounts |
| `ODD_HOUR` | Large transactions midnight–5 AM |
| `NO_DEVICE_HIGH_AMOUNT` | High amount without device fingerprint |

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Web dashboard |
| GET | `/health` | No | Health check |
| POST | `/api/v1/transactions/check` | No (rate limited) | Dashboard scoring |
| POST | `/api/v1/transactions/score` | API key | Secure programmatic API |
| GET | `/api/v1/dashboard/stats` | No | Live statistics |
| GET | `/api/v1/dashboard/recent` | No | Recent transactions |

**Secure API example:**

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/transactions/score `
  -H "Content-Type: application/json" `
  -H "X-API-Key: your-api-key-here" `
  -d '{"user_id":"user_101","amount":15000,"currency":"INR","channel":"upi","device_id":"phone_1","country_code":"IN"}'
```

## Run tests

```powershell
python -m pytest tests/ -v
```

## Project structure

```
RealTimeFraud/
├── config/                 # Settings
├── src/
│   ├── api/                # FastAPI, security, middleware, routes
│   ├── core/               # Schemas
│   ├── detection/          # Fraud engine + rules
│   ├── features/           # Feature store
│   ├── services/           # Business logic + audit log
│   └── web/                # Dashboard UI (HTML/CSS/JS)
├── scripts/
├── tests/
└── requirements.txt
```
