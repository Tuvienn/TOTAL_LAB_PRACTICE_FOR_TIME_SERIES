# TIME SERIES — CANONICAL MULTI-AGENT WORKFLOW

## 1. Purpose

This file defines execution order and rule routing. It does not duplicate the normative requirements in `.agents/rules/`.

## 2. Rule Loading

For every repository task, read:

```text
.agents/rules/GENERAL_RULES.md
```

Additionally read:

| Task type | Additional source |
|---|---|
| File, code, data, configuration, structure, notebook, or documentation change | `.agents/rules/CODE_RULES.md` |
| Time Series analysis, processing, forecasting, validation, or evaluation | `.agents/rules/TIME_SERIES_RULES.md` |
| Work under a scoped practice | Relevant scoped rules, approved specification, and approved plan |
| Bug or scientific issue | Relevant owner rules plus evidence and approved fix scope |

## 3. General Workflow

```text
Understand
→ Clarify material uncertainty
→ Identify applicable rules and scope
→ Plan the approved change
→ Confirm when required
→ Execute one focused step
→ Run or inspect
→ Verify
→ Report
```

### 3.1 Understand

Identify the objective, input, output, scope, constraints, affected owners, and validation method.

### 3.2 Clarify

Ask only when missing information materially affects correctness, safety, scope, architecture, data protocol, or expected output.

### 3.3 Route

Load the canonical general rule and every additional rule required by the task type. More specific approved scoped rules supplement the shared rules.

### 3.4 Plan and Confirm

For meaningful changes, state the objective, impacted files, exclusions, steps, risks, and validation. Obtain approval when required.

### 3.5 Execute

Implement only the approved scope, one focused logical step at a time.

### 3.6 Run and Verify

Inspect actual outputs, tests, data properties, side effects, and affected consumers as appropriate.

### 3.7 Report

Report changes, evidence, validation, remaining risks, and the next step without claiming unsupported completion.

## 4. Time Series Workflow

```text
Define the problem
→ Inspect the data
→ Validate the time index
→ Check data quality
→ Visualize
→ Analyze temporal structure
→ Define the forecasting or analysis setup
→ Define metrics
→ Build a baseline when modeling
→ Engineer time-safe features when required
→ Apply the approved method or model
→ Perform time-aware validation
→ Analyze errors and residuals
→ Conclude from actual evidence
```

Skip modeling-only steps when the approved task is exploratory analysis rather than forecasting.

## 5. Practice Workflow

For work under `total_practice/Practice_1/`:

1. Read the Practice README and current approval state.
2. Read the Practice architecture and code/execution rules.
3. Read the relevant approved exercise specification when it exists.
4. Read the relevant approved before-process plan for implementation.
5. Inspect current-flow and relevant artifacts.
6. Execute sequentially within the approved scope.
7. Run and verify every step.
8. Store outputs in their approved owners.
9. Update current state when required.
10. Report evidence and unresolved issues.

Draft or unapproved scoped documents provide context but do not authorize implementation.

## 6. Bug and Scientific-Issue Workflow

```text
Evidence
→ Observed versus expected behavior
→ Owner and dependency tracing
→ Root-cause analysis
→ Issue record in Practice `docs/error_analysis/` when non-trivial
→ Fix plan in Practice `docs/fix_plans/`
→ Human scope approval
→ Sequential correction
→ Local validation
→ Impact validation
→ Execution evidence in Practice `docs/logs/`
→ Current-status update when required
→ Report
```

## 7. Task States

Use one truthful main-task state:

```text
NOT_STARTED
PLANNING
WAITING_APPROVAL
IN_PROGRESS
BLOCKED
VALIDATING
COMPLETED
```

Only one main logical task should be `IN_PROGRESS` at a time.

## 8. Stop Conditions

Stop the active execution when a canonical rule requires it, when required approval is missing, when the scope must expand, or when validation reveals an unresolved upstream problem.
