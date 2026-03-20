# Flow: Project Discovery Interview

## Trigger
The user has provided an idea. It may be detailed or just a sentence.

**User's idea**: $ARGUMENTS

## Instructions

Conduct a structured discovery interview to understand the project deeply before building anything. This is critical — the quality of the interview determines the quality of the plan.

### Interview Protocol

Ask questions **ONE AT A TIME**. Wait for the user's response before asking the next question. Be conversational, not robotic. Build on their answers.

### Question Areas (adapt based on the idea)

**1. Core Concept**
- What problem does this solve? Who is it for?
- What's the single most important thing it needs to do?

**2. Technical Scope**
- What language/framework preference? (or should I pick the best fit?)
- Any external APIs or services needed?
- Does it need a database? What kind of data?
- Does it need a UI? What kind — web app, CLI, API only?

**3. Key Features**
- What are the 3-5 must-have features for v1?
- What should explicitly NOT be in v1?

**4. Data & Integrations**
- What are the key data entities?
- Any external systems to integrate with?
- Any authentication needs?

**5. Constraints & Preferences**
- Any strong opinions on architecture or tools?
- Performance requirements?
- Where will this run? (local, cloud, serverless?)

**6. Definition of Done**
- How will you know v1 is complete?
- What does a successful demo look like?

### Adaptive Questioning

- Skip questions that aren't relevant to the idea
- Go deeper on areas where the user has strong opinions
- If the user says "you decide" — make a recommendation and confirm
- Aim for 6-10 questions total, not more

### Output

After the interview is complete, write the full summary to `docs/interview-answers.md` with:
- Project name (ask the user or suggest one)
- One-paragraph summary
- Technical decisions
- Feature list (must-have vs nice-to-have)
- Architecture decisions
- Constraints and requirements

Then tell the user:
> "Interview complete. I've captured everything in `docs/interview-answers.md`. Ready to generate the plan? Just say **go ahead** or **/flow-next-plan**."
