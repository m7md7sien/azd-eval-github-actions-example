#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OFFLINE_WORKFLOW = ROOT / ".github" / "workflows" / "azd-eval.yml"
LIVE_WORKFLOW = ROOT / ".github" / "workflows" / "live-evaluation.yml"
AZURE_CONFIG = ROOT / "azure.yaml"
EVAL_CONFIG = ROOT / "live" / "azure.eval.yaml"
FIXTURE = ROOT / "live" / "data" / "golden.jsonl"

EXPECTED_ROWS = [
    {
        "query": "What is the capital of France?",
        "response": "Paris",
        "ground_truth": "Paris",
    },
    {
        "query": "What is 2 + 2?",
        "response": "4",
        "ground_truth": "4",
    },
]


def fail(message: str) -> None:
    raise AssertionError(message)


def load_yaml(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    try:
        parsed = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid YAML: {exc}")
    if not isinstance(parsed, dict):
        fail(f"{path.relative_to(ROOT)} must contain a YAML mapping.")
    return parsed, text


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        fail(f"{message}: expected {expected!r}, found {actual!r}.")


def assert_action_pins(path: Path, text: str) -> None:
    uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", text)
    if not uses:
        fail(f"{path.relative_to(ROOT)} does not use any actions.")
    for action in uses:
        if "@" not in action or not re.fullmatch(r"[0-9a-f]{40}", action.rsplit("@", 1)[1]):
            fail(f"{path.relative_to(ROOT)} has a non-immutable action reference: {action}")


def normalize_powershell(script: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"`\s*\r?\n\s*", " ", script)).strip()


def validate_offline_workflow() -> None:
    workflow, text = load_yaml(OFFLINE_WORKFLOW)
    assert_action_pins(OFFLINE_WORKFLOW, text)

    assert_equal(
        set(workflow.get("on", {}).keys()),
        {"push", "pull_request", "workflow_dispatch"},
        "Offline workflow triggers changed",
    )
    assert_equal(
        workflow.get("permissions"),
        {"contents": "read"},
        "Offline workflow permissions changed",
    )

    scaffold = workflow.get("jobs", {}).get("scaffold", {})
    operating_systems = (
        scaffold.get("strategy", {})
        .get("matrix", {})
        .get("os", [])
    )
    assert_equal(
        operating_systems,
        ["ubuntu-24.04", "windows-2025"],
        "Offline workflow operating-system matrix changed",
    )
    if "AZURE_CLIENT_ID" in text or "AZURE_TENANT_ID" in text or "id-token" in text:
        fail("Offline workflow must remain credential-free.")
    if "Compare-Object $expectedArtifactFiles $artifactFiles" not in text:
        fail("Offline workflow no longer validates its sanitized artifact file set.")


def validate_project_config() -> None:
    azure_config, _ = load_yaml(AZURE_CONFIG)
    assert_equal(
        set(azure_config.keys()),
        {"name", "services"},
        "Root azure.yaml must stay infrastructure-free",
    )
    service = azure_config.get("services", {}).get("live-evaluation")
    assert_equal(
        service,
        {
            "host": "azure.ai.eval",
            "$ref": "./live/azure.eval.yaml",
        },
        "Root azure.yaml live evaluation service changed",
    )

    eval_config, _ = load_yaml(EVAL_CONFIG)
    assert_equal(
        eval_config.get("datasets"),
        [{"name": "ci-golden", "file": "./data/golden.jsonl"}],
        "Live dataset configuration changed",
    )
    evals = eval_config.get("evals", [])
    if len(evals) != 1:
        fail("Live evaluation configuration must declare exactly one evaluation.")
    evaluation = evals[0]
    assert_equal(evaluation.get("name"), "ci-f1-quality", "Live evaluation name changed")
    assert_equal(evaluation.get("dataset"), "ci-golden", "Live evaluation dataset changed")
    assert_equal(evaluation.get("evaluation_level"), "turn", "Live evaluation level changed")
    evaluators = evaluation.get("evaluators", [])
    if len(evaluators) != 1:
        fail("Live evaluation must declare exactly one evaluator.")
    evaluator = evaluators[0]
    assert_equal(evaluator.get("evaluator"), "builtin.f1_score", "Live evaluator changed")
    assert_equal(
        evaluator.get("initialization_parameters"),
        {"threshold": "0.9"},
        "Live evaluator threshold changed",
    )
    assert_equal(
        evaluator.get("data_mapping"),
        {
            "query": "{{item.query}}",
            "response": "{{item.response}}",
            "ground_truth": "{{item.ground_truth}}",
        },
        "Live evaluator data mapping changed",
    )

    rows = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert_equal(rows, EXPECTED_ROWS, "Live deterministic fixture changed")
    for index, row in enumerate(rows):
        assert_equal(
            set(row.keys()),
            {"query", "response", "ground_truth"},
            f"Fixture row {index + 1} contains non-allowlisted fields",
        )


def validate_live_workflow() -> None:
    workflow, text = load_yaml(LIVE_WORKFLOW)
    assert_action_pins(LIVE_WORKFLOW, text)

    assert_equal(
        set(workflow.get("on", {}).keys()),
        {"workflow_dispatch"},
        "Live workflow must remain default-off",
    )
    assert_equal(
        workflow.get("permissions"),
        {"contents": "read", "id-token": "write"},
        "Live workflow permissions changed",
    )

    job = workflow.get("jobs", {}).get("live-evaluation", {})
    assert_equal(
        job.get("environment"),
        {"name": "live-evaluation"},
        "Live workflow protected environment changed",
    )
    if "azd auth login" not in text or "--federated-credential-provider github" not in text:
        fail("Live workflow must keep GitHub OIDC authentication through azd.")

    hero_steps = [
        step
        for step in job.get("steps", [])
        if step.get("name") == "Run Scenario 5 evaluation lifecycle"
    ]
    if len(hero_steps) != 1:
        fail("Live workflow must contain exactly one Scenario 5 lifecycle step.")
    script = normalize_powershell(hero_steps[0].get("run", ""))

    commands = [
        "azd up --no-prompt",
        "azd ai eval run start --eval ci-f1-quality --no-prompt --no-wait -o json",
        "azd ai eval run show $runId --eval ci-f1-quality --wait --fail-on 'pass-rate=0.8' --output json --no-prompt",
        "azd ai eval run output export $runId --eval ci-f1-quality --output-file $rawExport --no-prompt",
    ]
    positions = []
    for command in commands:
        position = script.find(command)
        if position < 0:
            fail(f"Live workflow is missing the required command: {command}")
        positions.append(position)
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        fail("Scenario 5 commands are not in deploy, start, show, export order.")

    start_segment = script[positions[1] : positions[2]]
    if re.search(r"(?<!no-)--wait(?:\s|$)", start_segment):
        fail("Evaluation start must not block.")
    if "azd ai eval create" in script:
        fail("Live workflow must reconcile through azd up instead of direct eval create.")
    if "--project-endpoint" in script or "--path live" in script:
        fail("Lifecycle commands must resolve the checked-in azd service configuration.")

    required_guards = [
        '$status -cne "completed"',
        "$passed -ne 2 -or $failed -ne 0 -or $errored -ne 0",
        "Get-DescendantPropertyValues",
        "$score -lt 0.9",
        "Compare-Object $expectedArtifactFiles $artifactFiles",
        "Remove-Item -LiteralPath $rawPath",
        "$forbiddenValues",
    ]
    for guard in required_guards:
        if guard not in script:
            fail(f"Live workflow is missing required validation or sanitization: {guard}")

    upload_steps = [
        step
        for step in job.get("steps", [])
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    if len(upload_steps) != 1:
        fail("Live workflow must upload exactly one sanitized artifact.")
    upload = upload_steps[0].get("with", {})
    assert_equal(
        upload.get("path"),
        "${{ runner.temp }}/live-evaluation-evidence/results.json",
        "Live artifact upload path changed",
    )


def main() -> int:
    validate_offline_workflow()
    validate_project_config()
    validate_live_workflow()
    print("Validated workflow YAML, azd/evaluation configuration, fixture, and Scenario 5 lifecycle.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, json.JSONDecodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
