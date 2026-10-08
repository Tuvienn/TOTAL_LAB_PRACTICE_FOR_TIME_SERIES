# TIME SERIES — CODE AND FILE-CHANGE RULES

## 1. Purpose

These rules apply to code, file, data, structure, configuration, notebook, documentation, debugging, and refactoring changes.

They supplement `GENERAL_RULES.md` and do not replace scoped scientific or Practice-specific rules.

## 2. Understand Before Changing

Before a meaningful change, identify:

```text
objective
input
expected output
affected files
files that must not change
reason
impact
risks
alternatives when material
validation method
```

Do not implement when a missing requirement materially affects correctness, architecture, safety, or expected behavior.

## 3. Plan and Approval Gate

Before modifying code, files, folders, workflows, architecture, execution protocols, or substantive documentation:

1. State the objective.
2. Identify affected files and excluded files.
3. Describe the planned changes.
4. Explain the reason, impact, risks, and relevant alternatives.
5. Define validation and stop conditions.
6. Obtain Human approval when required by the active task or scoped workflow.

A request to prepare or discuss a task is not implementation approval.

## 4. Focused Sequential Execution

Use small logical changes:

```text
change one focused responsibility
→ run or inspect it
→ verify the result
→ continue to the next approved step
```

- Do not combine unrelated refactoring, dependency updates, new analysis, bug fixes, and folder restructuring.
- Do not continue to a dependent step while the current step has an unexplained failure.
- Only one main logical implementation task should be `IN_PROGRESS` at a time.

## 5. Architecture and Ownership

- Follow the current architecture, folder structure, naming conventions, and ownership boundaries.
- Read comparable existing code before introducing a new pattern.
- Put reusable logic in its approved source owner rather than duplicating it in notebooks or downstream consumers.
- Fix the root-cause owner instead of patching downstream symptoms.
- Do not create a new layer, dependency direction, folder responsibility, or duplicate implementation without approval.
- Do not change an architecture document merely to legitimize a non-conforming implementation.

## 6. Stable and Unrelated Work

- Do not modify stable code or files outside the approved scope.
- Do not refactor a working module merely for stylistic preference.
- If a required fix affects an unapproved owner or consumer, stop and request a scope update.
- Preserve existing Human-approved decisions unless the Human explicitly reopens them.

## 7. Naming and Paths

Prefer the repository's established convention. If no more specific convention exists:

| Item | Convention |
|---|---|
| Python module, function, variable, file | `snake_case` |
| Python class | `PascalCase` |
| Constant | `UPPER_SNAKE_CASE` |
| Web/config file or folder | `kebab-case` |
| API endpoint | plural noun in `kebab-case` |
| Database table or column | `snake_case` |
| Git branch | prefix plus `kebab-case` |
| Commit message | `[type]: [short description]` |

For Python path handling, prefer `pathlib.Path` and avoid machine-specific absolute paths.

## 8. Source Quality

Prefer:

```text
clear names
focused cohesive functions
explicit inputs and outputs
deterministic behavior
single responsibility
minimal hidden state
```

Avoid:

```text
broad exception swallowing
silent mutation
duplicate logic
hard-coded machine paths
unexplained fallback behavior
```

Do not add comments that merely narrate obvious code. Comments are allowed only when they explain non-obvious business constraints or special algorithms, or when explicitly requested.

Do not add external icon packages or icons outside an established design system without approval.

## 9. Dependencies and Configuration

- Do not add or upgrade a dependency merely to make a task easier.
- Significant dependency changes require a reason, impact analysis, compatibility check, and approval.
- Do not store secrets in code, configuration, logs, notebooks, or documentation.
- Do not place machine-specific absolute paths in shared configuration.

## 10. Investigation and Fixing

For a non-trivial bug or scientific issue:

```text
collect evidence
→ describe observed versus expected behavior
→ inspect relevant owners and consumers
→ identify the root cause
→ document the issue when useful
→ propose the fix scope
→ obtain approval when required
→ implement sequentially
→ validate locally and across affected consumers
```

Do not jump directly from a traceback to an unverified patch.

Do not silently switch methods, parameters, dependencies, or validation thresholds when the intended path fails.

## 11. Repeated-Failure Escalation

After three materially similar failed attempts on the same problem:

1. Stop the repeated approach.
2. Summarize the attempts and changes.
3. Compare the evidence and identify the repeated pattern.
4. Verify upstream/downstream or client/server boundaries when relevant.
5. Present at least two next directions when possible.
6. Wait for Human direction before a fourth similar attempt.

## 12. Run and Verify

Every change requires validation proportional to its risk, for example:

```text
syntax and import checks
targeted function behavior
data shape and schema
timestamp and alignment behavior
tests
notebook execution order
expected output files
regression checks for affected consumers
```

Reading code or observing no syntax error is not sufficient evidence of correctness.

## 13. Completion and Reporting

Do not report `done`, `fixed`, `passed`, or `complete` unless:

```text
the approved scope is implemented
relevant execution or inspection succeeded
required outputs were inspected
blocking errors are resolved
requirements and acceptance criteria are satisfied
remaining risks and limitations are disclosed
```

Report:

```text
files changed
what was wrong or missing
why the change was made
impact
validation performed and its result
outputs created
remaining risks or side effects
next step
```

## 14. Stop Conditions

Stop implementation when:

```text
requirements or scope are materially unclear
rules conflict
required source material is missing
an unexpected schema or protocol appears
a new dependency is required
the scope must expand
validation fails unexpectedly
an upstream owner is incorrect
required Human approval is missing
```
