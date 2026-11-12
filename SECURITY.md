# Security Policy

## This repository contains vulnerabilities on purpose

**Please read this before filing anything.**

`app/` and `native/` are **teaching material**. They deliberately contain:

| Defect | Location | Why it is there |
|---|---|---|
| SQL injection | `app/reports.py` | Baseline — conventional scanners find this too |
| Cross-tenant authorization bypass (IDOR) | `app/attachments.py` | The centrepiece. One endpoint is missing `AND tenant_id = ?` while its siblings have it |
| Server-side request forgery | `app/webhook.py` | Used to show that a fix can follow the repository's own conventions |
| Same-tenant object-level authorization bypass | `app/comments.py` | Not part of the guided workshop; exists so the nightly CI pipeline has a finding that a plain `tenant_id` check does not cover |
| Heap buffer overflow | `native/csvparse.c` | Bonus exercise, reproduced under AddressSanitizer |
| A **deliberate false positive** | `app/exporter.py` | `shell=True` that is provably not exploitable — the point of the exercise is that it gets dismissed |

Participants find and fix these during a workshop. That is the entire purpose of
the repository.

### Consequences

- **Alerts from Code Scanning, Dependabot, or any SAST are expected here.**
  They are not incidents. Please do not escalate them.
- **This code is never deployed.** It runs only inside a participant's disposable
  Cloud Shell session, bound to localhost, seeded with fictional data
  (`Acme` / `Globex` / `Initech`). There is no hosted instance.
- **Do not deploy it, and do not expose it to a network.** The README says the
  same thing in its first screen.

## Why the repository asks for Code Scanning

Customers evaluating CodeMender consistently ask how it fits the AppSec tooling
they already own. The answer is that it exports SARIF, which uploads to GitHub
Code Scanning like any other scanner
(`.github/workflows/codemender-scan.yml`). Demonstrating that is more convincing
than describing it.

Enabling Code Scanning here will surface the defects listed above. That is the
intended outcome.

## Reporting an actual problem

Some things *would* be real problems. Please do report:

- A credential, token, internal hostname, or customer name committed by mistake
- Anything that could affect a system outside a participant's own Cloud Shell
- Content that should not be in an internal repository

Contact the maintainer directly (see `CODEOWNERS`, or the repository's
Insights → Contributors) rather than opening a public issue.

## Pre-GA notice

CodeMender is a **limited preview** product. Access is granted per project, and
the terms restrict use to limited testing and evaluation. This repository
records measured behaviour of an unreleased product and is **internal only** —
it should not be made public without review.
