#!/usr/bin/env bash
# create_bug_report.sh - Bug report template generator
# Part of the qa-test-planner skill
#
# Usage:
#   ./create_bug_report.sh --severity critical --format markdown
#   ./create_bug_report.sh --severity minor --format json --output bug_report.json
#   ./create_bug_report.sh --help

set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────────────────────────
SEVERITY=""
FORMAT="markdown"
OUTPUT=""
BUG_TITLE=""
COMPONENT=""
ENVIRONMENT=""
REPORTER=""

# ─── Colors ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ─── Functions ──────────────────────────────────────────────────────────────────

usage() {
    cat <<'HELP'
create_bug_report.sh - Bug report template generator

USAGE:
    create_bug_report.sh --severity <level> [OPTIONS]

REQUIRED:
    --severity <level>  Bug severity. One of:
                          critical - System crash, data loss, security vulnerability
                          major    - Feature broken, no workaround available
                          minor    - Feature impaired, workaround exists
                          trivial  - Cosmetic issue, typo, minor visual defect

OPTIONS:
    --format <format>   Output format: markdown (default), json
    --output <file>     Write output to file instead of stdout
    --title <title>     Bug title (skips interactive prompt)
    --component <name>  Affected component (skips interactive prompt)
    --env <environment> Environment where bug was found (skips interactive prompt)
    --reporter <name>   Reporter name (skips interactive prompt)
    --help              Show this help message

EXAMPLES:
    # Interactive mode - prompts for details
    ./create_bug_report.sh --severity critical

    # Non-interactive mode
    ./create_bug_report.sh --severity major --format markdown \
        --title "Login fails with SSO" --component "Authentication" \
        --env "Production" --reporter "QA Team"

    # JSON output for integration with bug tracking systems
    ./create_bug_report.sh --severity minor --format json --output bug.json
HELP
}

error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${BLUE}$1${NC}" >&2
}

prompt_value() {
    local prompt="$1"
    local default="${2:-}"
    local value=""
    if [[ -n "$default" ]]; then
        echo -en "${GREEN}${prompt} [${default}]: ${NC}" >&2
    else
        echo -en "${GREEN}${prompt}: ${NC}" >&2
    fi
    read -r value
    echo "${value:-$default}"
}

validate_severity() {
    case "$1" in
        critical|major|minor|trivial) return 0 ;;
        *) return 1 ;;
    esac
}

validate_format() {
    case "$1" in
        markdown|json) return 0 ;;
        *) return 1 ;;
    esac
}

# Map severity to priority
severity_to_priority() {
    case "$1" in
        critical) echo "P1 - Immediate" ;;
        major)    echo "P2 - High" ;;
        minor)    echo "P3 - Medium" ;;
        trivial)  echo "P4 - Low" ;;
    esac
}

# Generate a unique bug ID
generate_bug_id() {
    local sev_prefix
    case "$SEVERITY" in
        critical) sev_prefix="CRIT" ;;
        major)    sev_prefix="MAJ" ;;
        minor)    sev_prefix="MIN" ;;
        trivial)  sev_prefix="TRV" ;;
    esac
    echo "BUG-${sev_prefix}-$(date +%Y%m%d)-$(printf '%03d' $((RANDOM % 1000)))"
}

# ─── Gather interactive inputs ──────────────────────────────────────────────────

gather_inputs() {
    info "── Bug Report Details ──"

    if [[ -z "$BUG_TITLE" ]]; then
        BUG_TITLE=$(prompt_value "Bug title" "")
        [[ -z "$BUG_TITLE" ]] && BUG_TITLE="[Descriptive Bug Title]"
    fi

    if [[ -z "$COMPONENT" ]]; then
        COMPONENT=$(prompt_value "Affected component/module" "")
        [[ -z "$COMPONENT" ]] && COMPONENT="[Component Name]"
    fi

    if [[ -z "$ENVIRONMENT" ]]; then
        ENVIRONMENT=$(prompt_value "Environment (e.g., Production, Staging, Dev)" "Staging")
    fi

    if [[ -z "$REPORTER" ]]; then
        REPORTER=$(prompt_value "Reporter name" "QA Team")
    fi
}

# ─── Severity-specific content ──────────────────────────────────────────────────

severity_impact() {
    case "$SEVERITY" in
        critical)
            echo "**CRITICAL IMPACT**: This issue causes system failure, data loss, or security exposure. Requires immediate attention and hotfix deployment."
            ;;
        major)
            echo "**MAJOR IMPACT**: Core functionality is broken with no viable workaround. Blocks user workflows and should be prioritized in the current sprint."
            ;;
        minor)
            echo "**MINOR IMPACT**: Feature is impaired but a workaround exists. Users can continue their workflow with reduced efficiency."
            ;;
        trivial)
            echo "**TRIVIAL IMPACT**: Cosmetic or minor visual issue that does not affect functionality. Can be addressed in a future maintenance cycle."
            ;;
    esac
}

severity_sla() {
    case "$SEVERITY" in
        critical) echo "Resolution SLA: 4 hours | Acknowledgment: 30 minutes" ;;
        major)    echo "Resolution SLA: 24 hours | Acknowledgment: 2 hours" ;;
        minor)    echo "Resolution SLA: 1 sprint | Acknowledgment: 1 business day" ;;
        trivial)  echo "Resolution SLA: Backlog | Acknowledgment: 1 week" ;;
    esac
}

# ─── Output formatters ──────────────────────────────────────────────────────────

generate_markdown() {
    local bug_id priority
    bug_id=$(generate_bug_id)
    priority=$(severity_to_priority "$SEVERITY")

    cat <<EOF
# Bug Report: ${BUG_TITLE}

| Field              | Value                                    |
|--------------------|------------------------------------------|
| **Bug ID**         | ${bug_id}                                |
| **Title**          | ${BUG_TITLE}                             |
| **Severity**       | ${SEVERITY^^}                            |
| **Priority**       | ${priority}                              |
| **Component**      | ${COMPONENT}                             |
| **Environment**    | ${ENVIRONMENT}                           |
| **Reporter**       | ${REPORTER}                              |
| **Date Reported**  | $(date -u +"%Y-%m-%d")                   |
| **Status**         | Open                                     |
| **Assigned To**    | [Unassigned]                             |

---

## Impact Assessment

$(severity_impact)

$(severity_sla)

---

## Environment Details

- **OS / Browser**: [e.g., macOS 14.2 / Chrome 120, Windows 11 / Firefox 121]
- **App Version**: [e.g., v2.3.1, commit SHA]
- **Device**: [e.g., Desktop, iPhone 15 Pro, Samsung Galaxy S24]
- **Screen Resolution**: [e.g., 1920x1080]
- **Network**: [e.g., Broadband, 4G, Throttled 3G]
- **User Role/Permissions**: [e.g., Admin, Standard User, Guest]
- **Related Feature Flags**: [e.g., feature_new_checkout=enabled]

---

## Steps to Reproduce

1. [Navigate to / Open the specific page or feature]
2. [Describe the exact action taken]
3. [Describe any input data used]
4. [Describe the next action]
5. [Observe the bug]

**Reproduction Rate**: [Always / Intermittent (~X%) / One-time]

---

## Expected Behavior

[Describe what should happen when following the steps above. Reference the specification or design document if available.]

---

## Actual Behavior

[Describe what actually happens. Be specific about error messages, visual glitches, or incorrect data.]

---

## Screenshots / Recordings

<!-- Attach screenshots, screen recordings, or GIFs that demonstrate the issue -->

| Description | Attachment |
|-------------|------------|
| [What this shows] | ![Screenshot placeholder](attachment_url) |

---

## Console / Log Output

\`\`\`
[Paste any relevant console errors, stack traces, or log output here]
\`\`\`

---

## Additional Context

- **Related Issues**: [Link to related bug reports or feature requests]
- **Regression**: [Yes/No - Was this working before? If yes, which version?]
- **Workaround**: [Describe any known workaround, or "None"]
- **Customer Impact**: [Number of users affected, if known]
- **Notes**: [Any other relevant context, configuration details, or observations]

---

## For Developers

- **Suspected Root Cause**: [If known, describe the likely cause]
- **Suggested Fix**: [If known, describe the approach]
- **Files Likely Involved**: [List suspected files/modules]
- **Test Coverage**: [Are there existing tests for this area? Do they pass?]
EOF
}

generate_json() {
    local bug_id priority
    bug_id=$(generate_bug_id)
    priority=$(severity_to_priority "$SEVERITY")

    python3 -c "
import json
import datetime

report = {
    'bug_id': '$bug_id',
    'title': $(python3 -c "import json; print(json.dumps('$BUG_TITLE'))"),
    'severity': '$SEVERITY',
    'priority': '$priority',
    'component': $(python3 -c "import json; print(json.dumps('$COMPONENT'))"),
    'environment': {
        'name': $(python3 -c "import json; print(json.dumps('$ENVIRONMENT'))"),
        'os_browser': '[e.g., macOS 14.2 / Chrome 120]',
        'app_version': '[e.g., v2.3.1]',
        'device': '[e.g., Desktop]',
        'screen_resolution': '[e.g., 1920x1080]',
        'network': '[e.g., Broadband]',
        'user_role': '[e.g., Standard User]',
        'feature_flags': []
    },
    'reporter': $(python3 -c "import json; print(json.dumps('$REPORTER'))"),
    'date_reported': datetime.date.today().isoformat(),
    'status': 'Open',
    'assigned_to': None,
    'impact_assessment': $(python3 -c "
import json
severity='$SEVERITY'
impacts = {
    'critical': 'System failure, data loss, or security exposure. Requires immediate hotfix.',
    'major': 'Core functionality broken, no workaround. Blocks user workflows.',
    'minor': 'Feature impaired but workaround exists. Reduced user efficiency.',
    'trivial': 'Cosmetic or visual issue. No functional impact.'
}
print(json.dumps(impacts.get(severity, '')))
"),
    'steps_to_reproduce': [
        '[Navigate to the specific page or feature]',
        '[Describe the exact action taken]',
        '[Describe any input data used]',
        '[Describe the next action]',
        '[Observe the bug]'
    ],
    'reproduction_rate': '[Always / Intermittent / One-time]',
    'expected_behavior': '[Describe what should happen]',
    'actual_behavior': '[Describe what actually happens]',
    'screenshots': [],
    'console_log_output': '[Paste relevant errors or stack traces]',
    'additional_context': {
        'related_issues': [],
        'is_regression': None,
        'workaround': '[Describe workaround or None]',
        'customer_impact': '[Number of users affected]',
        'notes': ''
    },
    'developer_notes': {
        'suspected_root_cause': '',
        'suggested_fix': '',
        'files_involved': [],
        'existing_test_coverage': ''
    }
}

print(json.dumps(report, indent=2))
"
}

# ─── Parse arguments ────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --severity)
            [[ -z "${2:-}" ]] && error "--severity requires a value"
            SEVERITY="$2"
            validate_severity "$SEVERITY" || error "Invalid severity '$SEVERITY'. Must be: critical, major, minor, trivial"
            shift 2
            ;;
        --format)
            [[ -z "${2:-}" ]] && error "--format requires a value"
            FORMAT="$2"
            validate_format "$FORMAT" || error "Invalid format '$FORMAT'. Must be: markdown, json"
            shift 2
            ;;
        --output)
            [[ -z "${2:-}" ]] && error "--output requires a file path"
            OUTPUT="$2"
            shift 2
            ;;
        --title)
            [[ -z "${2:-}" ]] && error "--title requires a value"
            BUG_TITLE="$2"
            shift 2
            ;;
        --component)
            [[ -z "${2:-}" ]] && error "--component requires a value"
            COMPONENT="$2"
            shift 2
            ;;
        --env)
            [[ -z "${2:-}" ]] && error "--env requires a value"
            ENVIRONMENT="$2"
            shift 2
            ;;
        --reporter)
            [[ -z "${2:-}" ]] && error "--reporter requires a value"
            REPORTER="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# ─── Validate required arguments ────────────────────────────────────────────────

[[ -z "$SEVERITY" ]] && error "--severity is required. Use --help for usage information."

# ─── Interactive prompts for missing values ─────────────────────────────────────

gather_inputs

# ─── Generate output ────────────────────────────────────────────────────────────

info "Generating ${SEVERITY} bug report template in ${FORMAT} format..."

output_content=""
case "$FORMAT" in
    markdown) output_content=$(generate_markdown) ;;
    json)     output_content=$(generate_json) ;;
esac

if [[ -n "$OUTPUT" ]]; then
    output_dir=$(dirname "$OUTPUT")
    if [[ ! -d "$output_dir" ]]; then
        mkdir -p "$output_dir" || error "Cannot create output directory: $output_dir"
    fi
    echo "$output_content" > "$OUTPUT"
    info "Bug report written to: ${OUTPUT}"
else
    echo "$output_content"
fi
