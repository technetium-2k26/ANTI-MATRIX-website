# Anti-Matrix Offer Letter Template System Fix & Master Document Architecture

**Document Title**: OFFER_LETTER_TEMPLATE_FIX.md  
**Module**: Offer Letter Template Management & Employee Document Engine  
**Execution Date**: September 2026  
**Status**: Completed, Fully Tested & Verified  

---

## 1. Root Cause of the Missing Template Error
Previously, when administrators attempted to generate an Offer Letter on `/admin/employees/<employee_id>/offer-letter/generate`, the generation service (`services/offer_letter_service.py`) relied on hardcoded filesystem fallback paths (`uploads/templates/offer letter (Anti-matrix).docx` and `uploads/templates/offer_letter_master.docx`). If neither of those exact hardcoded strings was present at that specific relative path, the system raised:
```
FileNotFoundError: Master Offer Letter DOCX template 'offer letter (Anti-matrix).docx' was not found.
```
This failed on production and Render environments where local developer filenames do not exist by default, and violated the principle of using the database-driven Template Management system as the authoritative single source of truth.

---

## 2. Hardcoded Paths Removed
- Removed the deprecated `get_offer_letter_master_path()` function and all hardcoded strings pointing to `"offer letter (Anti-matrix).docx"`.
- Eliminated all fallback logic that searched local paths or guessed file locations.
- Replaced generation lookup with `get_active_offer_letter_template()` which queries the database for the active `DocumentTemplate` record and loads its verified storage path.

---

## 3. Template Database Model Used
The application uses the `DocumentTemplate` model defined in [models/document.py](file:///c:/Users/Prave/Desktop/ANTI-MATRIX/ANTI-MATRIX-website/models/document.py):
- `id`: Primary key (Integer)
- `template_type`: Indexed string (`'offer_letter'`, `'experience_letter'`, `'certificate'`)
- `name`: Display name (e.g., `'Anti-Matrix Master Offer Letter'`)
- `filename`: Original uploaded filename preserved for UI display (e.g., `'offer letter (Anti-matrix).docx'`)
- `file_path`: Absolute/relative filesystem storage path to the uploaded DOCX
- `is_active`: Boolean flag indicating whether the template is the currently active version
- `created_at` & `updated_at`: UTC timestamps

---

## 4. Template Storage Mechanism
When an administrator uploads a master DOCX template via **Admin Dashboard &rarr; Templates &rarr; Document Templates &rarr; Offer Letter**:
1. The uploaded file is validated for `.docx` extension.
2. The file is saved to the persistent storage directory (`uploads/templates/`) with a secure timestamped and UUID-tagged filename (e.g., `offer_letter_1788577000_a1b2c3.docx`).
3. The original uploaded filename (e.g. `offer letter (Anti-matrix).docx`) is stored in the database record for display.

---

## 5. Active Template Selection
To retrieve the active template, `get_active_offer_letter_template()` executes:
```python
active_template = DocumentTemplate.query.filter_by(
    template_type='offer_letter',
    is_active=True
).order_by(DocumentTemplate.id.desc()).first()
```
- If no record exists: raises `OfferLetterTemplateNotFoundError`.
- If record exists but file is missing on disk: raises `OfferLetterTemplateFileMissingError`.
- No hardcoded filename fallbacks are used under any circumstance.

---

## 6. Upload Workflow
1. Administrator navigates to **Admin Dashboard &rarr; Templates &rarr; Document Templates**.
2. Selects a Microsoft Word `.docx` file and clicks **Upload Template** (or **Replace Template**).
3. The server validates the file, stores it with a unique name in `uploads/templates/`, sets `is_active = True`, and commits the record to the database.
4. Flash message confirms: `Document template '<filename>' uploaded and set as ACTIVE successfully.`

---

## 7. Replacement Workflow
When a new master Offer Letter template is uploaded:
1. All previous active records for `'offer_letter'` are updated to `is_active = False`.
2. The new template is saved to a distinct file path and marked `is_active = True`.
3. Previously generated employee Offer Letters remain 100% intact because each generated document is linked to the specific template version and saved separately in `uploads/generated_documents/`.

---

## 8. DOCX Generation Workflow
1. Administrator navigates to `/admin/employees/<employee_id>/offer-letter/generate`.
2. The page inspects the database:
   - If active template exists and file is present: renders the generation form with active template metadata at the top.
   - If template is missing or unuploaded: renders an alert banner with a direct link to Template Management and disables generation.
3. Upon POST:
   - Retrieves `active_template = get_active_offer_letter_template()`.
   - Clones the master template DOCX in memory via `docx.Document(active_template.file_path)`.
   - Replaces all dynamic candidate, job, and company placeholders across paragraphs, runs, tables, headers, and footers.
   - Saves generated file to `uploads/generated_documents/<employee_id>_Offer_Letter.docx`.
   - Master template on disk remains completely untouched and immutable.

---

## 9. Placeholder Replacement
The engine supports the following dynamic placeholders:
- `{{offer_date}}` / `[DD/MM/YYYY]`: Current generation date
- `{{employee_name}}` / `[Candidate Name]`: Full candidate/employee name
- `{{reference_number}}` / `[Reference Number]`: Application ID (e.g., `AM-APP-000123`)
- `{{job_title}}` / `[Job Title]`: Role title (e.g., `AI Engineer Intern`)
- `{{responsibilities}}` / `[brief description of responsibilities]`: Position description
- `{{key_tasks}}` / `[key tasks / deliverables]`: Key technical deliverables
- `{{joining_date}}` / `[Joining Date]`: Joining/start date
- `{{work_mode}}` / `[remote / hybrid / on-site]`: Work location/mode
- `{{conditions}}` / `[background verification / document submission / any other condition]`: Conditions of offer
- `{{acceptance_deadline}}` / `[Acceptance Deadline]`: Deadline for acceptance
- `{{employee_id}}`: Employee ID (e.g., `AM4827`)
- `{{department}}`: Department name
- `{{internship_duration}}`: Formatted internship duration (e.g., `3 Months`)

---

## 10. Formatting Preservation
- Replacements operate directly on run-level text (`paragraph.runs`) within python-docx.
- Preserves all fonts, font sizes, colors, bold, italic, line spacing, margins, logos, borders, headers, footers, tables, and page breaks.

---

## 11. Employee Document Storage & Relationship
- Generated documents are saved as `uploads/generated_documents/<employee_id>_Offer_Letter.docx`.
- The database creates/updates an `EmployeeDocument` record:
  - `employee_id`: Foreign key to `employees.id`
  - `template_id`: Foreign key to `document_templates.id`
  - `document_type`: `'offer_letter'`
  - `file_name`: `<employee_id>_Offer_Letter.docx`
  - `file_path`: Absolute path on disk
  - `status`: `'GENERATED'`
  - `email_status`: `'not_sent'`

---

## 12. Render Deployment Considerations
- Template management is 100% accessible and operable via the web UI at `/admin/templates`.
- On fresh Render instances, administrators upload the master DOCX through the UI once, which persists to the database and storage.
- The system never crashes or assumes a pre-existing local developer file path.

---

## 13. Error Handling
- **No Active Template**: Flashes `"Offer Letter template has not been uploaded. Please upload an Offer Letter template from Admin Dashboard → Templates."` and displays an alert banner on the generation page.
- **Physical File Missing**: Flashes `"The active Offer Letter template record exists, but its file could not be found. Please upload the template again."`
- Internal filesystem paths and tracebacks are never leaked to regular users.

---

## 14. Testing Performed
Automated test suite in `tests/test_offer_letter_system.py` covers:
1. `test_01_database_active_template_retrieval`: Retrieval of active template from DB.
2. `test_02_generate_offer_letter_for_employee_1`: DOCX generation, placeholder replacement, and styling preservation.
3. `test_03_generate_offer_letter_for_employee_2_and_isolation`: Isolation between different employee documents.
4. `test_04_master_template_remains_unmodified_after_generations`: Immutability of master template file.
5. `test_05_verify_and_send_offer_letter_email`: Email sending and one-time delivery lock.
6. `test_06_admin_routes_security_and_access_control`: Role-based route access controls.
7. `test_07_no_active_template_error_handling`: Error handling when no template is in DB.
8. `test_08_missing_physical_file_error_handling`: Error handling when template file is missing on disk.
9. `test_09_template_upload_and_replacement_flow`: Uploading, replacing, and preserving old documents.

---

## 15. Test Results

```
======================================================================
TEST SUITE EXECUTION SUMMARY
======================================================================
1. tests/test_offer_letter_system.py (9 tests)  --> PASSED (100% OK)
2. tests/test_user_application_flow.py (11 tests) --> PASSED (100% OK)
3. tests/test_payment_test_mode.py     (6 tests)  --> PASSED (100% OK)
4. tests/test_email_system.py         (10 tests) --> PASSED (100% OK)
5. test_admin_careers.py              (6 tests)  --> PASSED (100% OK)
6. test_cashfree_internship_system.py (12 tests) --> PASSED (100% OK)
7. test_delete_all_jobs.py            (8 tests)  --> PASSED (100% OK)
8. test_employee_credentials_system.py(8 tests)  --> PASSED (100% OK)
9. verify_all_10_scenarios.py         (10 steps) --> PASSED (100% OK)
10. verify_employee_credentials_flow.py(9 steps) --> PASSED (100% OK)
======================================================================
OVERALL STATUS: 100% OF ALL TESTS PASSED (0 FAILURES, 0 ERRORS)
======================================================================
```

---

## Final Checklist

| Verification Item | Status |
| :--- | :--- |
| Hardcoded template path removed | **YES** |
| Database-driven active template | **YES** |
| Upload Offer Letter Template | **YES** |
| Template stored correctly | **YES** |
| Active template status | **YES** |
| Template replacement | **YES** |
| Missing template handling | **YES** |
| Missing physical file handling | **YES** |
| Actual uploaded DOCX used | **YES** |
| Employee data fetched from DB | **YES** |
| Application data fetched from DB | **YES** |
| Job data fetched from DB | **YES** |
| Formatting preserved | **YES** |
| Master template protected | **YES** |
| Employee-specific document generated | **YES** |
| Employee-specific document stored | **YES** |
| Correct employee-document relationship | **YES** |
| Offer Letter preview | **YES** |
| Verify & Send preserved | **YES** |
| Correct Offer Letter attached to email | **YES** |
| One-time email protection preserved | **YES** |
| Render compatible | **YES** |
| No hardcoded fallback | **YES** |
