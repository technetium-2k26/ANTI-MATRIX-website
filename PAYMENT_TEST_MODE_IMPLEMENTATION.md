# PAYMENT_TEST_MODE Implementation Report & Documentation

## Overview
This document details the temporary payment testing bypass implemented for Anti-Matrix. It allows end-to-end candidate application submissions, server-side simulated payments, unique Application ID generation, database storage, and email notifications to be tested without making actual financial transactions via Cashfree.

---

## 1. Cashfree Architecture Preservation
- **Real Cashfree Code Intact**: The official Cashfree payment service (`services/cashfree_service.py`), SDK checkout template (`templates/pages/payment_cashfree_checkout.html`), webhook handler (`routes/main.py`), and verification endpoints remain completely preserved.
- **Zero Config Deletions**: `CASHFREE_CLIENT_ID`, `CASHFREE_CLIENT_SECRET`, `CASHFREE_ENVIRONMENT`, `CASHFREE_API_VERSION`, and return/webhook URLs have not been modified or deleted.

---

## 2. Environment Configuration & Switch
The mode is strictly toggled via the `PAYMENT_TEST_MODE` environment variable.

| Environment | `PAYMENT_TEST_MODE` Default | Behavior |
|---|---|---|
| **Development** | `true` | Displays `[ Complete Test Payment ]` button; performs server-side simulated payment. |
| **Testing** | `true` | Unit & automated test suites run without external API calls. |
| **Production** | `false` | Real Cashfree payment gateway is active (`Pay ₹199` / `Pay ₹399`). |

### `.env.example` Configuration
```env
# TEMPORARY DEVELOPMENT PAYMENT MODE
# Set to true ONLY for local/testing environments to bypass Cashfree checkout.
# MUST be false in production.
PAYMENT_TEST_MODE=false
```

---

## 3. Server-Side Application Fee Determination
The Application Fee is strictly calculated and enforced on the server based on internship duration:
- **1 Month Internship**: Application Fee = **₹199**
- **3 Months Internship**: Application Fee = **₹399**

Client-supplied amounts are never trusted. The server enforces the authoritative fee directly from `INTERNSHIP_FEES` mapping in `config.py`.

---

## 4. Test Payment Flow & Order of Operations
The testing workflow follows a secure backend lifecycle:

```
Candidate Fills Application Form (Uploads Resume ± Aadhaar)
                    ↓
Server Validates Form & Document Requirements
                    ↓
Draft Application Created (Status: pending_payment)
                    ↓
Review Page Displays Authoritative Application Fee (₹199 / ₹399)
                    ↓
Candidate Clicks [ Complete Test Payment ]
                    ↓
POST /careers/apply/test-payment/<app_id>
                    ↓
Server Validates Job & Calculates Exact Application Fee
                    ↓
Payment Record Created with gateway='TEST', status='paid'
                    ↓
Permanent Application ID Generated (AM-APP-XXXXXX)
                    ↓
Application Status Updated to 'submitted' & payment_status to 'paid'
                    ↓
Official Application Successful Email Sent (Duplicate Protected)
                    ↓
Candidate Redirected to Success Page
```

---

## 5. Idempotency & Duplicate Submission Protection
- If a candidate clicks **Complete Test Payment** multiple times rapidly or refreshes the confirmation:
  1. The server detects `payment_status == 'paid'`.
  2. It immediately returns the existing Application ID and redirects to the success page.
  3. No duplicate applications, payments, or emails are created.

---

## 6. Official Email Notification
- **Trigger**: Sent automatically upon successful simulated payment.
- **Duplicate Protection**: Verified against `application_success_email_status == 'SENT'`.
- **Variables Mapped**:
  - `{{Student Name}}` → Candidate's full name
  - `{{Internship Role}}` → Position Title
  - `{{Application ID}}` → Generated Application ID (`AM-APP-XXXXXX`)
  - `{{Application Date}}` → Application submission date
  - `{{Company Email}}` → `info@antimatrix.co.in`
  - `{{Website}}` → `www.antimatrix.co.in`

---

## 7. How to Switch Back to Cashfree
To activate real Cashfree checkout:
1. In your `.env` file, set:
   ```env
   PAYMENT_TEST_MODE=false
   ```
2. In production deployments, ensure `PAYMENT_TEST_MODE` is either omitted (defaults to `false` in `ProductionConfig`) or explicitly set to `false`.

---

## 8. Verification Checklist

| Requirement | Status |
|---|---|
| Real Cashfree code preserved | **YES** |
| Cashfree credentials/config preserved | **YES** |
| `PAYMENT_TEST_MODE` implemented | **YES** |
| Test Payment button ("Complete Test Payment") | **YES** |
| 1 Month = ₹199 | **YES** |
| 3 Months = ₹399 | **YES** |
| "Application Fee" wording used exclusively | **YES** |
| Server-side amount calculation | **YES** |
| Server-side test payment processing | **YES** |
| Application ID generated after successful payment | **YES** |
| Application stored in database | **YES** |
| Payment marked Paid | **YES** |
| Application marked Submitted | **YES** |
| Application Successful email triggered | **YES** |
| Correct email template used | **YES** |
| Correct Application ID in email | **YES** |
| Duplicate email prevented | **YES** |
| Duplicate application prevented | **YES** |
| Success page displayed properly | **YES** |
| Admin dashboard updated immediately | **YES** |
| Test mode production protection | **YES** |
| Experience Letter system unchanged | **YES** |
| Certificate system unchanged | **YES** |
| Existing Offer Letter system unchanged | **YES** |
