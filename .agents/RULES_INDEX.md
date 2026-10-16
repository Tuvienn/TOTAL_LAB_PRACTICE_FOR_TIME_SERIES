# TIME SERIES — MULTI-AGENT RULE ROUTER

## 1. Purpose

This file is the canonical routing entry point for repository governance, rules,
workflows, and scoped Practice sources.

`working_rule.md` is the Human-owned Human–AI governance charter. The files under
`.agents/rules/` organize active rules by responsibility, and
`.agents/workflows/WORKFLOW.md` owns execution routing.

Native tool entry points must route here and must not duplicate repository rules.

## 2. Governance State

```text
MIGRATION_IN_PROGRESS=false
WORKING_RULE_GOVERNANCE_ACTIVE=true
CANONICAL_RULE_SOURCE_ACTIVE=true
HISTORICAL_ACKNOWLEDGEMENT_AUTHORITY=false
AGENTS_ENTRY_POINT_RETAINED=true
SIGNATURE_PROVENANCE_MIGRATION_COMPLETED=true
NATIVE_ENTRY_POINTS_VERIFIED=true
```

The former `.agent/` paths do not exist in the current repository. They are not
active sources and must not be recreated or deleted without a separate Human-approved
task.

## 3. Active Sources and Routing

Governance charter:

```text
working_rule.md
```

Active rule owners:

```text
.agents/rules/GENERAL_RULES.md
.agents/rules/CODE_RULES.md
.agents/rules/TIME_SERIES_RULES.md
```

Active workflow owner:

```text
.agents/workflows/WORKFLOW.md
```

Routing:

- Always read `working_rule.md` and `rules/GENERAL_RULES.md`.
- Read `rules/CODE_RULES.md` when analyzing, creating, modifying, reviewing, or
  executing code, tests, configuration, architecture, or documentation.
- Read `rules/TIME_SERIES_RULES.md` for Time Series data, analysis, modeling,
  forecasting, evaluation, visualization, or conclusions.
- Follow `workflows/WORKFLOW.md` for task routing, approval gates, execution,
  verification, and reporting.

## 4. Historical Records

Historical acknowledgements are stored only at:

```text
.agents/history/acknowledgements.md
```

This history is provenance only and has no normative authority. Agents and sessions
are not required to read, sign, update, or re-acknowledge it during normal work.

## 5. Scoped Sources

For work under `total_practice/Practice_2/`, also consult:

```text
total_practice/Practice_2/README.md
total_practice/Practice_2/docs/rules/architecture_rule.md
total_practice/Practice_2/docs/rules/rule_code.md
```

Exercise specifications and before-process plans apply only when they exist and their approval state permits execution.

## 6. Rule Precedence

Within the repository-local instruction layer, use this order:

1. The relevant Human-approved exercise specification or before-process plan.
2. The applicable scoped rule under `total_practice/Practice_2/docs/rules/`.
3. `.agents/rules/TIME_SERIES_RULES.md` for Time Series-specific constraints.
4. `.agents/rules/CODE_RULES.md` for code and implementation constraints.
5. `.agents/rules/GENERAL_RULES.md` for repository-wide constraints.
6. `working_rule.md` for the general Human–AI governance charter.
7. `.agents/workflows/WORKFLOW.md` for execution routing and state transitions.

More specific instructions override more general instructions only within their
scope and only when they do not weaken safety, integrity, chronology, approval,
or evidence requirements.

Platform, system, developer, safety, and explicit current Human instructions
remain higher authority than repository-local documentation.

## 7. Conflict Handling

If instructions conflict:

```text
STOP
→ identify the conflicting sources
→ explain the impact
→ do not implement the disputed action
→ wait for Human resolution
```

## 8. Native Entry-Point Contract

Each tool-specific entry point must:

- route to this file;
- contain no duplicated normative repository rule body;
- remain minimal and tool-native;
- be verified before its legacy replacement is retired.

## 9. Maintenance

- Keep this file as a router, not a duplicate rule body.
- Add only paths that exist or are explicitly marked as migration targets.
- Keep historical acknowledgements outside active rules and workflows.
- Do not require agents or sessions to sign or re-acknowledge historical records.
- Update all affected references when a canonical path changes.
