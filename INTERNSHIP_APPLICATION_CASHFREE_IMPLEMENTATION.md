# Anti-Matrix — Internship Application & Cashfree Payment Flow Implementation Report

## Executive Summary
This document provides a comprehensive technical breakdown of the Internship Application & Cashfree Payment Integration engineered for the **Anti-Matrix** web platform. The existing Flask, SQLAlchemy, and Vanilla CSS architecture was extended to support job-specific duration workflows (1 Month and 3 Months), dynamic Indian state and city hierarchies, conditional proof uploads (Aadhaar, PAN, College ID), server-side fee calculation, Cashfree Payment Gateway checkout with webhook/return signature verification, non-destructive database migrations, and an authenticated admin application dossier.

---

## 1. Files Analyzed
- `app.py`: Flask application factory, configuration loading, error handlers, and blueprint registrations.
- `config.py`: Application configurations, secret keys, upload path constants, and pricing mappings.
- `models/job.py`: `JobPosting` and `JobApplication` SQLAlchemy models.
- `models/payment.py`: `Payment` model tracking Cashfree order IDs, session IDs, verification status, and transaction references.
- `routes/main.py`: Public routes including `/careers`, `/careers/apply/<job_id>`, `/careers/apply/review/<app_id>`, and `/careers/apply/success/<app_id>`.
- `routes/payment.py`: Cashfree checkout initiation, return URL callbacks, webhook receivers, and failure recovery.
- `routes/admin.py`: Admin dashboard, job posting CRUD, candidate applications list, detail dossier, and secure document streaming.
- `services/cashfree_service.py`: Cashfree PG v2023-08-01 API client with signature verification and local sandbox fallback.
- `templates/pages/job_apply.html`: Candidate application form questionnaire and dynamic UI logic.
- `templates/pages/job_apply_review.html`: Pre-payment candidate review step.
- `templates/pages/job_apply_success.html`: Post-payment application confirmation view.
- `templates/admin/applications.html`: Admin applications overview table.
- `templates/admin/application_detail.html`: Admin candidate dossier view with document downloads and payment audit.

---

## 2. Files Modified
1. `config.py`:
   - Added `INDIA_STATES_AND_CITIES`: Complete mapping for all 36 Indian States and Union Territories with major cities and "Other".
   - Added `EDUCATION_LEVELS`: Standard academic qualifications.
   - Added `COMMON_DEGREES`: Common degrees in engineering, commerce, management, science, etc.
   - Added `GRADUATION_YEARS`: Years 2022 to 2029 (enforcing 2029 maximum).
   - Added `INTERNSHIP_FEES`: Strict server-side fee mapping (`1_month` = ₹199, `3_months` = ₹399).
2. `models/job.py`:
   - Extended `JobApplication` model with: `first_name`, `last_name`, `address`, `state`, `city`, `pincode`, `education_level`, `major`, `pan_filename`, and `pan_path`.
   - Maintained full backward compatibility with legacy fields (`full_name`, `college`, `department`, `degree`, `year_of_study`, `current_cgpa`).
3. `routes/main.py`:
   - Updated `apply_job` route: Form validation for First Name, Last Name, Email, Phone Number, Address, Indian State, Dependent City, 6-digit Pincode, Education Level, Degree, Major, Graduation Year (<= 2029), Resume (PDF, DOC, DOCX), and conditional Aadhaar/PAN/College ID (PDF, JPG, JPEG, PNG).
   - Enforced server-side duration-based requirements (`1_month` -> Resume only; `3_months` -> Aadhaar required, PAN/College ID optional).
   - Redirects to `/careers/apply/review/<app_id>` for internship positions requiring fee payment.
4. `routes/admin.py`:
   - Updated `download_document` route to support downloading PAN Card (`pan`) alongside `resume`, `aadhaar`, and `college_id` under strict `@admin_required` authorization.
5. `templates/pages/job_apply.html`:
   - Added top callout banner displaying `Internship Duration: 1 Month` or `Internship Duration: 3 Months`.
   - Structured the form into clean visual sections matching Anti-Matrix dark theme:
     1. Personal Information (First Name, Last Name, Email, Phone)
     2. Address & Location (Address, State dropdown, Dependent City dropdown, Pincode)
     3. Educational Background (Education level dropdown, Degree, Major, Graduation Year dropdown up to 2029)
     4. Proofs & Verification (Aadhaar required for 3M, PAN optional for 3M, College ID optional for 3M; completely hidden for 1M)
     5. Resume Upload (Required for all)
   - Client-side dynamic state-to-city population and interactive validation.
6. `templates/pages/job_apply_review.html`:
   - Displays complete pre-payment review summary: Personal info, Address, Education, Document filenames.
   - Displays server-enforced fee (₹199 for 1 Month, ₹399 for 3 Months) and action button `Pay ₹199` / `Pay ₹399`.
7. `templates/admin/application_detail.html`:
   - Displays all candidate fields (First Name, Last Name, Address, State, City, Pincode, Education Level, Major, Degree, Graduation Year).
   - Provides secure download links for Resume, Aadhaar, PAN Card, and College ID Card.
   - Displays Cashfree payment audit record (Order ID, Payment ID, Amount Paid, Status, Date).
8. `.env.example`:
   - Configured Cashfree environment variables (`CASHFREE_ENVIRONMENT`, `CASHFREE_CLIENT_ID`, `CASHFREE_CLIENT_SECRET`, `CASHFREE_API_VERSION`, `CASHFREE_RETURN_URL`, `CASHFREE_WEBHOOK_URL`).

---

## 3. Files Created
1. `migrations/migrate_cashfree_internship.py`:
   - Non-destructive SQLite/PostgreSQL schema migration script adding all new candidate columns to `job_applications` without dropping or recreating tables.
2. `test_cashfree_internship_system.py`:
   - Automated unit test suite with 12 comprehensive test methods verifying all 10 scenario requirements.
3. `verify_all_10_scenarios.py`:
   - End-to-end multi-step validation script testing the entire workflow from Admin Job Posting to Public Careers, Application Questionnaire, Cashfree Checkout, Return Verification, and Admin Dossier inspection.
4. `INTERNSHIP_APPLICATION_CASHFREE_IMPLEMENTATION.md`:
   - This comprehensive technical implementation report.

---

## 4. Database Changes & Migration Details
The existing `job_applications` table was modified using SQLite `ALTER TABLE ADD COLUMN` queries wrapped in transactional integrity:
- `first_name` (VARCHAR 100)
- `last_name` (VARCHAR 100)
- `address` (TEXT)
- `state` (VARCHAR 100)
- `city` (VARCHAR 100)
- `pincode` (VARCHAR 20)
- `education_level` (VARCHAR 100)
- `major` (VARCHAR 150)
- `pan_filename` (VARCHAR 255)
- `pan_path` (VARCHAR 500)

**Safety Verification**: No tables were dropped, existing job postings were preserved, and existing applications remained intact.

---

## 5. Application Fields & Form Architecture
| Field Name | Type | Validation / Constraints | Required (1M) | Required (3M) |
|---|---|---|---|---|
| **First Name** | Text Input | Non-empty string | Yes | Yes |
| **Last Name** | Text Input | Non-empty string | Yes | Yes |
| **Email** | Email Input | Valid RFC-compliant email regex | Yes | Yes |
| **Phone Number** | Tel Input | 10-digit Indian mobile number format | Yes | Yes |
| **Address** | Textarea | Street address, building, locality | Yes | Yes |
| **State** | Dropdown | 36 Indian States/UTs from `INDIA_STATES_AND_CITIES` | Yes | Yes |
| **City** | Dependent Dropdown | Filtered based on state; validated server-side | Yes | Yes |
| **Pincode** | Text Input | Exactly 6 digits (`^\d{6}$`) | Yes | Yes |
| **Education Level** | Dropdown | Selected from standard academic levels | Yes | Yes |
| **Degree** | Dropdown / Input | Degree qualification name | Yes | Yes |
| **Major** | Text Input | Field of study / specialization | Yes | Yes |
| **Graduation Year** | Dropdown | Integer range up to 2029 maximum | Yes | Yes |
| **Resume** | File Upload | PDF, DOC, DOCX (<= 10MB) | Yes | Yes |
| **Aadhaar Card** | File Upload | PDF, JPG, JPEG, PNG (<= 10MB) | **Hidden / No** | **Yes** |
| **PAN Card** | File Upload | PDF, JPG, JPEG, PNG (<= 10MB) | **Hidden / No** | **Optional** |
| **College ID Card** | File Upload | PDF, JPG, JPEG, PNG (<= 10MB) | **Hidden / No** | **Optional** |

---

## 6. Internship Duration & Pricing Logic

### Duration Identification
The duration is retrieved directly from the selected `JobPosting.duration` attribute stored in the database.
- If `duration == '1_month'`: Badge displays `Internship Duration: 1 Month`.
- If `duration == '3_months'`: Badge displays `Internship Duration: 3 Months`.
- The candidate cannot alter this value on the client.

### Server-Enforced Fee Mapping
Fees are mapped strictly server-side through `INTERNSHIP_FEES` in `config.py`:
- `1_month` -> **₹199**
- `3_months` -> **₹399**

**Tamper Protection**: Any client-submitted amount in POST parameters (e.g. `amount=1`, `amount=99`) is strictly ignored. The backend recalculates the order amount directly from `job.duration` before generating Cashfree payment sessions.

---

## 7. 1-Month vs 3-Month Workflows

### 1-Month Internship Flow:
1. Candidate views `Internship Duration: 1 Month`.
2. Proofs section (Aadhaar, PAN, College ID) is completely hidden in the UI.
3. Candidate fills Personal Info, Address (State/City/Pincode), Education (Level, Degree, Major, Graduation Year <= 2029), and uploads Resume.
4. Review page confirms details and shows fee: **₹199**.
5. Candidate clicks `Pay ₹199` -> Cashfree order created for ₹199.
6. Upon verified payment, application code `AM-APP-XXXXXX` is generated, status set to `submitted`, and success page displayed.

### 3-Month Internship Flow:
1. Candidate views `Internship Duration: 3 Months`.
2. Proofs section is dynamically displayed with Aadhaar Card (marked Required `*`), PAN Card (marked Optional), and College ID Card (marked Optional).
3. Candidate fills all fields and uploads Aadhaar + Resume.
4. Review page confirms details and shows fee: **₹399**.
5. Candidate clicks `Pay ₹399` -> Cashfree order created for ₹399.
6. Upon verified payment, application code `AM-APP-XXXXXX` is generated, status set to `submitted`, and success page displayed.

---

## 8. State & Dependent City Implementation
- `config.py` defines `INDIA_STATES_AND_CITIES` containing all 36 Indian states and union territories.
- On the frontend (`templates/pages/job_apply.html`), an event listener on the State select dynamically re-populates the City select with the corresponding valid cities.
- On the backend (`routes/main.py`):
  1. Validates `state in INDIA_STATES_AND_CITIES`.
  2. Validates `city.lower() in [c.lower() for c in INDIA_STATES_AND_CITIES[state]]`.
  3. If a mismatched combination is submitted (e.g., `State: Tamil Nadu`, `City: Bengaluru`), the server immediately rejects the submission with: `Selected city is not valid for state Tamil Nadu.`

---

## 9. File Upload Security
1. **Isolated Storage**: Files are saved to dedicated server directories (`uploads/resumes` and `uploads/documents`), strictly separated from the public static web root (`static/`).
2. **Path Traversal Protection**: Uses `werkzeug.utils.secure_filename` combined with unique UUID/timestamp prefixes.
3. **MIME & Extension Whitelisting**:
   - Resumes: `.pdf`, `.doc`, `.docx`
   - Proof Documents: `.pdf`, `.jpg`, `.jpeg`, `.png`
   - Rejects executable files (`.exe`, `.sh`, `.php`, `.bat`, `.cmd`, `.js`, etc.).
4. **File Size Enforcement**: 10MB maximum per file.
5. **Admin Protected Access**: Documents can only be retrieved through authenticated routes (`/admin/applications/<id>/document/<type>` and `/admin/applications/<id>/resume`) decorated with `@admin_required`.

---

## 10. Cashfree Payment Gateway Integration
- **API Version**: `2023-08-01`
- **Order Creation Endpoint**: `POST /pg/orders`
- **Order Fetch Endpoint**: `GET /pg/orders/{order_id}`
- **Security**:
  - `CASHFREE_CLIENT_SECRET` is kept server-side only in environment variables.
  - Return URL callback (`/payment/cashfree/return`) fetches live order status from Cashfree API and confirms `order_status == 'PAID'` and matching `order_amount` before updating database records.
  - Webhook callback (`/payment/cashfree/webhook`) computes `HMAC-SHA256(timestamp + raw_payload, client_secret)` and compares against `x-webhook-signature`.
  - **Idempotency**: Duplicate returns or webhook events check `payment.payment_status == 'paid'` to prevent duplicate application codes or double database updates.

---

## 11. Application Creation Timing & State Machine
1. **Draft / Pre-Payment**:
   - `payment_status = 'pending'`
   - `application_status = 'pending_payment'`
2. **Payment Success**:
   - `payment_status = 'paid'`
   - `application_status = 'submitted'`
   - Unique Application ID assigned (e.g., `AM-APP-000001`).
3. **Payment Failure / Cancelled**:
   - `payment_status = 'failed'` / `user_dropped`
   - `application_status = 'pending_payment'`
   - Candidate is directed to retry payment without re-entering form data.
4. **Duplicate Protection**:
   - Server checks if an application with matching `(email, job_id)` already has `application_status == 'submitted'` or `payment_status == 'paid'`.
   - If found, blocks the submission with: `You have already applied for this position.`

---

## 12. Admin Dashboard & Dossier
- Accessible at `/admin/applications` for authenticated administrators.
- Displays table with Application ID, Candidate Name, Email, Phone, Job Title, Duration, Fee, Payment Status badge (`Paid`), Application Status (`Submitted`), and Timestamp.
- Detail view (`/admin/applications/<id>`) displays:
  - Personal Details & Address (State, City, Pincode)
  - Education (Education Level, Degree, Major, Graduation Year)
  - Document Downloads (Resume, Aadhaar, PAN, College ID)
  - Cashfree Payment Record (Order ID, Payment Reference ID, Amount, Status)

---

## 13. Test Verification & Results

### Automated Unit Test Suite (`test_cashfree_internship_system.py` + `test_admin_careers.py` + `test_delete_all_jobs.py`)
All 22 unit tests passed:
```
Ran 22 tests in 3.977s
OK
```

### 10-Scenario Verification Matrix (`verify_all_10_scenarios.py`)
| Scenario # | Description | Test Result |
|---|---|---|
| **Scenario 1** | 1-Month Internship displays resume only, hides Aadhaar/PAN/College ID, charges ₹199. | **PASSED** |
| **Scenario 2** | 3-Month Internship displays Aadhaar (required), PAN (optional), College ID (optional), charges ₹399. | **PASSED** |
| **Scenario 3** | Server ignores manipulated client amounts (charges ₹399 for 3M even if client posts ₹199). | **PASSED** |
| **Scenario 4** | 1-Month Internship rejects submission without Resume. | **PASSED** |
| **Scenario 5** | 3-Month Internship rejects submission without Aadhaar. | **PASSED** |
| **Scenario 6** | 3-Month Internship accepts submission when PAN is omitted (optional). | **PASSED** |
| **Scenario 7** | 3-Month Internship accepts submission when College ID is omitted (optional). | **PASSED** |
| **Scenario 8** | Backend rejects invalid State/City combination (e.g. State: Tamil Nadu, City: Bengaluru). | **PASSED** |
| **Scenario 9** | Refreshing return/success page does not create duplicate applications or payments. | **PASSED** |
| **Scenario 10** | Duplicate Cashfree webhook handled idempotently with no double processing. | **PASSED** |

---

## 14. Render Deployment Compatibility
- `requirements.txt` contains all required packages (`Flask`, `Flask-Login`, `Flask-SQLAlchemy`, `Flask-WTF`, `python-dotenv`, `gunicorn`, `email-validator`, `requests`).
- `Procfile` specifies `web: gunicorn app:app`.
- Environment variables configured for seamless production switching (`CASHFREE_ENVIRONMENT=production`).
- File uploads stored in designated local writable directories or persistent disk.

---

## 15. Email Notification Status
- **Email Notifications**: **INTENTIONALLY NOT IMPLEMENTED** in this phase as instructed. No Brevo, SMTP, Gmail, or SendGrid dependencies were added.

---

## 16. Final Checklist

| Requirement | Status |
|---|---|
| Application page | **YES** |
| 1 Month option | **YES** |
| 3 Month option | **YES** |
| First Name | **YES** |
| Last Name | **YES** |
| Email | **YES** |
| Phone | **YES** |
| Address | **YES** |
| India State dropdown | **YES** |
| Dependent City dropdown | **YES** |
| Pincode | **YES** |
| Education | **YES** |
| Degree | **YES** |
| Major | **YES** |
| Graduation Year up to 2029 | **YES** |
| Resume | **YES** |
| Aadhaar conditional | **YES** |
| PAN optional conditional | **YES** |
| College ID optional conditional | **YES** |
| 1 Month = ₹199 | **YES** |
| 3 Months = ₹399 | **YES** |
| Cashfree Checkout | **YES** |
| Server-side amount validation | **YES** |
| Server-side Cashfree verification | **YES** |
| Webhook verification | **YES** |
| Application ID generation | **YES** |
| Database storage | **YES** |
| Admin application display | **YES** |
| Secure document access | **YES** |
| Payment retry | **YES** |
| Duplicate protection | **YES** |
| Mobile responsive | **YES** |
| Render compatible | **YES** |
| Email | **NOT IMPLEMENTED — INTENTIONALLY** |
