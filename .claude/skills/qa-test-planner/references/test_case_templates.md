# Test Case Templates Reference

This document provides standardized test case templates for each test type supported by the QA Test Planner skill. Each template includes structure definitions and filled-in examples.

---

## Table of Contents

1. [Functional Test Case Template](#functional-test-case-template)
2. [Integration Test Case Template](#integration-test-case-template)
3. [E2E Test Case Template](#e2e-test-case-template)
4. [Accessibility Test Case Template](#accessibility-test-case-template)
5. [Performance Test Case Template](#performance-test-case-template)

---

## Functional Test Case Template

### Template Structure

```
ID:               TC-FUNC-XXX
Title:            [Action] [Object] [Condition]
Type:             Functional
Priority:         [Critical | High | Medium | Low]
Feature Area:     [Module / Component name]
Preconditions:    [Required state before test execution]
Test Data:        [Specific data inputs needed]
Steps:            [Numbered sequence of actions]
Expected Results: [Observable outcomes that indicate pass/fail]
Postconditions:   [Expected state after test execution]
```

### Example: User Registration Validation

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-FUNC-001                                    |
| **Title**        | Verify user registration with valid email      |
| **Type**         | Functional                                     |
| **Priority**     | High                                           |
| **Feature Area** | User Management - Registration                 |
| **Status**       | Not Executed                                   |

**Preconditions:**
- Application is running and accessible
- Registration page is reachable
- No existing account with test email address

**Test Data:**
- Email: testuser_001@example.com
- Password: SecureP@ss123
- Name: Test User

**Steps:**
1. Navigate to the registration page (`/register`)
2. Enter "Test User" in the Full Name field
3. Enter "testuser_001@example.com" in the Email field
4. Enter "SecureP@ss123" in the Password field
5. Enter "SecureP@ss123" in the Confirm Password field
6. Click the "Create Account" button

**Expected Results:**
- User is redirected to the email verification page
- Success message "Account created. Please verify your email." is displayed
- A verification email is sent to testuser_001@example.com
- User record is created in the database with `verified: false`
- Password is stored as a bcrypt hash, not plaintext

**Postconditions:**
- New user record exists in the `users` table
- Verification token exists in the `email_verifications` table

---

### Example: Input Validation - Invalid Email Format

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-FUNC-002                                    |
| **Title**        | Reject registration with invalid email format  |
| **Type**         | Functional                                     |
| **Priority**     | Medium                                         |
| **Feature Area** | User Management - Registration                 |

**Preconditions:**
- Application is running and accessible
- Registration page is reachable

**Test Data:**
- Invalid emails: `notanemail`, `user@`, `@domain.com`, `user@.com`, `user@domain`

**Steps:**
1. Navigate to the registration page
2. Enter a valid name and password
3. Enter each invalid email from test data, one at a time
4. Attempt to submit the form

**Expected Results:**
- Form submission is prevented for each invalid email
- Inline validation error "Please enter a valid email address" is displayed
- No API call is made to the backend
- No user record is created in the database

---

## Integration Test Case Template

### Template Structure

```
ID:               TC-INTG-XXX
Title:            [Service A] [operation] with [Service B] [expected outcome]
Type:             Integration
Priority:         [Critical | High | Medium | Low]
Feature Area:     [Service / API boundary being tested]
Services:         [List of services involved]
Preconditions:    [Service availability, data state]
Request:          [API method, endpoint, headers, payload]
Expected Results: [Response code, body, side effects across services]
Rollback:         [Cleanup steps to reset state]
```

### Example: Order Service Creates Payment Intent

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-INTG-001                                    |
| **Title**        | Order creation triggers payment intent in Stripe|
| **Type**         | Integration                                    |
| **Priority**     | Critical                                       |
| **Feature Area** | Order Service <-> Payment Service               |

**Services Involved:**
- Order Service (internal)
- Payment Service (internal)
- Stripe API (external)

**Preconditions:**
- Order Service is running and healthy
- Payment Service is running and connected to Stripe (test mode)
- Valid Stripe test API keys are configured
- Test user has items in their cart
- Test user has a valid shipping address on file

**Request:**
```
POST /api/v1/orders
Authorization: Bearer <valid_user_token>
Content-Type: application/json

{
  "cart_id": "cart_test_001",
  "shipping_address_id": "addr_test_001",
  "payment_method": "card"
}
```

**Expected Results:**
- Order Service returns `201 Created` with order ID
- Order record is created with status `payment_pending`
- Payment Service receives the order event via message queue
- Stripe `PaymentIntent` is created with correct amount
- Payment Service updates order status to `payment_processing`
- Stripe webhook confirms payment, status becomes `payment_confirmed`

**Verification Queries:**
```sql
-- Verify order was created
SELECT id, status, total FROM orders WHERE cart_id = 'cart_test_001';
-- Expected: status = 'payment_confirmed'

-- Verify payment record
SELECT stripe_payment_intent_id, status FROM payments WHERE order_id = '<order_id>';
-- Expected: status = 'succeeded'
```

**Rollback:**
- Cancel the Stripe PaymentIntent via API
- Delete test order and payment records

---

### Example: User Service Syncs with Email Provider

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-INTG-002                                    |
| **Title**        | User profile update syncs to email marketing   |
| **Type**         | Integration                                    |
| **Priority**     | Medium                                         |
| **Feature Area** | User Service <-> Email Marketing Service       |

**Services Involved:**
- User Service (internal)
- Email Marketing Service (e.g., SendGrid, Mailchimp)

**Preconditions:**
- User Service is running
- Email marketing API is accessible (sandbox/test mode)
- Test user exists and is subscribed to marketing list

**Request:**
```
PATCH /api/v1/users/user_test_001
Authorization: Bearer <valid_token>
Content-Type: application/json

{
  "first_name": "Updated",
  "email_preferences": { "marketing": true, "product_updates": false }
}
```

**Expected Results:**
- User Service returns `200 OK` with updated profile
- User record is updated in the database
- A `user.profile.updated` event is published to the message queue
- Email marketing service subscriber record is updated within 30 seconds
- Marketing list membership reflects new preferences

---

## E2E Test Case Template

### Template Structure

```
ID:               TC-E2E-XXX
Title:            [User persona] can [complete workflow] [condition]
Type:             E2E
Priority:         [Critical | High | Medium | Low]
Feature Area:     [User-facing workflow name]
User Persona:     [Role / type of user]
Browser/Device:   [Target browser and device]
Preconditions:    [Application state, test accounts, data]
User Journey:     [Step-by-step user actions with UI verifications]
Expected Results: [Final outcome from user perspective]
```

### Example: Customer Completes Checkout

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-E2E-001                                     |
| **Title**        | Customer can complete checkout with credit card |
| **Type**         | E2E                                            |
| **Priority**     | Critical                                       |
| **Feature Area** | Shopping - Checkout Flow                       |
| **User Persona** | Registered Customer                            |
| **Browser**      | Chrome 120+ (Desktop, 1920x1080)               |

**Preconditions:**
- Application is deployed to staging
- Test customer account exists (test_customer@example.com)
- Product catalog has items in stock
- Stripe test mode is enabled

**User Journey:**
1. Navigate to the homepage
   - *Verify*: Homepage loads within 3 seconds, product grid is visible
2. Search for "wireless headphones"
   - *Verify*: Search results appear, at least 1 product matches
3. Click on the first product result
   - *Verify*: Product detail page shows name, price, description, and "Add to Cart" button
4. Click "Add to Cart"
   - *Verify*: Cart icon updates to show "1 item", toast notification appears
5. Click the cart icon to open the cart
   - *Verify*: Cart sidebar shows the product with correct name and price
6. Click "Proceed to Checkout"
   - *Verify*: Checkout page loads with shipping address form
7. Select saved shipping address or enter a new one
   - *Verify*: Address is validated, shipping options appear
8. Select "Standard Shipping ($5.99)"
   - *Verify*: Order summary updates with shipping cost
9. Enter test credit card (4242 4242 4242 4242, exp 12/26, CVC 123)
   - *Verify*: Card field shows Visa icon, no validation errors
10. Click "Place Order"
    - *Verify*: Loading indicator appears, button is disabled
11. Wait for order confirmation
    - *Verify*: Confirmation page shows order number, total, and estimated delivery
    - *Verify*: Confirmation email is received within 2 minutes

**Expected Results:**
- Order is created successfully with correct items and pricing
- Payment is captured via Stripe
- Customer receives order confirmation email
- Order appears in the customer's order history

---

### Example: New User Onboarding Flow

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-E2E-002                                     |
| **Title**        | New user completes onboarding wizard           |
| **Type**         | E2E                                            |
| **Priority**     | High                                           |
| **Feature Area** | User Onboarding                                |
| **User Persona** | First-time Visitor                             |
| **Browser**      | Safari (iPhone 15, 390x844)                    |

**Preconditions:**
- Application is deployed to staging
- No existing account with test email

**User Journey:**
1. Open the app from a marketing link
   - *Verify*: Landing page loads, "Get Started" CTA is prominent
2. Tap "Get Started"
   - *Verify*: Registration form appears with social login options
3. Complete registration with email
   - *Verify*: Verification code is sent, input field appears
4. Enter verification code
   - *Verify*: Account is verified, onboarding wizard starts
5. Complete profile setup (name, avatar, preferences)
   - *Verify*: Each step has clear progress indicator
6. Complete the onboarding wizard
   - *Verify*: Dashboard loads with personalized content based on preferences

---

## Accessibility Test Case Template

### Template Structure

```
ID:               TC-A11Y-XXX
Title:            [Component/Page] meets [WCAG criterion]
Type:             Accessibility
Priority:         [Critical | High | Medium | Low]
WCAG Criterion:   [e.g., 1.1.1 Non-text Content, Level A]
Feature Area:     [Page or component being tested]
Tools:            [Automated tools and assistive technologies used]
Preconditions:    [Page state, assistive technology setup]
Test Steps:       [Specific accessibility checks]
Expected Results: [WCAG compliance criteria]
```

### Example: Navigation Menu Keyboard Accessibility

| Field              | Value                                        |
|--------------------|----------------------------------------------|
| **ID**             | TC-A11Y-001                                  |
| **Title**          | Main navigation is fully keyboard accessible |
| **Type**           | Accessibility                                |
| **Priority**       | Critical                                     |
| **WCAG Criterion** | 2.1.1 Keyboard (Level A)                     |
| **Feature Area**   | Global Navigation                            |

**Tools:**
- axe-core browser extension
- NVDA screen reader (Windows) / VoiceOver (macOS)
- Chrome DevTools Accessibility panel

**Preconditions:**
- Page is fully loaded
- Mouse/trackpad is not used during testing
- Screen reader is running

**Test Steps:**
1. Press `Tab` from the browser address bar
   - *Check*: First focusable element in the navigation receives focus
   - *Check*: Focus indicator (outline) is clearly visible with at least 3:1 contrast
2. Continue pressing `Tab` through all navigation items
   - *Check*: Focus moves in logical left-to-right, top-to-bottom order
   - *Check*: No element is skipped, no focus trap occurs
3. When focused on a dropdown menu trigger, press `Enter` or `Space`
   - *Check*: Dropdown menu opens
   - *Check*: Screen reader announces "expanded" state
4. Press `Arrow Down` to navigate dropdown items
   - *Check*: Focus moves to each dropdown item sequentially
5. Press `Escape` to close the dropdown
   - *Check*: Dropdown closes
   - *Check*: Focus returns to the trigger element
   - *Check*: Screen reader announces "collapsed" state
6. Press `Tab` past the last navigation item
   - *Check*: Focus moves to the main content area (skip navigation works)

**Expected Results:**
- All navigation items are reachable via keyboard alone
- Focus order is logical and predictable
- Focus indicator is always visible (WCAG 2.4.7 Focus Visible)
- Dropdown menus support `Enter`, `Space`, `Arrow`, and `Escape` keys
- Screen reader announces all interactive states (expanded/collapsed)
- Skip navigation link is present and functional

---

### Example: Form Color Contrast and Labels

| Field              | Value                                        |
|--------------------|----------------------------------------------|
| **ID**             | TC-A11Y-002                                  |
| **Title**          | Login form meets color contrast and labeling requirements |
| **Type**           | Accessibility                                |
| **Priority**       | High                                         |
| **WCAG Criterion** | 1.4.3 Contrast (Level AA), 1.3.1 Info and Relationships (Level A) |
| **Feature Area**   | Authentication - Login Form                  |

**Tools:**
- axe-core / Lighthouse accessibility audit
- Colour Contrast Analyser (CCA)
- Browser DevTools

**Preconditions:**
- Login page is loaded
- Both light and dark themes are tested

**Test Steps:**
1. Run automated accessibility scan (axe-core)
   - *Check*: Zero violations related to contrast or form labels
2. Inspect each form label with DevTools
   - *Check*: Every `<input>` has an associated `<label>` with matching `for`/`id`
   - *Check*: Placeholder text is NOT the only label
3. Measure color contrast of form labels against background
   - *Check*: Ratio is at least 4.5:1 for normal text
   - *Check*: Ratio is at least 3:1 for large text (18px+ or 14px+ bold)
4. Measure color contrast of input field text against field background
   - *Check*: Ratio is at least 4.5:1
5. Measure color contrast of error messages
   - *Check*: Error text meets 4.5:1 contrast ratio
   - *Check*: Errors are not communicated by color alone (icon or text present)
6. Check focus styles on form fields
   - *Check*: Focus indicator has at least 3:1 contrast against adjacent colors

**Expected Results:**
- All text meets WCAG 2.1 AA contrast ratios
- All form fields have proper programmatic labels
- Error states are perceivable without relying on color alone
- Form is usable in both light and dark themes

---

## Performance Test Case Template

### Template Structure

```
ID:               TC-PERF-XXX
Title:            [Metric] for [scenario] under [load condition]
Type:             Performance
Priority:         [Critical | High | Medium | Low]
Feature Area:     [Feature or endpoint being tested]
Tool:             [k6, Lighthouse, Artillery, JMeter, etc.]
Load Profile:     [Users, ramp-up, duration, think time]
Metrics:          [What is measured and thresholds]
Preconditions:    [Environment, data volume, monitoring setup]
Test Steps:       [Execution procedure]
Expected Results: [Pass/fail thresholds for each metric]
```

### Example: API Response Time Under Load

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-PERF-001                                    |
| **Title**        | Product search API p95 latency under 500 concurrent users |
| **Type**         | Performance                                    |
| **Priority**     | High                                           |
| **Feature Area** | Product Search API                             |
| **Tool**         | k6                                             |

**Load Profile:**
- Virtual Users: 500 concurrent
- Ramp-up: 0 to 500 over 2 minutes
- Steady state: 500 users for 10 minutes
- Ramp-down: 500 to 0 over 1 minute
- Think time: 1-3 seconds between requests

**Metrics & Thresholds:**

| Metric                | Threshold    | Action if Failed      |
|-----------------------|--------------|-----------------------|
| p50 response time     | < 100ms      | Investigate           |
| p95 response time     | < 500ms      | Block release         |
| p99 response time     | < 1000ms     | Investigate           |
| Error rate            | < 0.1%       | Block release         |
| Throughput            | > 200 req/s  | Investigate           |
| CPU utilization       | < 80%        | Scale infrastructure  |
| Memory utilization    | < 75%        | Investigate leaks     |

**Preconditions:**
- Performance test environment is isolated (no other traffic)
- Database contains 100,000+ product records
- Search index is rebuilt and warmed
- Application monitoring (APM) is enabled
- Database query logging is enabled for slow queries

**Test Steps:**
1. Reset application metrics and monitoring baselines
2. Execute k6 load test script with the defined profile
3. Monitor real-time metrics dashboard during execution
4. Capture results after test completion
5. Analyze p50/p95/p99 latency, error rate, and throughput
6. Check for memory leaks (compare memory before and after)
7. Review slow query log for database bottlenecks

**Expected Results:**
- All latency thresholds are met
- Error rate stays below 0.1%
- No memory leaks detected (memory stabilizes during steady state)
- No database connection pool exhaustion
- Application recovers to normal latency within 30 seconds of ramp-down

---

### Example: Page Load Performance (Core Web Vitals)

| Field            | Value                                          |
|------------------|------------------------------------------------|
| **ID**           | TC-PERF-002                                    |
| **Title**        | Homepage Core Web Vitals meet "Good" thresholds|
| **Type**         | Performance                                    |
| **Priority**     | High                                           |
| **Feature Area** | Homepage                                       |
| **Tool**         | Lighthouse CI / Web Vitals                     |

**Metrics & Thresholds (Core Web Vitals):**

| Metric                          | Good       | Needs Improvement | Poor     |
|---------------------------------|------------|--------------------|----------|
| Largest Contentful Paint (LCP)  | < 2.5s     | 2.5s - 4.0s        | > 4.0s   |
| Interaction to Next Paint (INP) | < 200ms    | 200ms - 500ms      | > 500ms  |
| Cumulative Layout Shift (CLS)   | < 0.1      | 0.1 - 0.25         | > 0.25   |
| First Contentful Paint (FCP)    | < 1.8s     | 1.8s - 3.0s        | > 3.0s   |
| Time to First Byte (TTFB)       | < 800ms    | 800ms - 1800ms     | > 1800ms |

**Preconditions:**
- Application is deployed to staging with production-like CDN configuration
- Test is run on a throttled connection (4G simulation: 9 Mbps down, 1.5 Mbps up, 150ms RTT)
- Browser cache is cleared before each run
- Test is run 5 times and median values are used

**Test Steps:**
1. Configure Lighthouse with mobile throttling preset
2. Run Lighthouse audit on the homepage 5 times
3. Record each Core Web Vital metric
4. Calculate median values across all runs
5. Compare medians against "Good" thresholds
6. If any metric is in "Needs Improvement" or "Poor", identify the contributing factors

**Expected Results:**
- All Core Web Vitals are in the "Good" range (median of 5 runs)
- Lighthouse Performance score is 90+
- No render-blocking resources in the critical path
- Images are properly sized and use modern formats (WebP/AVIF)
- JavaScript bundle size is under 200KB (gzipped)
