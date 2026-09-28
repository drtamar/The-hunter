---
name: source-verification
description: How to verify a source artifact — image manipulation detection, account authenticity checks, claim corroboration. Used before promoting a finding from Indeterminate to Confirmed.
---

# Source Verification Skill

No finding should reach `Confirmed` without verification. This skill is the checklist. Pattern derived from `claude-skills-journalism/source-verification`.

## Image authenticity

1. **EXIF inspection** — `exiftool <file>`. Look for camera make/model, GPS, software (Photoshop = manipulation flag).
2. **Reverse image** — TinEye / Yandex / Google Lens. If the image is older than the claimed event → stolen.
3. **Stock-photo check** — reverse-search hits Shutterstock / iStock / Pexels → fake persona.
4. **Generative-AI detection** — manual: hands, ears, jewelry, logos, text rendering, asymmetric earrings, melted backgrounds, six fingers.
5. **PNG / JPG resave artifact** — quantization tables, double-JPEG signs.

## Account authenticity

1. **Account age vs activity gap** — 5-year-old account first posting last week is suspicious.
2. **Follower / following ratio** — 100k followers, 10 posts → bought.
3. **Engagement-to-follower ratio** — < 0.1% suggests fake followers.
4. **Posting timezone** — cluster reveals operator tz; mismatch with claimed location → false geographic claim.
5. **Language** — typos, MT-isms, native-locale idioms.
6. **Profile photo reverse** — stock or stolen → false persona.

## Claim corroboration

1. **Two-source rule (Grade A)** — Confirmed requires ≥ 2 independent grade-A supports.
2. **Source independence** — two articles citing the same press release = one source.
3. **Triangulation** — different vector types corroborate (registrar email + chain explorer + Telegram link).
4. **Time consistency** — events that contradict the timeline get downgraded.

## Document authenticity

1. **Metadata** — PDFInfo, exiftool, Word `<docx>/docProps/core.xml` — author, last-modified-by, software, dates.
2. **Visual inconsistencies** — font shifts, alignment breaks, kerning anomalies, copy-paste artifacts.
3. **Issuer verification** — if the doc claims to be from a bank, a court, a notary — verify with the issuer (where legally permissible).

## Quote attribution

A quote is only as good as the archive. Always:
- Permanent archive URL.
- SHA-256 of the page at time of capture.
- Screenshot.
- Note any later edits (compare with subsequent fetch).

## Hypothesis lifecycle

A finding’s status only moves:
- `Indeterminate` → `Confirmed` when verification produces ≥ 2 grade-A supports.
- `Indeterminate` → `Refuted` when a grade-A source contradicts and rebuttal fails.
- `Confirmed` → `Indeterminate` when new evidence raises doubt (write a `superseded_by` row).
- Never silently change status. Always append a new ledger row with the reason.
