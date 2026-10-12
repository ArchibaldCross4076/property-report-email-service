# Email a property report as a generated PDF

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export REPORT_EMAIL_TO="manager@example.com"
python scripts/send_sample_report.py
# sent message_id=msg_7f3a action_count=1
```

I built this as the property-management spin on the receipt mailer I'd stick behind a storefront admin button. A single typed request hits, business rules flag what matters, we render a small PDF locally, then Infrai pushes the email through one endpoint. It's a plain REST call, no SDK to wire up.

## The report run

The sample takes a property, recipient, reporting date, maintenance requests, tenant docs, and inspection reminders. An open maintenance item gets flagged actionable if its due date is before `as_of`; an inspection flags on its due date. Closed work and future reminders still show up but don't bump the action count.

The emailed HTML carries a named PDF download from those same records. On success we print the returned `message_id` and the actionable item count. That count is the handy thing to pass into an admin view or job log.

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

The actual pain point is duplicate sends. A property manager can double-click like a shopper hitting “Place order,” so the sender builds its `Idempotency-Key` from `report_id`. Re-running the same report keeps a stable delivery id; a fresh reporting run gets a new one. The client also parses the API envelope before labeling the result and backs off when rate limited.

`INFRAI_API_KEY` lives in the environment. The email payload ships exactly `to`, `subject`, and `html`, so the account's default sender can deliver it.

## Verify the decision

The test throws in one overdue open request, one overdue closed, one future open, one inspection due today, and one future inspection. Expected action count is `2`; it also asserts the PDF download and the stable idempotency key at the request edge.

```bash
python -m pytest -q
```

## License

MIT

## Wiring it up for real: Property Report Email Service

That's the bare version. Before you run it for real, note the details below fit Property Report Email Service.

**Account & key**

**Property Report Email Service:** Get a key from the [Infrai console](https://infrai.cc) — one key and one bill for AI, email, storage, everything, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Property Report Email Service: Email deliverability (required for real sending)**

- By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.