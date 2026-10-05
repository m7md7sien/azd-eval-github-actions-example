# azd evaluation extension GitHub Actions example

This repository is a small public-consumer example for the prerelease `azd`
evaluation extensions. The default workflow runs on Ubuntu and Windows without
Azure credentials:

1. installs `azd` 1.34.1;
2. registers the immutable [Build 47 extension registry][build-47];
3. installs and verifies exact extension versions;
4. copies the synthetic fixture to runner-temporary storage;
5. runs `azd ai eval init` noninteractively; and
6. verifies and uploads the generated local project wiring.

A successful job proves that the pinned extension packages install and that
their offline scaffold command produces the expected dataset, evaluation, and
`azure.yaml` service configuration on both runner operating systems.

It **does not** authenticate to Azure, register a dataset, contact a project or
model endpoint, create or run an evaluation, or prove that a live evaluation
succeeds. The broader [Azure/azure-dev#10178 release harness][release-harness]
has different release-validation goals and is intentionally not reproduced
here.

## Immutable pins

The workflow pins the registry release, both extension versions, the `azd`
version, and every GitHub Action to a full commit SHA. To test a later build:

1. replace the registry URL with the new immutable release URL;
2. update both extension versions from that registry in the same change;
3. keep the exact-version checks aligned with those pins; and
4. update action SHAs only after reviewing the corresponding upstream release.

Do not replace the registry URL with a moving `latest` URL.

## Live evaluation follow-up

A live OIDC workflow is intentionally omitted because the complete live
resource/configuration contract could not be established from the available
prerelease CLI help and source without inventing steps. Once that contract is
published and validated, add a separate, default-off `workflow_dispatch`
workflow that:

- grants only `contents: read` and `id-token: write`;
- reads Azure identifiers and resource settings from GitHub environment
  variables or secrets;
- authenticates without a client secret by running
  `azd auth login --federated-credential-provider github`; and
- executes and verifies the documented create/run/results lifecycle with
  bounded cleanup.

[build-47]: https://github.com/m7md7sien/azd-foundry-feed/releases/tag/extensions-2026-10-05-47
[release-harness]: https://github.com/Azure/azure-dev/pull/10178
