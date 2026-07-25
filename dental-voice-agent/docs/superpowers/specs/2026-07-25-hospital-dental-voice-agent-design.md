# Free Dental Checkup — Inbound AI Voice Agent

**Date:** 2026-07-25
**Status:** Design approved, pending implementation plan

## Purpose

Add an automated option to the hospital's existing inbound IVR on **+965 22207777**. Callers who press `2` reach an AI voice agent that describes the limited-time free dental checkup promotion, answers three common questions, and — for interested callers — captures a name and mobile number and emails the request to the call center for a human to follow up.

The existing `press 1 → human agent` path is unchanged. This project only adds a branch.

## Scope

**In scope:** language selection, promotion pitch, three FAQ answers, booking capture (name + mobile), confirmation readback, notification email to the call center, human fallback from every point in the flow.

**Out of scope:** real-time appointment scheduling, calendar integration, any HIS/CRM write, outbound calling, medical triage or advice, payment, and any specialty other than the dental promotion.

## Constraints and decisions

| Decision | Choice | Rationale |
|---|---|---|
| Deployment context | Real hospital, real patients | Requires human fallback, PII handling, consent disclosure |
| Telephony | Existing on-prem Asterisk / FreePBX | Full dialplan control; `press 2` is additive |
| Languages | Arabic and English, caller selects | Realistic for Kuwait; avoids fragile auto-detection |
| Voice platform | **Retell AI** (cloud) | Conversational quality and latency unattainable on the available CPU-only VM |
| Data egress | **Accepted** — audio and PII leave the network | Explicit decision by the project owner. See Compliance below. |
| Booking destination | **Email only**, no database | Owner's decision; durability addressed via on-disk spool + retry |
| Mobile number capture | **DTMF keypad**, before Retell handoff | Arabic digit ASR over phone lines is the highest-risk failure point |
| Integration direction | On-prem VM **polls** Retell API | Avoids opening inbound firewall rules on the hospital network |
| Hosting | Same on-prem VM as Asterisk | Already provisioned; resource-capped to protect live calls |

### Compliance note

Because Retell AI is a cloud service, live call audio, caller names, and mobile numbers are transmitted outside the hospital network to Retell and its underlying ASR/LLM/TTS subprocessors. This is a deliberate, owner-approved trade-off made to achieve conversational quality.

**Blocking prerequisites before real patients are routed to this branch:**

1. A signed data-processing agreement with Retell AI covering patient personal data.
2. Hospital compliance sign-off on the recording/AI disclosure wording in both Arabic and English.
3. Confirmation of the call-center email address (see Open Questions).

## Architecture

```
Caller → +965 22207777 → Asterisk (on-prem VM, existing IVR)
                            │
                     1 → human agent queue (unchanged)
                     2 → AI branch
                            │
                     language select (DTMF)
                            │
                     disclosure notice
                            │
                     SIP trunk ──────────► Retell AI (cloud)
                                              │  conversational agent
                                              │  pitch · FAQ · name capture
                                              ▼
                                          call ends
                                              │
        booking-worker (on-prem VM) ◄── poll ─┘
             │  outbound HTTPS only, every 30s
             ├─► validate + dedup
             ├─► write spool record
             └─► send email → callcenter@<confirm>
```

### Components

| Component | Responsibility | Location |
|---|---|---|
| `dialplan/` | Asterisk context: language select, disclosure, DTMF number capture, SIP handoff, fallback routing | PBX (`extensions_custom.conf`) |
| Retell agent config | Prompt, voice, language variants, conversation flow | Retell dashboard, exported to repo |
| `booking-worker` | Polls Retell, validates, dedups, renders and sends email, retries | On-prem VM |
| `spool/` | One JSON record per booking; `pending/`, `sent/`, `failed/` | On-prem VM |

Each is independently testable: the dialplan via SIPp scripted calls, the worker via fixture records, the agent config via Retell's own test harness.

## Call flow

1. **Language select** — "For English press 1 · للعربية اضغط 2". No input or invalid twice → human queue.
2. **Disclosure** — one sentence in the chosen language stating the caller is speaking with an automated assistant and that the call is processed by an AI service. Played before any capture.
3. **Mobile number (DTMF)** — "Enter your 8-digit mobile number." Validated as 8 digits beginning `5`, `6`, or `9`. Read back via Asterisk digit playback; `1` confirms, `2` re-enters. Two failed attempts → human queue.
4. **Handoff to Retell** — call bridges over SIP trunk. The validated number is passed as a custom SIP header so the agent never has to ask for it.
5. **Conversation** — greeting, promotion pitch, FAQ on request, and capture of the caller's full name. The agent confirms the name back to the caller.
6. **Completion** — Retell marks the call complete with structured data: `interested`, `customer_name`, `language`.
7. **Notification** — worker polls, sees the completed call, sends the email.

At every prompt, `0` transfers to the same destination as the existing `press 1`.

### Booking validity rule

A booking exists only when the caller has confirmed **both** the number readback (step 3) and the name (step 5). Calls ending earlier are discarded rather than partially sent, so the call center never receives an incomplete lead.

### Kill switch

An Asterisk database flag (`database put dental promo enabled 0`) routes `press 2` directly to the human queue. Lets the hospital end the promotion without a dialplan edit or a deploy.

## Notification email

**To:** the call center address (see Open Questions)
**Subject:** New Free Dental Checkup Appointment Request

Body fields: customer name, mobile number, language used, call source (`Inbound Call`), inbound number `+965 22207777`, timestamp in Asia/Kuwait, and the Retell call ID.

- The **call ID** is included so a rep can reference a specific request when something looks wrong.
- When Retell reports low confidence on the captured name, the email says so explicitly rather than presenting an uncertain spelling as fact.
- Outside call-center working hours, the closing line reads "our team will contact you during working hours" instead of "shortly".

**Delivery:** sent via the hospital SMTP relay with exponential backoff for up to one hour. A record moves `pending → sent` only on a confirmed `250`. The send is keyed on Retell call ID, so a retry after an ambiguous failure cannot produce a duplicate email. Records still unsent after an hour move to `failed/` and trigger an alert to an ops address.

## Data handling

| Data | Retention | Notes |
|---|---|---|
| Spool record (name, mobile) | 30 days | Retry and audit window |
| Retell-side recording and transcript | Per Retell config — set to minimum | Configure retention in Retell, do not rely on default |
| Anonymized outcome log (timestamp, call ID, outcome) | 1 year | Promotion metrics without retaining PII |

No full-call audio is stored on the hospital VM. A nightly systemd timer purges expired records. Retention periods are configuration values so compliance can shorten them without a code change.

## Failure modes

| Failure | Behavior |
|---|---|
| Silence or invalid key twice at any prompt | Transfer to human queue |
| Number fails validation twice | Transfer to human queue |
| SIP trunk to Retell unreachable | `press 2` falls back to human queue immediately; ops alert |
| Retell agent errors mid-call | Call returns to Asterisk, routed to human queue |
| Retell API unreachable during poll | Worker retries with backoff; no data loss, email delayed |
| SMTP relay down | Retry up to 1 hour, then `failed/` + ops alert; record preserved |
| Disk full / spool unwritable | Branch self-disables, `press 2` → human, ops alert |
| Caller hangs up mid-flow | Record discarded unless both fields confirmed |

Every path resolves to a human. The system's worst case is behaving as if it were not installed.

## Resource isolation

The VM already runs Asterisk in production. The worker must not degrade live calls:

- systemd unit with `CPUQuota=50%` and `MemoryMax=1G`.
- Python in a dedicated venv at `/opt/dental-agent`; the system interpreter is untouched.
- Dialplan changes are additive, in a new context in `extensions_custom.conf`.
- **Rollback:** point `press 2` at the human queue and reload. No uninstall, no Asterisk restart.

## Testing

- **Unit:** number validation, spool record serialization, email rendering in both languages, dedup key behavior, after-hours wording selection.
- **Integration:** worker against fixture Retell API responses, including low-confidence names, duplicate call IDs, and SMTP failure injection.
- **Dialplan:** SIPp scripted calls over a test extension covering book, decline, FAQ, timeout, invalid input, and `0` from every prompt — asserting the resulting spool record.
- **Pre-launch manual:** a native Kuwaiti Arabic speaker on a real handset over the live carrier. Phone-band audio and dialect behavior are where surprises appear.

## Required tools and access

**On the VM:** Python 3.11+, venv, `systemd`, `git`. Python packages: `httpx`, `pydantic`, `tenacity`. No GPU, no Docker, no database, no inbound firewall rules.

**Accounts:** Retell AI account with SIP trunking enabled and a signed DPA.

**Access to obtain:**
- Root/`asterisk` sudo on the PBX; if FreePBX, a Custom Destination plus `extensions_custom.conf` write access.
- SMTP relay host, port, credentials, with the sender address allowlisted.
- The exact extension or queue behind the existing `press 1`.
- A test DID or internal extension pointing at the AI branch.

## Open questions

1. **Call-center email address.** The address given was `callcenter@emmail.com.kw`; `emmail` appears to be a typo. Must be confirmed before go-live — a wrong address fails silently.
2. **Call-center working hours**, to drive the after-hours wording.
3. **Ops alert address** for failed sends and trunk outages.
4. **Retell Gulf Arabic quality** — to be assessed in the pre-launch manual test. If dialect handling proves unreliable, the fallback is to narrow the Arabic path to a guided DTMF flow while leaving English conversational.

## Explicit non-goals

The agent gives no medical advice, makes no diagnosis, promises no treatment outcome, quotes no prices beyond "the initial consultation is free", and collects nothing beyond name and mobile number. Any clinical question is deferred to the dentist at the appointment.
