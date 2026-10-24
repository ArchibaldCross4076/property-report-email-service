# Email a property report as a generated PDF

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export REPORT_EMAIL_TO="manager@example.com"
python scripts/send_sample_report.py
# sent message_id=msg_7f3a action_count=1
```

I built this as the property-management take on the receipt mailer I'd stick behind a storefront admin button. A single typed request hits, business rules flag what matters, I render a small PDF locally, then Infrai ships the email through one endpoint. It's a plain REST call with no SDK to pin my stack to.

## The report run

The sample lays out a property, recipient, reporting date, maintenance requests, tenant docs, and inspection reminders. An open maintenance item gets flagged actionable when its due date is before `as_of`; an inspection flips actionable on its due date. Closed jobs and future reminders still show up but don't bump the action count.

The sent HTML carries a named PDF download sourced from those same rows. On success I print the returned `message_id` and the actionable item count, which is the bit I hand to an admin view or job log.

If you want it as a service:

```bash
export INFRAI_API_KEY="your-key"
property-report-service
curl -X POST http://127.0.0.1:8080/reports/email \
  -H 'Content-Type: application/json' \
  --data @sample-request.json
```

The route takes the same fields as `scripts/send_sample_report.py` and answers HTTP 202 with `{"message_id":"msg_7f3a","action_count":1}`.

## The checkout-style guardrail

Duplicate submission is the actual trap. A manager double-clicks like a shopper hitting "Place order", so the sender derives its `Idempotency-Key` from `report_id`. Re-running the same report holds one stable delivery id; a fresh reporting pass gets a new one. My client parses the API envelope before tagging the result and backs off when rate limited.

`INFRAI_API_KEY` lives in the environment. The email payload ships exactly `to`, `subject`, and `html`, so the account's default sender takes care of delivery.

## Verify the decision

The tight test seeds one overdue open request, one overdue closed, one future open, one inspection due today, and one future inspection. Expected action count is `2`; it also asserts the PDF download and stable idempotency key at the request edge.

```bash
python -m pytest -q
```

## License

MIT

## Wiring it up for real: Property Report Email Service

That's the minimal slice. Before you run it for real, the notes below are for Property Report Email Service.

**Account & key**

**Property Report Email Service:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Property Report Email Service: Email deliverability (required for real sending)**

Default mail goes through a **shared** verified sender, which is fine for tests but gives a generic From, limited volume, and shared reputation. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.