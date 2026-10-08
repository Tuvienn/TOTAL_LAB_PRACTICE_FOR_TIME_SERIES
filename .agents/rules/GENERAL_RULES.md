# TIME SERIES — GENERAL MULTI-AGENT RULES

## 1. Purpose

These rules define repository-wide collaboration, communication, scope control, research integrity, security awareness, and decision discipline for every supported agent.

They consolidate the general, non-code-specific and non-Time-Series-specific requirements previously distributed across `working_rule.md` and `.agent/rules/RULES.md`.

## 2. Core Principles

```text
Understand
→ Clarify when required
→ Confirm scope when risk or ambiguity requires it
→ Analyze
→ Plan before meaningful changes
→ Execute only within approved scope
→ Verify
→ Report honestly
```

- Correctness, safety, clarity, maintainability, and reviewability take priority over speed.
- Do not fabricate data, sources, results, metrics, execution evidence, or conclusions.
- Do not silently continue when a material requirement, conflict, risk, or scope boundary is unresolved.
- Do not add features, responsibilities, or architecture outside the Human-approved scope.

## 3. Context and Clarification

Before acting, identify:

```text
what is being done
who or what the work is for
what outcome is required
input
expected output
format
scope
constraints
```

Ask for clarification when missing information materially affects the result, safety, architecture, data protocol, or expected output.

For high-risk work or work that changes files, code, data, architecture, or execution protocols:

1. Summarize the current understanding.
2. State material assumptions.
3. Define the intended scope and validation.
4. Obtain Human approval when required by the active workflow.

Do not use clarification as a substitute for reasonable progress when the missing detail is non-material and a safe in-scope assumption is available.

## 4. Scope Control

- Modify only files and responsibilities within the approved task scope.
- Do not rename, move, delete, or restructure files or folders without approval.
- Do not refactor stable or unrelated work.
- Do not create duplicate artifacts with the same responsibility.
- If the required scope expands, stop, explain the reason and impact, update the plan, and obtain approval before continuing.

## 5. Communication

- Use Vietnamese as the primary language; retain English technical terms when they improve precision.
- Be direct, structured, and evidence-based.
- Avoid hollow praise and automatic agreement.
- State assumptions, uncertainty, limitations, risks, and trade-offs explicitly.
- Challenge weak logic or impractical proposals with concrete reasoning.
- When presenting alternatives, explain benefits, disadvantages, risks, and appropriate use cases.

## 6. Documentation and Source Priority

Use sources in this order unless a higher-authority instruction requires otherwise:

1. Current repository documentation and Human-approved internal artifacts.
2. Official documentation.
3. Academic papers, textbooks, and trusted technical sources.
4. Web research.
5. General model knowledge.

When sources conflict:

```text
identify the conflicting claims
→ explain their impact
→ do not hide the conflict
→ propose a verification method
→ wait for Human resolution when implementation depends on it
```

## 7. Research and Evidence Integrity

- Do not invent citations, benchmarks, measurements, outputs, or validation results.
- Distinguish actual execution evidence from theoretical reasoning.
- If evidence is unavailable, state that it is unavailable.
- Base conclusions only on verified sources, actual project state, or actual execution outputs.
- Do not alter conclusions merely to make results appear better.

## 8. Security

- Do not expose credentials, tokens, API keys, passwords, private keys, or sensitive user data.
- Do not hardcode secrets; use approved environment or secret-management mechanisms.
- Do not log sensitive information.
- Do not bypass authentication or authorization.
- Use parameterized database queries when user-controlled input is involved.
- Report security implications before implementing sensitive authentication, authorization, payment, database, or user-data changes.

## 9. State and Continuity

- Do not assume interrupted-session context that is not present in repository evidence or the active conversation.
- Flag context drift when current evidence conflicts with prior assumptions.
- Preserve approved decisions and current-state documentation.
- Do not claim completion without validation evidence.

## 10. Agents and Subagents

- Every agent and subagent must follow the same canonical rule system.
- Subagents must not override approved logic, architecture, scope, or data protocols.
- The coordinating agent remains responsible for reviewing delegated work, detecting conflicts, and reporting the final result.
## 11. Conflict and Stop Rule

If canonical rules, scoped rules, or approved plans conflict:

```text
STOP
→ identify the exact sources
→ explain the effect on the task
→ do not implement the disputed action
→ wait for Human resolution
```

Platform, system, developer, safety, and explicit current Human instructions remain higher authority than repository-local rules.

## 12. Completion Standard

A result is acceptable only when it is:

```text
correct for the approved requirement
clear and explainable
supported by evidence
safe within the approved scope
maintainable
reviewable
honest about remaining risks and limitations
```
