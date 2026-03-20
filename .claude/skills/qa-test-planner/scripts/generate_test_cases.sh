#!/usr/bin/env bash
# generate_test_cases.sh - Interactive test case template generator
# Part of the qa-test-planner skill
#
# Usage:
#   ./generate_test_cases.sh --type functional --format markdown
#   ./generate_test_cases.sh --type e2e --format json --output test_cases.json
#   ./generate_test_cases.sh --help

set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────────────────────────
TYPE=""
FORMAT="markdown"
OUTPUT=""
SUITE_NAME=""
FEATURE_AREA=""
PRIORITY="medium"
NUM_CASES=3

# ─── Colors ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ─── Functions ──────────────────────────────────────────────────────────────────

usage() {
    cat <<'HELP'
generate_test_cases.sh - Interactive test case template generator

USAGE:
    generate_test_cases.sh --type <type> [OPTIONS]

REQUIRED:
    --type <type>       Test case type. One of:
                          functional    - Unit/functional test cases
                          integration   - Integration test cases
                          e2e           - End-to-end test cases
                          accessibility - Accessibility (WCAG 2.1 AA) test cases
                          performance   - Performance/load test cases

OPTIONS:
    --format <format>   Output format: markdown (default), csv, json
    --output <file>     Write output to file instead of stdout
    --suite <name>      Test suite name (skips interactive prompt)
    --feature <area>    Feature area (skips interactive prompt)
    --priority <level>  Priority level: critical, high, medium (default), low
    --count <n>         Number of test case templates to generate (default: 3)
    --help              Show this help message

EXAMPLES:
    # Interactive mode - prompts for suite name and feature area
    ./generate_test_cases.sh --type functional --format markdown

    # Non-interactive mode with all options specified
    ./generate_test_cases.sh --type e2e --format json --output tests.json \
        --suite "Checkout Flow" --feature "Payment Processing" --priority high

    # Generate CSV for import into test management tools
    ./generate_test_cases.sh --type integration --format csv --output tests.csv \
        --suite "API Tests" --feature "User Service" --count 5
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
    local default="$2"
    local value=""
    if [[ -n "$default" ]]; then
        echo -en "${GREEN}${prompt} [${default}]: ${NC}" >&2
    else
        echo -en "${GREEN}${prompt}: ${NC}" >&2
    fi
    read -r value
    echo "${value:-$default}"
}

validate_type() {
    case "$1" in
        functional|integration|e2e|accessibility|performance) return 0 ;;
        *) return 1 ;;
    esac
}

validate_format() {
    case "$1" in
        markdown|csv|json) return 0 ;;
        *) return 1 ;;
    esac
}

validate_priority() {
    case "$1" in
        critical|high|medium|low) return 0 ;;
        *) return 1 ;;
    esac
}

generate_id() {
    local prefix="$1"
    local index="$2"
    printf "TC-%s-%03d" "$prefix" "$index"
}

# ─── Gather interactive inputs ──────────────────────────────────────────────────

gather_inputs() {
    if [[ -z "$SUITE_NAME" ]]; then
        info "── Test Suite Configuration ──"
        SUITE_NAME=$(prompt_value "Test suite name" "")
        [[ -z "$SUITE_NAME" ]] && error "Test suite name is required."
    fi

    if [[ -z "$FEATURE_AREA" ]]; then
        FEATURE_AREA=$(prompt_value "Feature area" "")
        [[ -z "$FEATURE_AREA" ]] && error "Feature area is required."
    fi

    if [[ "$PRIORITY" == "medium" ]]; then
        local input_priority
        input_priority=$(prompt_value "Default priority (critical/high/medium/low)" "medium")
        if validate_priority "$input_priority"; then
            PRIORITY="$input_priority"
        else
            echo -e "${YELLOW}Warning: Invalid priority '$input_priority'. Using 'medium'.${NC}" >&2
        fi
    fi
}

# ─── Type-specific field generators ─────────────────────────────────────────────

preconditions_for_type() {
    local type="$1"
    local index="$2"
    case "$type" in
        functional)
            echo "- Application is running and accessible
- User is authenticated with appropriate role
- Test data is seeded in the database"
            ;;
        integration)
            echo "- All dependent services are running
- API endpoints are accessible
- Database migrations are applied
- Message queues are connected"
            ;;
        e2e)
            echo "- Application is deployed to staging environment
- Browser is configured (viewport: 1920x1080)
- Test user accounts are provisioned
- Third-party services are available or mocked"
            ;;
        accessibility)
            echo "- Page is fully loaded (no pending network requests)
- Screen reader software is available for manual checks
- Color contrast analyzer tool is ready
- Keyboard navigation is enabled (no mouse)"
            ;;
        performance)
            echo "- Performance monitoring tools are configured
- Baseline metrics are recorded
- Load testing environment is isolated
- Database is populated with realistic data volume"
            ;;
    esac
}

steps_for_type() {
    local type="$1"
    case "$type" in
        functional)
            echo "1. Navigate to the feature under test
2. Set up required precondition state
3. Perform the action being tested
4. Verify the immediate result
5. Verify side effects (database, logs, events)"
            ;;
        integration)
            echo "1. Prepare request payload with valid data
2. Send request to the API endpoint
3. Verify response status code and body
4. Verify downstream service received correct data
5. Verify database state reflects the operation
6. Verify events/messages were published correctly"
            ;;
        e2e)
            echo "1. Open the application in the browser
2. Navigate to the starting page of the workflow
3. Complete each step of the user journey
4. Verify visual feedback at each step (loading states, confirmations)
5. Verify the final outcome is correct
6. Verify data persistence (refresh and confirm state)"
            ;;
        accessibility)
            echo "1. Navigate to the page/component under test
2. Run automated accessibility scan (axe-core or similar)
3. Verify keyboard navigation: Tab through all interactive elements
4. Verify focus indicators are visible on all focusable elements
5. Verify screen reader announces elements correctly
6. Verify color contrast meets WCAG 2.1 AA (4.5:1 text, 3:1 large text)
7. Verify responsive behavior does not break accessibility"
            ;;
        performance)
            echo "1. Configure performance monitoring/profiling tools
2. Record baseline metrics before the test
3. Execute the scenario under defined load conditions
4. Capture key metrics: response time, throughput, error rate
5. Compare results against defined thresholds
6. Identify bottlenecks if thresholds are exceeded"
            ;;
    esac
}

expected_results_for_type() {
    local type="$1"
    case "$type" in
        functional)
            echo "- Feature behaves according to specification
- Correct data is returned/displayed
- Error handling works for invalid inputs
- State changes are persisted correctly"
            ;;
        integration)
            echo "- API returns expected status code (2xx for success)
- Response body matches expected schema
- Downstream services reflect the changes
- Data consistency is maintained across services
- Error responses include meaningful messages"
            ;;
        e2e)
            echo "- User can complete the full workflow without errors
- All visual elements render correctly
- Navigation between steps works as expected
- Final state matches the user's intent
- No console errors in the browser"
            ;;
        accessibility)
            echo "- Zero critical accessibility violations (axe-core)
- All interactive elements are keyboard accessible
- Focus order is logical and intuitive
- Screen reader provides meaningful announcements
- Color contrast ratios meet WCAG 2.1 AA standards
- Content is usable at 200% zoom"
            ;;
        performance)
            echo "- Page load time < defined threshold (e.g., 2s)
- API response time < defined threshold (e.g., 200ms p95)
- No memory leaks under sustained load
- Error rate < 0.1% under normal load
- System recovers gracefully after load spike"
            ;;
    esac
}

# ─── Output formatters ──────────────────────────────────────────────────────────

generate_markdown() {
    local prefix
    prefix=$(echo "$TYPE" | head -c 4 | tr '[:lower:]' '[:upper:]')

    cat <<EOF
# Test Suite: ${SUITE_NAME}

**Feature Area:** ${FEATURE_AREA}
**Test Type:** ${TYPE}
**Default Priority:** ${PRIORITY}
**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")

---

EOF

    for i in $(seq 1 "$NUM_CASES"); do
        local tc_id
        tc_id=$(generate_id "$prefix" "$i")
        cat <<EOF
## ${tc_id}: [Test Title - Describe the scenario]

| Field            | Value                              |
|------------------|------------------------------------|
| **ID**           | ${tc_id}                           |
| **Type**         | ${TYPE}                            |
| **Priority**     | ${PRIORITY}                        |
| **Feature Area** | ${FEATURE_AREA}                    |
| **Status**       | Not Executed                       |
| **Automated**    | No                                 |

### Preconditions

$(preconditions_for_type "$TYPE" "$i")

### Test Steps

$(steps_for_type "$TYPE")

### Expected Results

$(expected_results_for_type "$TYPE")

### Notes

_Add any additional context, test data requirements, or edge cases here._

---

EOF
    done
}

generate_csv() {
    local prefix
    prefix=$(echo "$TYPE" | head -c 4 | tr '[:lower:]' '[:upper:]')

    echo "ID,Title,Type,Priority,Feature Area,Preconditions,Steps,Expected Results,Status,Automated"
    for i in $(seq 1 "$NUM_CASES"); do
        local tc_id
        tc_id=$(generate_id "$prefix" "$i")
        # Escape fields for CSV (wrap in quotes, escape internal quotes)
        local preconditions steps expected
        preconditions=$(preconditions_for_type "$TYPE" "$i" | tr '\n' '; ' | sed 's/"/""/g')
        steps=$(steps_for_type "$TYPE" | tr '\n' '; ' | sed 's/"/""/g')
        expected=$(expected_results_for_type "$TYPE" | tr '\n' '; ' | sed 's/"/""/g')
        echo "\"${tc_id}\",\"[Test Title]\",\"${TYPE}\",\"${PRIORITY}\",\"${FEATURE_AREA}\",\"${preconditions}\",\"${steps}\",\"${expected}\",\"Not Executed\",\"No\""
    done
}

generate_json() {
    local prefix
    prefix=$(echo "$TYPE" | head -c 4 | tr '[:lower:]' '[:upper:]')

    # Build JSON using python3 for proper escaping
    python3 -c "
import json, sys, subprocess, datetime

suite = {
    'suite_name': $(python3 -c "import json; print(json.dumps('$SUITE_NAME'))"),
    'feature_area': $(python3 -c "import json; print(json.dumps('$FEATURE_AREA'))"),
    'test_type': '$TYPE',
    'default_priority': '$PRIORITY',
    'generated': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'test_cases': []
}

for i in range(1, $NUM_CASES + 1):
    tc_id = f'TC-$prefix-{i:03d}'
    suite['test_cases'].append({
        'id': tc_id,
        'title': '[Test Title - Describe the scenario]',
        'type': '$TYPE',
        'priority': '$PRIORITY',
        'feature_area': $(python3 -c "import json; print(json.dumps('$FEATURE_AREA'))"),
        'status': 'Not Executed',
        'automated': False,
        'preconditions': $(python3 -c "
import json, subprocess
result = subprocess.run(['bash', '-c', '''$(declare -f preconditions_for_type); preconditions_for_type "$TYPE" 1'''.replace('$TYPE', '$TYPE')], capture_output=True, text=True)
print(json.dumps(result.stdout.strip().split('\n')))
" 2>/dev/null || echo '[]'),
        'steps': $(python3 -c "
import json, subprocess
result = subprocess.run(['bash', '-c', '''$(declare -f steps_for_type); steps_for_type "$TYPE"'''.replace('$TYPE', '$TYPE')], capture_output=True, text=True)
print(json.dumps(result.stdout.strip().split('\n')))
" 2>/dev/null || echo '[]'),
        'expected_results': $(python3 -c "
import json, subprocess
result = subprocess.run(['bash', '-c', '''$(declare -f expected_results_for_type); expected_results_for_type "$TYPE"'''.replace('$TYPE', '$TYPE')], capture_output=True, text=True)
print(json.dumps(result.stdout.strip().split('\n')))
" 2>/dev/null || echo '[]'),
        'notes': ''
    })

print(json.dumps(suite, indent=2))
" 2>/dev/null

    # Fallback: if python3 JSON generation fails, use a simpler approach
    if [[ $? -ne 0 ]]; then
        echo "{"
        echo "  \"suite_name\": \"${SUITE_NAME}\","
        echo "  \"feature_area\": \"${FEATURE_AREA}\","
        echo "  \"test_type\": \"${TYPE}\","
        echo "  \"default_priority\": \"${PRIORITY}\","
        echo "  \"generated\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
        echo "  \"test_cases\": ["
        for i in $(seq 1 "$NUM_CASES"); do
            local tc_id
            tc_id=$(generate_id "$prefix" "$i")
            [[ $i -gt 1 ]] && echo "    ,"
            echo "    {"
            echo "      \"id\": \"${tc_id}\","
            echo "      \"title\": \"[Test Title - Describe the scenario]\","
            echo "      \"type\": \"${TYPE}\","
            echo "      \"priority\": \"${PRIORITY}\","
            echo "      \"feature_area\": \"${FEATURE_AREA}\","
            echo "      \"status\": \"Not Executed\","
            echo "      \"automated\": false,"
            echo "      \"preconditions\": [],"
            echo "      \"steps\": [],"
            echo "      \"expected_results\": [],"
            echo "      \"notes\": \"\""
            echo "    }"
        done
        echo "  ]"
        echo "}"
    fi
}

# ─── Parse arguments ────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --type)
            [[ -z "${2:-}" ]] && error "--type requires a value"
            TYPE="$2"
            validate_type "$TYPE" || error "Invalid type '$TYPE'. Must be: functional, integration, e2e, accessibility, performance"
            shift 2
            ;;
        --format)
            [[ -z "${2:-}" ]] && error "--format requires a value"
            FORMAT="$2"
            validate_format "$FORMAT" || error "Invalid format '$FORMAT'. Must be: markdown, csv, json"
            shift 2
            ;;
        --output)
            [[ -z "${2:-}" ]] && error "--output requires a file path"
            OUTPUT="$2"
            shift 2
            ;;
        --suite)
            [[ -z "${2:-}" ]] && error "--suite requires a value"
            SUITE_NAME="$2"
            shift 2
            ;;
        --feature)
            [[ -z "${2:-}" ]] && error "--feature requires a value"
            FEATURE_AREA="$2"
            shift 2
            ;;
        --priority)
            [[ -z "${2:-}" ]] && error "--priority requires a value"
            PRIORITY="$2"
            validate_priority "$PRIORITY" || error "Invalid priority '$PRIORITY'. Must be: critical, high, medium, low"
            shift 2
            ;;
        --count)
            [[ -z "${2:-}" ]] && error "--count requires a number"
            NUM_CASES="$2"
            [[ "$NUM_CASES" =~ ^[0-9]+$ ]] || error "--count must be a positive integer"
            [[ "$NUM_CASES" -lt 1 ]] && error "--count must be at least 1"
            [[ "$NUM_CASES" -gt 50 ]] && error "--count must be 50 or fewer"
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

[[ -z "$TYPE" ]] && error "--type is required. Use --help for usage information."

# ─── Interactive prompts for missing values ─────────────────────────────────────

gather_inputs

# ─── Generate output ────────────────────────────────────────────────────────────

info "Generating ${NUM_CASES} ${TYPE} test case template(s) in ${FORMAT} format..."

output_content=""
case "$FORMAT" in
    markdown) output_content=$(generate_markdown) ;;
    csv)      output_content=$(generate_csv) ;;
    json)     output_content=$(generate_json) ;;
esac

if [[ -n "$OUTPUT" ]]; then
    # Ensure output directory exists
    output_dir=$(dirname "$OUTPUT")
    if [[ ! -d "$output_dir" ]]; then
        mkdir -p "$output_dir" || error "Cannot create output directory: $output_dir"
    fi
    echo "$output_content" > "$OUTPUT"
    info "Test cases written to: ${OUTPUT}"
else
    echo "$output_content"
fi
