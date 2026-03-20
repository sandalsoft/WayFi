# Figma Design Validation Reference

This document provides guidance for validating implementations against Figma designs, including MCP integration workflows, visual comparison checklists, and common design-to-code gaps.

---

## Table of Contents

1. [Using Figma MCP for Design Validation](#using-figma-mcp-for-design-validation)
2. [Visual Comparison Checklist](#visual-comparison-checklist)
3. [Component Design Compliance Checklist](#component-design-compliance-checklist)
4. [Design-to-Code Validation Workflow](#design-to-code-validation-workflow)
5. [Common Design Implementation Gaps](#common-design-implementation-gaps)

---

## Using Figma MCP for Design Validation

The Figma MCP (Model Context Protocol) server allows Claude to directly access Figma files, inspect design tokens, and compare implementations against design specifications.

### Prerequisites

- Figma MCP server is configured and running
- Valid Figma access token is set in environment
- Figma file URLs or keys are available for the project

### Available MCP Operations

| Operation               | Description                                         | Use Case                                        |
|------------------------|-----------------------------------------------------|-------------------------------------------------|
| `get_file`             | Retrieve the full Figma file structure              | Understanding overall page/frame organization   |
| `get_file_nodes`       | Get specific nodes by ID                            | Inspecting individual components or frames      |
| `get_file_styles`      | List all styles (colors, text, effects)             | Extracting design tokens                        |
| `get_file_components`  | List all components and variants                    | Mapping design components to code components    |
| `get_image`            | Export frames/nodes as images                       | Visual comparison screenshots                   |
| `get_file_component_sets` | Get component sets with all variants            | Understanding component variant structures      |

### Extracting Design Tokens via MCP

Use the Figma MCP to extract and verify design tokens match the implementation:

**Colors:**
```
1. Call get_file_styles to retrieve all color styles
2. Extract fill colors, stroke colors, and opacity values
3. Compare against CSS custom properties or theme tokens
4. Flag any mismatches (hex values, opacity, gradient stops)
```

**Typography:**
```
1. Call get_file_styles for text styles
2. Extract: font-family, font-size, font-weight, line-height, letter-spacing
3. Compare against CSS typography definitions
4. Verify responsive type scale (if defined in Figma)
```

**Spacing and Layout:**
```
1. Call get_file_nodes for a specific frame
2. Extract: padding, gap, auto-layout properties
3. Map to CSS: padding, margin, gap, flexbox/grid properties
4. Verify alignment (top, center, bottom, stretch)
```

### MCP-Powered Validation Workflow

```
Step 1: Identify the Figma frame/component to validate
        → Use get_file or get_file_components to locate the node

Step 2: Extract design specifications
        → Use get_file_nodes with the node ID
        → Record: dimensions, colors, typography, spacing, effects

Step 3: Capture implementation state
        → Take a screenshot of the implemented component
        → Extract computed styles from the DOM

Step 4: Compare specifications
        → Diff design values against implementation values
        → Flag deviations outside acceptable tolerance

Step 5: Generate validation report
        → List all checked properties
        → Mark pass/fail for each
        → Include visual comparison (Figma export vs. screenshot)
```

### Tolerance Thresholds

Not all differences are bugs. Use these tolerances when comparing design to implementation:

| Property           | Acceptable Tolerance | Notes                                        |
|-------------------|---------------------|----------------------------------------------|
| Dimensions (px)    | +/- 1px             | Sub-pixel rendering may cause 1px variance   |
| Colors (hex)       | Exact match          | No tolerance; colors must match design tokens|
| Font size          | Exact match          | Must match the design spec exactly           |
| Line height        | +/- 1px              | Browser rendering may vary slightly          |
| Spacing/padding    | +/- 2px              | Allow minor variance for responsive layouts  |
| Border radius      | Exact match          | Visually noticeable if off                   |
| Opacity            | +/- 0.02             | Minor rendering differences                  |
| Shadow (blur/spread)| +/- 1px             | Shadow rendering varies across browsers      |

---

## Visual Comparison Checklist

Use this checklist when comparing an implemented UI against the Figma design.

### Spacing

- [ ] **Outer margins** match the design (page gutters, section spacing)
- [ ] **Inner padding** of containers matches the design
- [ ] **Gap between elements** matches (flex gap, grid gap, or margin)
- [ ] **Consistent spacing scale** is used (e.g., 4px, 8px, 12px, 16px, 24px, 32px, 48px)
- [ ] **Alignment** is correct (left, center, right, justify)
- [ ] **Vertical rhythm** is maintained (consistent line-height multiples)

### Colors

- [ ] **Primary brand colors** match the design tokens exactly
- [ ] **Secondary/accent colors** match the design tokens
- [ ] **Background colors** match for all sections/cards/modals
- [ ] **Text colors** match for headings, body, captions, links
- [ ] **Border colors** match (dividers, input borders, card borders)
- [ ] **Hover/active/focus state colors** match the design
- [ ] **Disabled state colors** are correct (reduced opacity or gray)
- [ ] **Dark mode colors** match dark theme Figma frames (if applicable)
- [ ] **Gradient directions and color stops** match the design
- [ ] **Opacity levels** are correct for overlays, backgrounds, and disabled states

### Typography

- [ ] **Font family** matches (including fallback stack)
- [ ] **Font weights** are correct (400 regular, 500 medium, 600 semibold, 700 bold)
- [ ] **Font sizes** match the type scale for each element level
- [ ] **Line heights** match the design
- [ ] **Letter spacing** matches (especially for headings, uppercase text)
- [ ] **Text alignment** matches (left, center, right, justify)
- [ ] **Text decoration** matches (underline for links, strikethrough)
- [ ] **Text truncation** behavior matches (ellipsis, line clamp)
- [ ] **Font rendering** is consistent (antialiasing: `-webkit-font-smoothing`)

### Responsive Breakpoints

- [ ] **Desktop** (1440px+): Layout matches Figma desktop frame
- [ ] **Large tablet** (1024px-1439px): Layout adapts correctly
- [ ] **Tablet** (768px-1023px): Layout matches Figma tablet frame
- [ ] **Mobile landscape** (480px-767px): Layout adapts correctly
- [ ] **Mobile portrait** (320px-479px): Layout matches Figma mobile frame
- [ ] **Column count changes** at correct breakpoints
- [ ] **Navigation transforms** correctly (hamburger menu on mobile)
- [ ] **Images resize** appropriately (no overflow, correct aspect ratio)
- [ ] **Font sizes adjust** at breakpoints (if responsive type scale is defined)
- [ ] **Touch targets** are minimum 44x44px on mobile
- [ ] **Content priority** shifts correctly (key content remains visible)
- [ ] **Horizontal scroll** does not occur at any breakpoint

### Icons and Images

- [ ] **Icon style** matches (outline vs. filled, size, stroke width)
- [ ] **Icon color** matches and changes correctly on hover/active states
- [ ] **Image aspect ratios** are preserved
- [ ] **Image placeholders/loading states** match the design
- [ ] **Avatar sizing** is consistent
- [ ] **Logo** renders correctly at all sizes

### Shadows and Effects

- [ ] **Box shadows** match (x, y, blur, spread, color)
- [ ] **Drop shadows** vs. **inner shadows** are correct
- [ ] **Blur effects** match (backdrop-filter, filter)
- [ ] **Border styles** match (solid, dashed, width, radius)
- [ ] **Transitions/animations** match the design intent

---

## Component Design Compliance Checklist

Verify each UI component matches its Figma component specification across all states and variants.

### Per-Component Checklist

```markdown
## Component: [Component Name]

**Figma Component:** [Link to Figma component]
**Code Component:** [File path or component name]

### Variants
- [ ] Default / Primary variant matches
- [ ] Secondary variant matches
- [ ] Tertiary / Ghost variant matches
- [ ] Destructive / Danger variant matches
- [ ] Size variants match (sm, md, lg, xl)

### States
- [ ] Default / Rest state matches
- [ ] Hover state matches
- [ ] Active / Pressed state matches
- [ ] Focus state matches (focus ring visible)
- [ ] Disabled state matches (opacity, cursor)
- [ ] Loading state matches (spinner, skeleton)
- [ ] Error state matches (border color, error message position)
- [ ] Selected / Active state matches (for toggles, tabs)

### Content Variations
- [ ] Short text content renders correctly
- [ ] Long text content handles overflow (truncation, wrapping)
- [ ] With icon (leading and trailing positions)
- [ ] Without icon
- [ ] With badge/counter
- [ ] Empty state

### Spacing & Sizing
- [ ] Padding matches Figma auto-layout padding
- [ ] Min-width / max-width constraints match
- [ ] Height matches (fixed or auto-height)
- [ ] Gap between child elements matches

### Accessibility
- [ ] Meets color contrast requirements in all variants
- [ ] Focus indicator is visible and meets WCAG 2.4.7
- [ ] Interactive elements have appropriate ARIA attributes
- [ ] Screen reader announces component correctly
```

### Common Components to Validate

Apply the above checklist to each of these core components:

1. **Button** (primary, secondary, ghost, icon-only, loading)
2. **Input** (text, email, password, search, textarea, with/without label and error)
3. **Select / Dropdown** (single, multi, searchable, with groups)
4. **Checkbox** (unchecked, checked, indeterminate, with label)
5. **Radio** (unselected, selected, group layout)
6. **Toggle / Switch** (off, on, disabled)
7. **Card** (with image, without image, horizontal, vertical)
8. **Modal / Dialog** (sizes, with form, confirmation)
9. **Toast / Notification** (success, error, warning, info)
10. **Table** (header, rows, sorting indicators, pagination, empty state)
11. **Navigation** (top bar, sidebar, breadcrumbs, tabs)
12. **Avatar** (sizes, with image, with initials, group)
13. **Badge** (colors, sizes, dot variant)
14. **Tooltip** (positions: top, right, bottom, left)
15. **Skeleton / Loading** (text lines, cards, table rows)

---

## Design-to-Code Validation Workflow

A step-by-step process for systematically validating that an implementation matches its Figma design.

### Phase 1: Preparation

```
1. Identify all Figma frames/pages relevant to the feature
   - Desktop design frame(s)
   - Tablet design frame(s) (if provided)
   - Mobile design frame(s) (if provided)
   - Component specification pages

2. Document the design tokens referenced
   - Color palette with hex values
   - Typography scale (sizes, weights, line-heights)
   - Spacing scale
   - Border radius values
   - Shadow definitions
   - Breakpoint values

3. List all unique components used in the feature
   - Map each to its Figma component
   - Note which variants and states are used
```

### Phase 2: Static Comparison

```
4. Desktop viewport comparison
   - Set browser to match Figma desktop frame width
   - Screenshot each section/page
   - Overlay or side-by-side compare with Figma export
   - Mark deviations

5. Tablet viewport comparison
   - Set browser to tablet width (768px or as defined)
   - Repeat screenshot and comparison

6. Mobile viewport comparison
   - Set browser to mobile width (375px or as defined)
   - Repeat screenshot and comparison

7. Component-level comparison
   - Inspect each component in isolation
   - Compare computed styles against Figma properties
   - Document deviations per component
```

### Phase 3: Interactive Validation

```
8. Verify interactive states
   - Hover states on buttons, links, cards
   - Focus states on form elements
   - Active/pressed states
   - Disabled states
   - Loading/skeleton states

9. Verify animations and transitions
   - Page transitions
   - Component mount/unmount animations
   - Hover transitions (timing, easing)
   - Loading animations

10. Verify responsive behavior between breakpoints
    - Slowly resize the browser from desktop to mobile
    - Watch for layout breaks, content jumps, or clipping
    - Verify elements reflow smoothly
```

### Phase 4: Reporting

```
11. Generate validation report with:
    - Summary: overall compliance percentage
    - Pass: elements matching design within tolerance
    - Fail: deviations outside tolerance (with screenshots)
    - Not Applicable: elements not present in current implementation phase

12. Categorize failures by severity:
    - Blocking: major layout or color issues visible to all users
    - Important: spacing or typography mismatches
    - Minor: subtle differences only visible in close comparison
    - Deferred: issues in unimplemented responsive variants

13. File bug reports for each failure using the UI/UX bug template
    (see bug_report_templates.md)
```

---

## Common Design Implementation Gaps

These are the most frequently encountered discrepancies between Figma designs and code implementations. Review this list proactively during development to catch issues early.

### 1. Spacing Inconsistencies

**What goes wrong:**
- Developers estimate spacing visually rather than extracting exact values from Figma
- Figma auto-layout padding is not translated to CSS padding/margin correctly
- Gap between elements in Figma auto-layout is implemented with margin instead of flex gap

**How to prevent:**
- Always inspect Figma element spacing numerically (do not eyeball)
- Use a design token system (CSS custom properties) for spacing
- Map Figma auto-layout gap to CSS `gap` property

### 2. Typography Drift

**What goes wrong:**
- Wrong font weight used (e.g., 500 vs. 600)
- Line height mismatch (Figma uses px, CSS uses unitless ratio)
- Letter spacing not applied (Figma shows it but developer misses it)
- Font family fallback stack causes different rendering

**How to prevent:**
- Define a typography scale in code that mirrors the Figma text styles
- Convert Figma line-height from px to unitless (e.g., 24px on 16px font = 1.5)
- Convert Figma letter spacing from percentage to em (e.g., 2% = 0.02em)
- Verify font files are loaded correctly (check DevTools network tab)

### 3. Color Token Mismatches

**What goes wrong:**
- Hardcoded hex values instead of design tokens
- Wrong shade of a color (e.g., gray-400 vs. gray-500)
- Opacity applied in Figma but not in CSS (or vice versa)
- Dark mode colors not mapped correctly

**How to prevent:**
- Use CSS custom properties that map directly to Figma color styles
- Never hardcode colors; always reference tokens
- Check that Figma "layer opacity" is translated to CSS `opacity` on the correct element
- Audit dark mode tokens separately from light mode

### 4. Missing Interaction States

**What goes wrong:**
- Hover state exists in Figma but not implemented
- Focus state is missing or uses browser default (ugly outline)
- Active/pressed state is not implemented
- Disabled state looks different from design

**How to prevent:**
- For each interactive component, check all states in Figma: rest, hover, focus, active, disabled
- Implement focus-visible for keyboard users (not focus which triggers on click too)
- Test disabled state explicitly (opacity, cursor, pointer-events)

### 5. Responsive Breakpoint Issues

**What goes wrong:**
- Figma designs only show 3 breakpoints but there are gaps in between
- Column count does not change at the right breakpoint
- Elements that should stack on mobile remain side-by-side
- Font sizes do not scale down for mobile

**How to prevent:**
- Establish exact breakpoint values with the design team
- Test at breakpoint boundaries (1px above and below each breakpoint)
- Test "in-between" widths that may not have explicit Figma designs
- Use container queries where appropriate for component-level responsiveness

### 6. Icon and Image Issues

**What goes wrong:**
- SVG icons have different stroke widths than the design
- Icons are the wrong size (design uses 20px, code uses 24px)
- Images are stretched or cropped differently than design intent
- Missing alt text for images (not a visual issue but an implementation gap)

**How to prevent:**
- Export icons directly from Figma rather than sourcing from icon libraries
- Verify icon size matches the design (width, height, viewBox)
- Use `object-fit: cover` vs. `contain` intentionally based on design
- Include alt text for all meaningful images

### 7. Shadow and Elevation Differences

**What goes wrong:**
- Box shadow values do not match Figma's drop shadow (x, y, blur, spread, color)
- Figma uses multiple shadows stacked; implementation only has one
- Shadow color opacity is wrong
- Inner shadow vs. drop shadow confusion

**How to prevent:**
- Extract shadow values precisely from Figma (click the shadow effect to see all values)
- Note that Figma's "spread" maps directly to CSS box-shadow spread
- Copy all shadow layers (Figma components often have 2-3 stacked shadows)
- Define shadow tokens (elevation-1, elevation-2, etc.) for reuse

### 8. Border and Radius Inconsistencies

**What goes wrong:**
- Border radius values are inconsistent (8px in design, 6px in code)
- Individual corner radii not applied (Figma allows per-corner radius)
- Border color or width differs from design
- Border is on the wrong side (e.g., bottom only vs. all sides)

**How to prevent:**
- Use a border-radius token scale (e.g., sm=4px, md=8px, lg=12px, full=9999px)
- Check if Figma uses per-corner radius (top-left may differ from bottom-right)
- Verify border-style, border-width, and border-color independently

### 9. Content Overflow Handling

**What goes wrong:**
- Long text overflows container instead of truncating with ellipsis
- Figma design uses short placeholder text; real content is longer
- Multi-line truncation (line-clamp) not implemented
- Scrollable areas not matching design behavior

**How to prevent:**
- Ask the design team: "What happens when this text is longer than shown?"
- Test with realistic content lengths (long names, long descriptions)
- Implement `text-overflow: ellipsis` and `-webkit-line-clamp` as needed
- Test scrollable containers with content that exceeds the visible area

### 10. Animation and Transition Gaps

**What goes wrong:**
- Figma prototyping shows transitions but implementation has none
- Timing or easing function does not match design intent
- Loading skeletons or shimmer effects are missing
- Page transitions are abrupt instead of animated

**How to prevent:**
- Check Figma prototype interactions for transition specifications
- Establish a standard transition duration (150ms-300ms) and easing function
- Implement skeleton loading states for async content
- Use shared animation tokens (duration, easing) across the codebase
