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

It **does not** authenticate to Azure, register a dataset, contact a project
endpoint, create or run an evaluation, or prove that a live evaluation
succeeds.

## Default-off live quality gate

The manually dispatched
[`live-evaluation.yml`](.github/workflows/live-evaluation.yml) workflow is a
real Foundry quality gate. It authenticates with GitHub OIDC, publishes the
two-row `live/` dataset and F1 evaluation, waits for the run, requires a
100-percent pass rate, verifies `passed=2`, `failed=0`, and `errored=0`, and
uploads only a sanitized count summary.

Configure the `live-evaluation` GitHub environment with these environment
secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_AI_PROJECT_ENDPOINT`

The federated identity needs the **Foundry User** role at the Foundry project
scope. The workflow uses no client secret and the `builtin.f1_score` evaluator
requires no model deployment.

The exact create/run lifecycle was validated locally against a disposable
Foundry project. A successful GitHub Actions live run is not claimed yet; the
repository run remains pending.

The broader [Azure/azure-dev#10178 release harness][release-harness] has
different release-validation goals and is intentionally not reproduced here.

## Immutable pins

The workflow pins the registry release, both extension versions, the `azd`
version, and every GitHub Action to a full commit SHA. To test a later build:

1. replace the registry URL with the new immutable release URL;
2. update both extension versions from that registry in the same change;
3. keep the exact-version checks aligned with those pins; and
4. update action SHAs only after reviewing the corresponding upstream release.

Do not replace the registry URL with a moving `latest` URL.

[build-47]: https://github.com/m7md7sien/azd-foundry-feed/releases/tag/extensions-2026-10-05-47
[release-harness]: https://github.com/Azure/azure-dev/pull/10178
