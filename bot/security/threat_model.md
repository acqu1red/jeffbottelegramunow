# Threat Model

## Assets
- Telegram identifiers and usernames (PII)
- Payment records and subscription status
- Invite links and channel access
- Admin credentials

## Trust Boundaries
- Telegram API and Stars payments
- Payment aggregator (Tinkoff)
- Web panel session and admin login
- SQLite storage and filesystem

## Threats and Mitigations
- PII leakage: encrypt PII with Fernet at rest; store only encrypted `telegram_id` and `username`.
- Unauthorized access to admin panel: salted password hash, rate limiting, and IP logging.
- Invite link sharing: one active invite per user, short TTL, revoke on reuse.
- Payment spoofing: verify webhook signatures and invoice payload.
- Subscription bypass: scheduler checks and auto-kick expired users.
- Database theft: data is encrypted; no clear-text identifiers stored.
- Replay of webhooks: idempotent payment processing and status checks.

## Residual Risks
- SQLite file compromise still exposes non-PII data and encrypted blobs.
- Compromised server runtime could access decrypted data.
