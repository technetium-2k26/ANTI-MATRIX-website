# ANTI-MATRIX — Master Offer Letter DOCX Template Implementation Report

This document presents the complete technical architecture, implementation details, data mappings, formatting preservation techniques, security controls, and verification results for the **Anti-Matrix Master Offer Letter DOCX Template System**.

---

## 1. Existing Project Architecture

The Anti-Matrix platform is built upon a modular, secure **Flask** backend architecture with **SQLAlchemy ORM** and **Flask-Login** / **Flask-WTF** security middleware:
- **Application Factory Pattern**: `create_app(config_name)` initializes blueprints, database bindings, CSRF protection, and upload folders (`app.py`).
- **Blueprints**:
  - `main_bp`: Public marketing pages, dynamic Careers page, application form, Cashfree payment processing, and webhooks.
  - `auth_bp`: User and administrator authentication, session handling, password verification.
  - `admin_bp`: Administrator management portal, job management, candidate applications, employee credential generation, template management, and document dispatch.
  - `contact_bp`: Inquiries and support message routing.
- **Frontend Engine**: Jinja2 server-side rendering using Vanilla CSS custom properties (`index.css`), responsive layouts, SVG icon components (`components/icons.html`), and strict accessibility standards.

---

## 2. Existing Database Models Used

The system reuses and builds upon existing models without redundant or duplicate entities:
1. **`User`** (`models/user.py`): Platform authentication model enforcing role-based access control (`admin`, `member`).
2. **`JobPosting`** (`models/job.py`): Job openings with title, department, location, employment type, duration, fees, description, requirements, and responsibilities.
3. **`JobApplication`** (`models/job.py`): Candidate applications with candidate personal data, college info, uploaded documents, internship duration choice, payment state, and official `application_code` (e.g. `AM-APP-000123`).
4. **`Employee`** (`models/employee.py`): Workforce records storing unique cryptographically random Employee IDs (`AM####`), 1-to-1 link to `JobApplication`, and helper accessors.
5. **`DocumentTemplate`** (`models/document.py`): Master document template records for Microsoft Word DOCX templates (`offer_letter`, `experience_letter`, `certificate`).
6. **`EmailTemplate`** (`models/document.py`): Customizable email communications with dynamic placeholder replacement (`application_successful`, `offer_letter`).
7. **`EmployeeDocument`** (`models/document.py`): Employee-specific generated document records storing file paths, generation timestamps, status progression (`NOT_GENERATED` &rarr; `GENERATED` &rarr; `VERIFIED` &rarr; `SENT`), and one-time email dispatch states.

---

## 3. Template Storage Implementation

Templates and generated artifacts are stored securely outside public web roots:
- **Master Templates**: `uploads/templates/`
  - Active Master Offer Letter: `uploads/templates/offer letter (Anti-matrix).docx`
  - Master Experience Letter (Upload only): `uploads/templates/experience_letter_master.docx`
  - Master Certificate (Upload only): `uploads/templates/certificate_master.docx`
- **Generated Employee Documents**: `uploads/generated_documents/`
  - Files named predictably by Employee ID (e.g., `AM4827_Offer_Letter.docx`).
- **Access Control**: All downloads and previews are served via authenticated Flask routes with `@admin_required` decorators (`send_from_directory`) — direct public URL enumeration is impossible.

---

## 4. Offer Letter Placeholder Mapping

The master DOCX template contains specific placeholders that map directly to system and database attributes:

| Template Placeholder | Internal Variable | Source Model & Attribute | Example Resolved Value |
| :--- | :--- | :--- | :--- |
| `[DD/MM/YYYY]` / `{{offer_date}}` | `offer_date` | Current Date (UTC generation time) | `04/09/2026` |
| `[Candidate Name]` / `{{employee_name}}` | `employee_name` | `Employee.candidate_name` / `JobApplication.full_name` | `John Doe` |
| `[Reference Number]` / `{{reference_number}}` | `reference_number` | `JobApplication.formatted_code` | `AM-APP-000123` |
| `[Job Title]` / `{{job_title}}` | `job_title` | `JobPosting.title` | `AI Engineer Intern` |
| `[brief description of responsibilities]` / `{{responsibilities}}` | `responsibilities` | `JobPosting.description` / Admin input | `work on generative AI models...` |
| `[key tasks / deliverables]` / `{{key_tasks}}` | `key_tasks` | `JobPosting.requirements` / Admin input | `Python, PyTorch, LLM pipeline...` |
| `[Joining Date]` / `{{joining_date}}` | `joining_date` | Configured Joining Date | `Immediate / As mutually agreed` |
| `[remote / hybrid / on-site]` / `{{work_mode}}` | `work_mode` | `JobPosting.location` | `Remote / Hybrid` |
| `[background verification / ...]` / `{{conditions}}` | `conditions` | Configured Offer Conditions | `satisfactory credential verification` |
| `[Acceptance Deadline]` / `{{acceptance_deadline}}` | `acceptance_deadline` | Default 7 days from generation | `11 September 2026` |

---

## 5. Employee, Application & Job Data Mapping

When an administrator selects an Employee:
1. **`Employee`** &rarr; Fetches registered employee record with `employee_id` (e.g. `AM4827`).
2. **`Employee.application`** &rarr; Fetches associated `JobApplication` with candidate full name, email, phone, and formatted reference code (`AM-APP-000123`).
3. **`JobApplication.job`** &rarr; Fetches linked `JobPosting` with title, department, location/work mode, description, and requirements.

All relationships are validated server-side before generation. If any link is missing or mismatched, generation is rejected.

---

## 6. DOCX Processing & Formatting Preservation Method

The generation engine in `services/offer_letter_service.py` clones the master template and replaces text at the individual **run level**:
1. **Cloning**: The master DOCX template file is opened as a clean `docx.Document` instance without modifying the source file on disk.
2. **Run-Level Style Preservation**:
   - Paragraph text runs (`run.text`) are individually inspected for exact placeholder matches.
   - When a placeholder is found in a run, `run.text = run.text.replace(key, val)` is executed.
   - All run formatting attributes (`font.name`, `font.size`, `bold`, `italic`, `font.color`, `underline`) remain 100% intact.
3. **Multi-Run Span Handling**: If a placeholder was split across adjacent runs during Word serialization, adjacent runs within that block are collapsed while retaining the formatting of the primary run.
4. **Table & Section Processing**: Tables, headers, and footers across all document sections are traversed and processed using the same run-preserving method.
5. **Preserved Visual Elements**:
   - Anti-Matrix logo and table layout
   - Green border and green horizontal divider
   - Typography font families and sizes (e.g., 14pt / 16pt bold headings)
   - Chennai contact info and footer branding
   - 2-page document structure without spurious page breaks.

---

## 7. Generated Document Storage & Employee Relationship

Each generated document is saved with a deterministic, employee-specific filename:
- **Path**: `uploads/generated_documents/AM4827_Offer_Letter.docx`
- **Database Record**: `EmployeeDocument` linked via foreign key to `Employee.id`:
  ```python
  emp_doc = EmployeeDocument(
      employee_id=employee.id,
      document_type='offer_letter',
      file_name='AM4827_Offer_Letter.docx',
      file_path='/absolute/path/uploads/generated_documents/AM4827_Offer_Letter.docx',
      status='GENERATED',
      email_status='not_sent',
      generated_at=now_utc
  )
  ```

---

## 8. Admin UI & Workflow

### 8.1 Unified Templates Hub (`/admin/templates`)
The Admin Dashboard features a single **Templates** button in the header actions and navigation tabs. Inside `/admin/templates`:
- **EMAIL TEMPLATES**:
  1. `Application Successful`: Editable Subject & Body with dynamic variables.
  2. `Offer Letter`: Editable Subject & Body with dynamic variables.
- **DOCUMENT TEMPLATES**:
  1. `Offer Letter`: Active master template indicator (`offer letter (Anti-matrix).docx`), Available fields guide, Replace Master Template form, and Download Master Template button.
  2. `Experience Letter`: Template upload-only form.
  3. `Certificate`: Template upload-only form.

### 8.2 Employee Management Table (`/admin/employees`)
Added an **Offer Letter** status column and contextual action buttons:
- **Not Generated**: Shows `[ Generate ]` button &rarr; opens parameter review form.
- **Generated**: Shows `[ Preview ]` (downloads DOCX) and `[ Verify & Send ]` button.
- **Sent**: Shows green `Sent` badge and `[ Preview ]` button (duplicate send button hidden).

### 8.3 Employee Detail Dossier (`/admin/employees/<employee_id>`)
Includes dedicated **Offer Letter Document** card with real-time status badges, file details, generation timestamp, delivery date, preview, regeneration, and verify actions.

---

## 9. Verification & Email Dispatch Workflow

1. **Pre-Send Verification Screen** (`/admin/employees/<id>/offer-letter/verify`):
   - Displays generated file name and generation timestamp.
   - Displays candidate details and locks destination email to the candidate's verified database email (`employee.candidate_email`).
   - Renders live preview of the formatted email subject and body with all placeholders populated.
   - Shows attached document pill (`AM####_Offer_Letter.docx`).
2. **Explicit Verification & Dispatch**:
   - Admin clicks `[ Verify & Send Offer Letter ]`.
   - Backend retrieves candidate's registered email and generated Offer Letter DOCX.
   - Constructs MIME multipart message with the DOCX attachment.
   - Sends email via configured SMTP (or sandbox simulated email).
   - Sets `EmployeeDocument.status = 'SENT'`, `email_status = 'sent'`, and timestamps `sent_at` & `verified_at`.

---

## 10. Strict One-Time Sending Protection

To prevent accidental duplicate emails:
1. Before initiating any dispatch, the backend verifies `emp_doc.email_status != 'sent'`.
2. If already sent, the backend immediately blocks execution and flashes:
   `"Offer Letter already sent. Duplicate sending is prevented."`
3. The frontend disables and replaces the send button with a green `"Offer Letter Already Sent"` confirmation banner.
4. If an email send fails due to network/SMTP errors, status is recorded as `failed` with the error logged, permitting admin retry. Once successfully delivered, no further sends are allowed.

---

## 11. Security, Authorization & CSRF

- **Authentication & Role Check**: All template and document routes are protected with `@admin_required`. Unauthenticated requests redirect to `/login`; authenticated non-admin users receive `403 Forbidden`.
- **File System Protection**: Template uploads validate file extensions (`.docx` only) and sanitize names with `werkzeug.utils.secure_filename`.
- **Direct Link Protection**: Document files cannot be accessed directly via static URLs; all access routes verify admin identity.
- **CSRF Protection**: All POST forms include valid CSRF tokens with Flask-WTF validation.

---

## 12. Comprehensive Test Verification

An automated test suite `tests/test_offer_letter_system.py` was developed and executed alongside all repository regression tests:

### Test Results Summary

```
tests/test_offer_letter_system.py:
  test_01_master_template_integrity ............................ PASS
  test_02_generate_offer_letter_for_employee_1 (AM4827 John Doe)  PASS
  test_03_generate_offer_letter_for_employee_2 (AM1934 Jane Smith) PASS
  test_04_master_template_remains_unmodified_after_generations .. PASS
  test_05_verify_and_send_offer_letter_email & one-time lock .... PASS
  test_06_admin_routes_security_and_access_control .............. PASS
  test_07_admin_template_management_view_with_session ........... PASS
  test_08_admin_generate_preview_and_verify_flow ................ PASS
Total: 8/8 tests PASSED (100%)

Full Regression Suite:
  test_employee_credentials_system.py ......................... PASS (12 tests)
  test_cashfree_internship_system.py ........................... PASS (10 tests)
  test_admin_careers.py ........................................ PASS (10 tests)
  test_delete_all_jobs.py ...................................... PASS (2 tests)
Total: 34/34 tests PASSED (100%)
```

---

## 13. Final Implementation Checklist

| Feature Requirement | Status | Verification Note |
| :--- | :---: | :--- |
| **Templates button on Admin Dashboard** | **YES** | Single `Templates` button and nav tab opening `/admin/templates` |
| **Email Template: Application Successful** | **YES** | Configurable subject and body in Template Hub |
| **Email Template: Offer Letter** | **YES** | Configurable subject and body in Template Hub |
| **Document Template: Offer Letter** | **YES** | Active master DOCX with replace and download capabilities |
| **Document Template: Experience Letter (Upload only)** | **YES** | Upload-only active; no generation or sending |
| **Document Template: Certificate (Upload only)** | **YES** | Upload-only active; no generation or sending |
| **Master Offer Letter preserved** | **YES** | Source DOCX on disk is never modified during generation |
| **Exact DOCX used as master** | **YES** | `uploads/templates/offer letter (Anti-matrix).docx` is master |
| **Employee data fetched automatically** | **YES** | Retrieved from `Employee` model |
| **Application data fetched automatically** | **YES** | Retrieved from linked `JobApplication` |
| **Job data fetched automatically** | **YES** | Retrieved from linked `JobPosting` |
| **Placeholder replacement** | **YES** | Run-level placeholder replacement for all dynamic fields |
| **Original formatting preserved** | **YES** | Font family, size, bold, color, and spacing intact |
| **Logo preserved** | **YES** | Anti-Matrix header logo and contact info preserved |
| **Header preserved** | **YES** | Top header layout and branding preserved |
| **Footer preserved** | **YES** | Chennai address and Anti-Matrix footer preserved |
| **Border preserved** | **YES** | Green decorative border preserved |
| **Seals preserved** | **YES** | Signature and seal sections preserved |
| **Page structure preserved** | **YES** | Exact 2-page document structure maintained |
| **Generated document stored per employee** | **YES** | Saved as `AM####_Offer_Letter.docx` |
| **Employee-document relationship** | **YES** | Linked via `EmployeeDocument` table in DB |
| **Preview available** | **YES** | Admin preview/download endpoint active |
| **Verify & Send available** | **YES** | Explicit admin verification page with email preview |
| **Registered email used** | **YES** | Locked to `employee.candidate_email` from DB |
| **Offer Letter attached** | **YES** | Employee DOCX attached to outgoing email |
| **One-time email protection** | **YES** | Duplicate sending strictly blocked and warned |
| **Email failure handling** | **YES** | Errors caught, logged, and retry allowed if not sent |
| **Admin authorization** | **YES** | Strict `@admin_required` checks on all endpoints |
| **Original master template protected** | **YES** | Master file verified unchanged after multiple generations |
| **Experience Letter generation** | **NO** | **INTENTIONALLY** — future phase |
| **Certificate generation** | **NO** | **INTENTIONALLY** — future phase |
| **Experience Letter email** | **NO** | **INTENTIONALLY** — future phase |
| **Certificate email** | **NO** | **INTENTIONALLY** — future phase |

---

## 14. Future Extension Points

When scheduled for subsequent releases:
1. **Experience Letter Engine**: Utilize the uploaded master Experience Letter DOCX template with placeholder mapping (`{{completion_date}}`, `{{performance_rating}}`, `{{duration}}`).
2. **Certificate Generation Engine**: Utilize the uploaded master Certificate DOCX template with certificate verification IDs and completion dates.
3. **Automated PDF Conversion**: If headless LibreOffice or a cloud document conversion service is provisioned in the hosting environment, generate companion `.pdf` versions alongside `.docx`.
