# Deployment Plan

## Status

Validated

## Scope

- Modify the existing azd evaluation sample to reconcile the checked-in live evaluation configuration.
- Do not provision Azure infrastructure, deploy models, add secrets, or broaden permissions.
- Preserve the existing offline scaffold, OIDC authentication, security controls, and evidence sanitization.

## Planned Changes

- Inspect repository instructions, workflows, live evaluation configuration, documentation, and validation coverage.
- Add the minimal azd project/service configuration required for `azd up --no-prompt`.
- Align the live workflow with the Scenario 5 deploy, asynchronous start, reattach/gate, and export sequence.
- Sanitize exported per-sample evidence through an explicit allowlist and clean raw output from runner temporary storage.
- Update documentation and focused validation tests.

## Validation

- Parse both workflow YAML files.
- Validate azd and evaluation configuration, schema, and deterministic fixture.
- Assert command order, required flags, completion state, exact `2/0/0` counts, artifact allowlist, and cleanup behavior.
- Run the smallest relevant repository checks without claiming hosted Azure success.

### All validation checks pass

- [x] 1. AZD Installation
- [x] 2. Schema Validation
- [x] 3. Environment Setup
- [x] 4. Authentication Check
- [x] 5. Subscription/Location Check (not applicable: no resources are provisioned)
- [x] 6. Aspire Pre-Provisioning Checks (not applicable)
- [x] 7. Provision Preview (not applicable: no IaC; service-target parsing validated)
- [x] 8. Build Verification
- [x] 9. Docker Build Context Validation (not applicable)
- [x] 10. Package Validation
- [x] 11. Azure Policy Validation (not applicable: no resources are provisioned)
- [x] 12. Aspire Post-Provisioning Checks (not applicable)

## Constraints

- Existing Azure AI project endpoint only; no infrastructure provisioning.
- Hosted live success remains unclaimed because the current personal-repository OIDC token lacks the required enterprise claim.
- Local lifecycle evidence may be described only within its documented limits.

## Decisions

- Mode: modify an existing CI sample.
- Recipe: azd service-target configuration only.
- Azure resources to provision: none.
- Subscription, location, quota, and infrastructure are not applicable because the workflow reconciles an evaluation definition against an existing project endpoint.
- Approval: the user explicitly directed implementation and a coordinating session confirmed proceeding directly.

## Validation Proof

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Repository validation | `python scripts\validate.py` | Passed: parsed both workflow YAML files and validated configuration, fixture, command order/flags, assertions, sanitization, and cleanup | 2026-10-05T22:10:45+03:00 |
| Diff formatting | `git diff --check` | Passed | 2026-10-05T22:10:45+03:00 |
| PowerShell syntax | `System.Management.Automation.Language.Parser.ParseFile(...)` on the Scenario 5 step | Passed | 2026-10-05T22:10:45+03:00 |
| azd installation | `azd version` | Passed: 1.34.1 | 2026-10-05T22:10:45+03:00 |
| Authentication status | `azd auth login --check-status` | Passed | 2026-10-05T22:10:45+03:00 |
| Service-target schema | `azd show --output json` in a disposable project | Passed: `live-evaluation` service recognized | 2026-10-05T22:10:45+03:00 |
| Service packaging | `azd package --no-prompt` in a disposable project | Passed | 2026-10-05T22:10:45+03:00 |
| Sanitizer behavior | Mocked Scenario 5 lifecycle with representative export JSON | Passed: two allowlisted rows produced and raw files removed | 2026-10-05T22:10:45+03:00 |

Hosted live Azure execution was not run and is not claimed.
