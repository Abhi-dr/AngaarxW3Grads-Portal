# JOVAC Navigation and MCQ Change Log

This document summarizes the work completed for JOVAC Previous/Next navigation, MCQ flow fixes, routing reliability, and related API/model/template updates.

## Scope of Work

1. Fixed one-by-one Previous/Next behavior for JOVAC tutorial and assignment pages.
2. Ensured navigation follows the configured mixed order in each `CourseSheet`.
3. Preserved sheet context using `?sheet=<sheet_slug>` so navigation is deterministic.
4. Improved JOVAC MCQ handling for rendering, submission, and page navigation.
5. Added response and page-level no-cache protections to reduce stale data issues.
6. Aligned model field state with migrations to keep migration checks clean.

## Files Changed and What Changed

### `student/models.py`

- Added `CourseSheet.get_previous_item(self, current_item_id)`.
- This complements the existing `get_next_item()` and enables true backward navigation through mixed ordered items.

### `student/jovac_views.py`

- Added `cache_control(no_cache=True, no_store=True, must_revalidate=True)` to `jovac_sheet`.
- Updated `submit_assignment`:
  - Reads `sheet` from query params.
  - Falls back to assignment's first related sheet if query is missing.
  - Passes `sheet_slug` to template context.
- Refactored `get_next_jovac_assignment`:
  - Resolves target `CourseSheet` from `?sheet=` when available.
  - Uses `course_sheet.get_next_item(...)` to move by configured sheet order.
  - Supports redirection by item type (Tutorial, Assignment, MCQ, Coding).
  - Keeps `?sheet=` on assignment/tutorial redirects.
  - Handles end-of-sheet gracefully.
- Added new `get_previous_jovac_assignment`:
  - Resolves `CourseSheet` with `?sheet=`.
  - Uses `course_sheet.get_previous_item(...)`.
  - Redirects by item type and preserves `?sheet=`.
  - Handles start-of-sheet gracefully.

### `student/urls.py`

- Added route:
  - `jovac/assignment/<int:id>/previous` -> `get_previous_jovac_assignment`.
- Reordered URL groups so MCQ routes are defined before the generic batch catch-all route.

### `templates/student/jovac/view_tutorial.html`

- Replaced history-based Previous button (`history.back()`) with explicit Previous URL.
- Updated top and bottom navigation controls to explicit Previous/Next anchors.
- Added client-side query parsing to preserve `sheet` context in both URLs.

### `templates/student/jovac/submit_assignment.html`

- Replaced history-based Previous button (`history.back()`) with explicit Previous URL.
- Updated both top and bottom controls to use:
  - Previous: `get_previous_jovac_assignment`
  - Next: `get_next_jovac_assignment`
- Preserves `?sheet={{ sheet_slug }}` when available.

### `templates/student/jovac/course_sheet.html`

- Updated assignment list API fetch to reduce stale responses:
  - Added timestamp query (`?t=...`).
  - Added fetch option `cache: 'no-store'`.
- Updated action links to propagate context:
  - Tutorial link now includes `?sheet=<sheetSlug>`.
  - Submit Assignment link now includes `?sheet=<sheetSlug>`.
- Updated MCQ action URL construction:
  - Uses item-level `sheet_slug` fallback.
  - Added safe handling when MCQ slug is missing.

### `student/api/views/jovac_api.py`

- Added `sheet_slug` to serialized MCQ items so frontend can build correct MCQ URLs.
- Added no-cache response headers on assignment list API response:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`

### `student/mcq_views.py`

- Added cache-control decorators to reduce stale MCQ page/submit behavior.
- Enhanced `mcq_question_view` to support both contexts:
  - Batch sheet MCQs.
  - JOVAC `CourseSheet` MCQs.
- Added JOVAC-aware access checks using `CourseSheet` enabled/approved state.
- Added explicit `previous_question_url` and `next_question_url` generation.
- For JOVAC MCQ page navigation, uses MCQ-only sequence inside current `CourseSheet`.
- Chooses template dynamically:
  - JOVAC -> `student/jovac/mcq_question.html`
  - Batch -> `student/batch/mcq/problem.html`
- Updated `submit_mcq_answer` to fetch by slug without strict `is_approved=True` filter, supporting JOVAC flow.

### `templates/student/jovac/mcq_question.html` (new file)

- Added dedicated JOVAC MCQ page template.
- Includes:
  - Question display and options.
  - Submit answer flow (AJAX).
  - Explanation and result messaging.
  - Previous/Next question controls.
  - Reset behavior to avoid stale browser state.

### `administration/api/serializers/jovac_serializers.py`

- Updated `MCQQuestionAdminSerializer` fields to include `sheet`.
- Added `create()` override to enforce `is_approved=True` for admin-created JOVAC MCQs.

### `administration/api/views/jovac_api.py`

- Added custom `create()` in `MCQQuestionAdminViewSet` to support JOVAC MCQ creation.
- Ensures a placeholder sheet (`jovac-mcq-storage`) exists and is enabled/approved.
- Injects that sheet ID into serializer input before creating MCQ.
- Returns consistent success payload.

### `practice/models.py`

- Updated `MCQQuestion.sheet` to:
  - `blank=True, null=True`
- Purpose: align model definition with current migration state and remove migration check mismatch.

## Validation and Testing Run

### Completed Checks

1. `python manage.py check`
   - Passed (no issues).
2. `python manage.py makemigrations --check --dry-run --noinput`
   - Passed after model alignment (no pending changes).
3. Navigation consistency smoke check (all sheets/items)
   - Checked sheets: 13
   - Checked items: 296
   - Navigation adjacency errors: 0
4. Route smoke checks for JOVAC pages/endpoints
   - Key routes responded successfully (expected 200/302 by endpoint type).
   - Previous/Next endpoint redirects preserved `?sheet=` context.

### Automated Tests

- Ran: `python manage.py test student administration practice --verbosity 2 --noinput`
- Result: 26 tests executed, 25 passed, 1 failed.
- Remaining failure:
  - Test: `student.tests_profile_api.ProfileAPITests.test_patch_profile_valid`
  - Issue: `coins_earned` assertion expected `> 0`, actual value `0`.
  - Note: this appears unrelated to JOVAC Previous/Next navigation changes.

## Current Outcome

- JOVAC tutorial/assignment Previous and Next now navigate deterministically one-by-one.
- Sheet context is preserved across page transitions.
- JOVAC MCQ routing/rendering path is improved and integrated with sheet-aware behavior.
- Migration consistency checks are clean.
- One unrelated profile API test remains to be fixed if full green test suite is required.