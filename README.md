# azd evaluation extension GitHub Actions example

This repository is a small public-consumer example for the prerelease `azd`
evaluation extensions.

## Offline install and scaffold

The default workflow runs on Ubuntu and Windows without Azure credentials:

1. installs `azd` 1.34.1;
2. registers the immutable [Build 47 extension registry][build-47];
3. installs and verifies exact extension versions;
4. copies the synthetic fixture to runner-temporary storage;
5. runs `azd ai eval init` noninteractively; and
6. verifies and uploads the generated local project wiring.

A successful job proves that the pinned extension packages install and that
their offline scaffold command produces the expected dataset, evaluation, and
`azure.yaml` service configuration on both runner operating systems.

The successful [main offline workflow run][offline-run] passed on both Ubuntu
and Windows.

It **does not** authenticate to Azure, register a dataset, contact a project
endpoint, create or run an evaluation, or prove that a live evaluation
succeeds.

## Default-off live quality gate

The manually dispatched
[`live-evaluation.yml`](.github/workflows/live-evaluation.yml) workflow is a
real Foundry quality gate aligned with Scenario 5 (Automation and CI/CD) from
`coreai-microsoft/foundrysdk_specs#251` at
`ac6194cfc34dbd4f29a829a586ed66fda6d61b8b`. It authenticates with GitHub
OIDC and then:

1. reconciles the checked-in `live/azure.eval.yaml` service with
   `azd up --no-prompt`;
2. starts `ci-f1-quality` without blocking and captures the JSON `run_id`;
3. reattaches with `azd ai eval run show --wait --fail-on pass-rate=0.8`;
4. still requires completed status and the deterministic
   `passed=2`, `failed=0`, `errored=0` result; and
5. exports the complete per-sample result to runner-temporary storage, derives
   a two-row allowlisted evidence document, and uploads only that document.

The uploaded JSON contains status, aggregate counts, evaluator name and
threshold, and for each deterministic fixture row only `query`, `response`,
`ground_truth`, `score`, and `passed`. The workflow validates the artifact file
set and rejects the project endpoint, credentials, tokens, and evaluation run
identifier before upload. Raw deploy, start, show, and export output remains in
runner-temporary files and is removed in `finally` cleanup.

Configure the `live-evaluation` GitHub environment with these environment
secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_AI_PROJECT_ENDPOINT`

The federated identity needs the **Foundry User** role at the Foundry project
scope. The workflow uses no client secret and the `builtin.f1_score` evaluator
requires no model deployment.

The earlier local live lifecycle was validated against a disposable Foundry
project with 2 passed, 0 failed, and 0 errored. That evidence predates this
exact GitHub Actions hero sequence, so it does not prove the updated hosted
workflow. A live GitHub Actions success remains unclaimed: this personal
repository cannot complete OIDC against Microsoft's tenant because its GitHub
token has an empty `enterprise` claim. Tenant policy returns `AADSTS7002381`
and requires `enterprise` to be `microsoft`, `github`, or
`microsoftopensource`.

The default-off workflow remains a valid reusable template when hosted by an
enterprise-backed GitHub organization whose token has an accepted
`enterprise` claim, or when targeting a tenant without that policy.

The broader [Azure/azure-dev#10178 release harness][release-harness] has
different release-validation goals and is intentionally not reproduced here.

Run `python scripts/validate.py` to parse both workflow files and validate the
infrastructure-free azd service reference, evaluation schema, deterministic
fixture, Scenario 5 command order and flags, explicit result assertions,
artifact allowlist, and raw-output cleanup.

## Immutable pins

The workflow pins the registry release, both extension versions, the `azd`
version, and every GitHub Action to a full commit SHA. To test a later build:

1. replace the registry URL with the new immutable release URL;
2. update both extension versions from that registry in the same change;
3. keep the exact-version checks aligned with those pins; and
4. update action SHAs only after reviewing the corresponding upstream release.

Do not replace the registry URL with a moving `latest` URL.

[build-47]: https://github.com/m7md7sien/azd-foundry-feed/releases/tag/extensions-2026-10-05-47
[offline-run]: https://github.com/m7md7sien/azd-eval-github-actions-example/actions/runs/37356577007
[release-harness]: https://github.com/Azure/azure-dev/pull/10178
