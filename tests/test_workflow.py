from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "daily.yml"


def load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_exists_and_scheduled():
    workflow = load_workflow()
    triggers = workflow.get("on") or workflow.get(True)
    assert triggers is not None
    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert triggers["schedule"][0]["cron"] == "0 22 * * *"


def test_workflow_runs_all_fields():
    workflow = load_workflow()
    steps = workflow["jobs"]["daily"]["steps"]
    text = "\n".join(str(step.get("run", "")) for step in steps)
    for field in ("labor", "ownership", "policy"):
        assert f"make daily FIELD={field}" in text


def test_workflow_commits_data_and_digests():
    workflow = load_workflow()
    steps = workflow["jobs"]["daily"]["steps"]
    text = "\n".join(str(step.get("run", "")) for step in steps)
    assert "git add data digests state" in text
    assert "git commit" in text
    assert "git push" in text


def test_workflow_has_write_permission():
    workflow = load_workflow()
    assert workflow["permissions"]["contents"] == "write"
