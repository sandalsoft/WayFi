# Bug Report Templates Reference

This document provides standardized bug report templates organized by severity and type. Each template includes a classification guide and a filled-in example.

---

## Table of Contents

1. [Severity Classification Guide](#severity-classification-guide)
2. [Critical Bug Template](#critical-bug-template)
3. [UI/UX Bug Template](#uiux-bug-template)
4. [Performance Bug Template](#performance-bug-template)
5. [Regression Bug Template](#regression-bug-template)

---

## Severity Classification Guide

Use the following matrix to classify bug severity consistently across the team.

### Severity Levels

| Severity     | Definition                                       | Examples                                          | Response Time    | Resolution SLA  |
|-------------|--------------------------------------------------|---------------------------------------------------|------------------|-----------------|
| **Critical** | System is down, data loss/corruption, security breach, or complete feature failure with no workaround | Application crash, payment processing failure, authentication bypass, data deletion bug | 30 min acknowledge | 4 hours |
| **Major**    | Core feature is broken or severely degraded, no reasonable workaround exists | Cannot submit forms, broken navigation flow, incorrect calculations, API returning wrong data | 2 hours acknowledge | 24 hours |
| **Minor**    | Feature works but with issues, a workaround exists | Sorting not working on one column, minor display issues on specific browsers, slow but functional operation | 1 business day | Current sprint |
| **Trivial**  | Cosmetic issue, typo, minor visual inconsistency that does not affect functionality | Typo in label, 1px alignment issue, slightly wrong color shade, extra whitespace | 1 week | Backlog |

### Severity Decision Tree

```
Is the system completely unusable or is there a security risk?
├── YES → CRITICAL
└── NO → Is core functionality broken with no workaround?
    ├── YES → MAJOR
    └── NO → Is functionality impaired but usable?
        ├── YES → MINOR
        └── NO → TRIVIAL
```

### Priority vs. Severity

Severity describes the technical impact. Priority describes the business urgency. They often align but not always:

| Scenario                                     | Severity | Priority |
|----------------------------------------------|----------|----------|
| Login is broken for all users                | Critical | P1       |
| Typo on the CEO's bio page (high visibility) | Trivial  | P2       |
| Export feature broken (used by 2 users)      | Major    | P3       |
| Color mismatch on rarely visited admin page  | Trivial  | P4       |

---

## Critical Bug Template

Use this template for system crashes, data loss, security vulnerabilities, and complete feature failures.

### Template

```markdown
# [CRITICAL] Bug Title - Brief description of the catastrophic issue

**Bug ID:** BUG-CRIT-YYYYMMDD-XXX
**Severity:** CRITICAL
**Priority:** P1 - Immediate
**Status:** Open - Escalated
**Assigned To:** [On-call engineer / Team lead]
**Reporter:** [Name]
**Date:** [YYYY-MM-DD HH:MM UTC]

## Impact

- **Users Affected:** [All users / Segment / Count]
- **Revenue Impact:** [Estimated $ impact or "Unable to process transactions"]
- **Data Impact:** [Data loss, corruption, or exposure details]
- **Duration:** [How long has this been occurring?]

## Environment

- **Production URL:** [URL where issue occurs]
- **App Version / Deploy:** [Version, commit SHA, or deploy timestamp]
- **Infrastructure:** [Affected servers, regions, services]

## Steps to Reproduce

1. [Exact steps]
2. [Include specific data if relevant]
3. [Note: reproduction rate: Always / X%]

## Expected Behavior

[What should happen]

## Actual Behavior

[What happens instead - include error messages verbatim]

## Evidence

- **Error Logs:** [Link to log aggregator query]
- **Metrics:** [Link to dashboard showing the spike/drop]
- **Screenshots:** [Attached]
- **Stack Trace:**
  ```
  [Paste full stack trace]
  ```

## Immediate Actions Taken

- [ ] Incident channel created: [#incident-XXXX]
- [ ] On-call engineer notified
- [ ] Status page updated
- [ ] Customer communication drafted
- [ ] Rollback evaluated: [Possible/Not possible - reason]

## Root Cause (to be filled post-resolution)

[Analysis of what caused the issue]

## Fix Verification

- [ ] Fix deployed to staging
- [ ] Reproduction steps no longer trigger the bug
- [ ] Monitoring confirms metrics returned to normal
- [ ] Post-incident review scheduled
```

### Example: Payment Processing Failure

# [CRITICAL] Payment processing fails for all credit card transactions

**Bug ID:** BUG-CRIT-20260115-001
**Severity:** CRITICAL
**Priority:** P1 - Immediate
**Status:** Open - Escalated
**Assigned To:** @payment-team-lead
**Reporter:** Monitoring Alert / QA Team
**Date:** 2026-01-15 14:32 UTC

**Impact:**
- Users Affected: All customers attempting checkout (~2,400/hour)
- Revenue Impact: Estimated $15,000/hour in lost transactions
- Data Impact: No data loss; transactions fail cleanly
- Duration: First alert at 14:28 UTC, ongoing

**Environment:**
- Production: checkout.example.com
- App Version: v3.12.1 (deployed 2026-01-15 13:45 UTC)
- Infrastructure: payment-service pods in us-east-1

**Steps to Reproduce:**
1. Add any item to cart
2. Proceed to checkout
3. Enter any credit card (including Stripe test cards)
4. Click "Place Order"
5. Observe: spinner runs for 30 seconds, then "Payment failed" error

**Actual Behavior:**
Payment Service returns HTTP 502. Stripe API returns `invalid_api_key` error. Root cause: deployment v3.12.1 overwrote the Stripe secret key environment variable with an empty string.

---

## UI/UX Bug Template

Use this template for visual defects, layout issues, interaction problems, and design inconsistencies.

### Template

```markdown
# [UI/UX] Bug Title - Component and visual issue description

**Bug ID:** BUG-UI-YYYYMMDD-XXX
**Severity:** [Minor | Trivial]
**Priority:** [P3 | P4]
**Status:** Open
**Assigned To:** [Frontend developer]
**Reporter:** [Name]
**Date:** [YYYY-MM-DD]

## Affected Component

- **Page/Route:** [URL or route path]
- **Component:** [Component name or region of the page]
- **Design Reference:** [Figma link or design spec URL]

## Environment

- **Browser:** [Name and version]
- **OS:** [Operating system and version]
- **Viewport:** [Width x Height in pixels]
- **Device:** [Desktop / Mobile device name]
- **Theme:** [Light / Dark / System]
- **Zoom Level:** [100% / 150% / 200%]

## Visual Evidence

| Expected (Design) | Actual (Implementation) |
|--------------------|-------------------------|
| ![Expected](design_screenshot_url) | ![Actual](actual_screenshot_url) |

## Description

**What is wrong:**
[Specific description of the visual/interaction issue]

**What it should look like:**
[Reference to design spec or description of correct appearance]

## Specific Deviations

| Property        | Expected         | Actual           |
|----------------|------------------|------------------|
| Font size       | 16px             | 14px             |
| Color           | #1A1A2E          | #333333          |
| Padding         | 16px             | 12px             |
| Border radius   | 8px              | 4px              |
| Alignment       | Center           | Left             |

## Steps to Reproduce

1. [Navigate to the page]
2. [Set viewport/device/theme if relevant]
3. [Describe the action or state that reveals the issue]

## Cross-Browser / Cross-Device Impact

| Browser/Device          | Affected? | Notes           |
|------------------------|-----------|-----------------|
| Chrome (Desktop)        | Yes/No    |                 |
| Firefox (Desktop)       | Yes/No    |                 |
| Safari (Desktop)        | Yes/No    |                 |
| Chrome (Android)        | Yes/No    |                 |
| Safari (iOS)            | Yes/No    |                 |
```

### Example: Button Misalignment on Mobile

# [UI/UX] Checkout "Place Order" button overlaps price summary on mobile

**Bug ID:** BUG-UI-20260120-003
**Severity:** Minor
**Priority:** P3
**Status:** Open
**Assigned To:** @frontend-team
**Reporter:** QA Team
**Date:** 2026-01-20

**Affected Component:**
- Page/Route: `/checkout/review`
- Component: OrderSummary / CheckoutActions
- Design Reference: [Figma - Checkout Mobile](https://figma.com/file/xxx)

**Environment:**
- Browser: Safari 17.2
- OS: iOS 17.2
- Viewport: 390x844 (iPhone 15)
- Theme: Light

**Description:**
The "Place Order" button overlaps the order total price text when the order summary contains 4+ line items. The button's fixed positioning does not account for the expanded summary height.

**Specific Deviations:**

| Property             | Expected         | Actual               |
|---------------------|------------------|-----------------------|
| Button position      | Below summary    | Overlapping summary   |
| Gap between elements | 24px             | -16px (overlapping)   |
| Summary scrollable   | Yes              | No                    |

---

## Performance Bug Template

Use this template for slow responses, memory leaks, high resource consumption, and degraded throughput.

### Template

```markdown
# [PERF] Bug Title - What is slow/degraded and by how much

**Bug ID:** BUG-PERF-YYYYMMDD-XXX
**Severity:** [Critical | Major | Minor]
**Priority:** [P1 | P2 | P3]
**Status:** Open
**Assigned To:** [Backend/Frontend developer]
**Reporter:** [Name]
**Date:** [YYYY-MM-DD]

## Performance Issue Summary

- **Affected Operation:** [API endpoint, page load, background job, etc.]
- **Current Performance:** [Measured value - e.g., 4.2s p95 response time]
- **Expected Performance:** [Threshold - e.g., < 500ms p95]
- **Degradation Factor:** [X times slower than expected]
- **Since When:** [Date/version when degradation started, if known]

## Environment

- **Environment:** [Production / Staging]
- **Infrastructure:** [Server specs, instance types, region]
- **Load Conditions:** [Concurrent users, request rate when issue occurs]
- **Data Volume:** [Database size, record counts relevant to the issue]

## Metrics & Evidence

### Response Time Distribution

| Percentile | Current  | Baseline | Threshold |
|-----------|----------|----------|-----------|
| p50        | [value]  | [value]  | [value]   |
| p95        | [value]  | [value]  | [value]   |
| p99        | [value]  | [value]  | [value]   |

### Resource Utilization

| Resource       | Current  | Normal   | Limit     |
|---------------|----------|----------|-----------|
| CPU            | [value]  | [value]  | [value]   |
| Memory         | [value]  | [value]  | [value]   |
| DB Connections | [value]  | [value]  | [value]   |
| Disk I/O       | [value]  | [value]  | [value]   |

### Evidence Links

- **APM Dashboard:** [Link]
- **Slow Query Log:** [Link]
- **Flame Graph / Profile:** [Link]
- **Metrics Graph:** [Link showing the degradation over time]

## Steps to Reproduce

1. [Describe how to trigger the slow operation]
2. [Include specific data/payload if relevant]
3. [Note conditions: load level, data size, etc.]

## Suspected Root Cause

[Analysis of what might be causing the performance issue - e.g., missing index, N+1 query, unoptimized algorithm, memory leak]

## Proposed Fix

[Suggested approach to resolve the issue]
```

### Example: Dashboard API Slow Query

# [PERF] Dashboard summary API response time degraded to 4.2s (target: 500ms)

**Bug ID:** BUG-PERF-20260118-001
**Severity:** Major
**Priority:** P2
**Status:** Open
**Assigned To:** @backend-team
**Reporter:** Performance Monitoring
**Date:** 2026-01-18

**Performance Issue Summary:**
- Affected Operation: `GET /api/v1/dashboard/summary`
- Current Performance: 4,200ms p95
- Expected Performance: < 500ms p95
- Degradation Factor: 8.4x slower
- Since When: Gradual degradation since v3.10.0 (2025-12-01)

**Suspected Root Cause:**
The dashboard summary query joins 5 tables without proper indexing on the `created_at` filter columns. As the `events` table grew past 10M rows, the query plan switched from index scan to sequential scan.

**Proposed Fix:**
1. Add composite index on `events(user_id, created_at)`
2. Add materialized view for dashboard aggregations
3. Implement query result caching with 5-minute TTL

---

## Regression Bug Template

Use this template when a previously working feature breaks after a code change, deployment, or dependency update.

### Template

```markdown
# [REGRESSION] Bug Title - What broke and when

**Bug ID:** BUG-REG-YYYYMMDD-XXX
**Severity:** [Critical | Major]
**Priority:** [P1 | P2]
**Status:** Open
**Assigned To:** [Developer who made the change / Team lead]
**Reporter:** [Name]
**Date:** [YYYY-MM-DD]

## Regression Summary

- **Feature Affected:** [Feature name and description]
- **Last Known Working Version:** [Version / commit SHA / date]
- **First Broken Version:** [Version / commit SHA / date]
- **Introducing Change:** [PR link, commit SHA, or deploy ID if identified]

## Change Analysis

### Suspected Introducing Change

- **PR/Commit:** [Link]
- **Author:** [Name]
- **Description:** [What the change was supposed to do]
- **Files Changed:** [List key files]
- **Why It Broke:** [Analysis of how the change caused the regression]

### Git Bisect Results (if performed)

```
First bad commit: [SHA]
Author: [Name]
Date: [Date]
Message: [Commit message]
```

## Current Behavior (Broken)

[Describe what happens now]

## Previous Behavior (Expected)

[Describe what used to happen / should happen]

## Steps to Reproduce

1. [Steps to see the regression]
2. [Include version/environment details]

## Test Coverage Analysis

- **Existing Tests:** [Were there tests for this feature? Did they pass?]
- **Test Gap:** [What test case was missing that would have caught this?]
- **Proposed Test:** [Describe a test to add to prevent future regression]

## Impact Assessment

- **Users Affected:** [Scope of impact]
- **Workaround Available:** [Yes/No - describe if yes]
- **Related Features:** [Other features that may be affected by the same change]

## Resolution Plan

- [ ] Identify the introducing commit (git bisect)
- [ ] Determine if rollback is faster than forward-fix
- [ ] Implement fix or rollback
- [ ] Add regression test to prevent recurrence
- [ ] Verify fix in staging
- [ ] Deploy fix to production
- [ ] Confirm feature works as expected
```

### Example: Search Filters Regression

# [REGRESSION] Search price filter returns no results after catalog service refactor

**Bug ID:** BUG-REG-20260122-001
**Severity:** Major
**Priority:** P2
**Status:** Open
**Assigned To:** @catalog-team
**Reporter:** QA Team
**Date:** 2026-01-22

**Regression Summary:**
- Feature Affected: Product search - price range filter
- Last Known Working Version: v3.11.2 (2026-01-15)
- First Broken Version: v3.12.0 (2026-01-20)
- Introducing Change: PR #1847 "Refactor catalog query builder"

**Change Analysis:**
PR #1847 refactored the catalog query builder to use a new ORM pattern. The price filter previously used `price_cents` (integer) but the new query builder references `price` (decimal) which does not exist as a column, causing the WHERE clause to silently return no results instead of erroring.

**Test Coverage Analysis:**
- Existing Tests: Unit tests for query builder existed but used mocked data
- Test Gap: No integration test that actually executes the price filter query against the database
- Proposed Test: Add integration test `test_search_with_price_filter_returns_results()` that seeds products and verifies filter results

**Impact Assessment:**
- Users Affected: Any user applying a price filter (~30% of searches)
- Workaround: Users can search without price filter and manually scroll
- Related Features: Other numeric filters (rating, weight) may have the same issue
