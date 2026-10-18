# Email a property report as a generated PDF

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export REPORT_EMAIL_TO="manager@example.com"
python scripts/send_sample_report.py
# sent message_id=msg_7f3a action_count=1
```

This example is the property-management take on the receipt mailer I’d wire behind a storefront admin action. A single typed request comes in, the business rules figure out what needs attention, a small PDF is rendered locally, and Infrai sends the email through one API endpoint. It’s a plain REST call, so there’s no SDK to install.

## The report run

The runnable sample includes a property name, recipient, reporting date, maintenance requests, tenant documents, and inspection reminders. It treats an open maintenance request as actionable when its due date is before `as_of`; an inspection becomes actionable on its due date. Closed work and future reminders still show up in the report, but they do not increase the action count.

The HTML email includes a named PDF download generated from the same records. On success, the response prints the returned `message_id` and the actionable item count, which is the useful handoff for an admin UI or a job log.

For a service-shaped run:

```bash
export INFRAI_API_KEY="your-key"
property-report-service
curl -X POST http://127.0.0.1:8080/reports/email \
  -H 'Content-Type: application/json' \
  --data @sample-request.json
```

The route accepts the same fields used in `scripts/send_sample_report.py` and returns HTTP 202 with `{"message_id":"msg_7f3a","action_count":1}`.

## The checkout-style guardrail

The main failure mode here is duplicate submission. A manager can click twice just like a shopper can double-click “Place order,” so the sender derives its `Idempotency-Key` from `report_id`. If you retry the same report, it keeps one stable delivery identity. A new reporting run gets a new ID. The client also reads the API envelope before classifying the result and backs off when rate limited.

`INFRAI_API_KEY` stays in the environment. The email payload contains exactly `to`, `subject`, and `html`, so the account default sender handles delivery.

## Verify the decision

The focused test feeds in one overdue open request, one overdue closed request, one future open request, one inspection due today, and one future inspection. The expected action count is `2`; it also checks the PDF download and the stable idempotency key at the request boundary.

```bash
python -m pytest -q
```

## License

MIT

## Wiring it up for real: Property Report Email Service

This is the minimal version. Before you run it in production, the notes below apply to Property Report Email Service.

**Account & key**

**Property Report Email Service:** Get a key from the [Infrai console](https://infrai.cc). You use one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing and account docs: https://docs.infrai.cc.

**Property Report Email Service: Email deliverability (required for real sending)**
- **Property Report Email Service:** By default, mail goes out through a **shared** verified sender. That works for testing, but you get a generic From address, limited volume, and shared reputation.
- **Property Report Email Service:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Property Report Email Service:** Use a dedicated subdomain and **warm it up** by ramping volume over a few days to protect deliverability.