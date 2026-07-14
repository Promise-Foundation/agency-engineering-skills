"""Tests for config loading and publication targets."""

from __future__ import annotations

import json

from hypothesize.config import load_config
from hypothesize.targets import render_target, stale_targets, target_files

PUBLICATION = {
    "manifest": {"schema_version": 1, "hypotheses": [], "note": "x < y"},
    "markdown": "| ID | Hypothesis |\n|---|---|\n| **H-1** | **One** |\n",
    "use_case_markdown": "| ID | Use case |\n|---|---|\n",
}


def _config(tmp_path):
    (tmp_path / "hypothesize.toml").write_text(
        "\n".join(
            [
                'catalog = "research/portfolio.toml"',
                "",
                "[runner]",
                'adapter = "behave"',
                'report = "artifacts/research/behave.json"',
                "",
                "[[targets]]",
                'kind = "json"',
                'path = "research/generated/research-status.json"',
                "",
                "[[targets]]",
                'kind = "markdown_region"',
                'path = "README.md"',
                'marker = "research-status"',
                "",
                "[[targets]]",
                'kind = "js"',
                'path = "site/data.js"',
                'variable = "RS"',
            ]
        ),
        encoding="utf-8",
    )
    return load_config(tmp_path)


def test_config_parses_targets(tmp_path):
    config = _config(tmp_path)
    assert config.adapter == "behave"
    assert [t.kind for t in config.targets] == ["json", "markdown_region", "js"]
    assert config.generated_json_target().path.endswith("research-status.json")


def test_json_target_is_sorted_with_trailing_newline(tmp_path):
    config = _config(tmp_path)
    target = next(t for t in config.targets if t.kind == "json")
    text = render_target(target, config.root, PUBLICATION)
    assert text.endswith("}\n")
    assert json.loads(text)["schema_version"] == 1


def test_js_target_escapes_and_wraps(tmp_path):
    config = _config(tmp_path)
    target = next(t for t in config.targets if t.kind == "js")
    text = render_target(target, config.root, PUBLICATION)
    assert text.startswith("window.RS = ")
    assert "\\u003c" in text  # the "<" in the manifest is escaped
    assert text.endswith(";\n")


def test_markdown_region_replaces_between_markers(tmp_path):
    config = _config(tmp_path)
    (config.root / "README.md").write_text(
        "intro\n<!-- BEGIN GENERATED: research-status -->\nOLD\n"
        "<!-- END GENERATED: research-status -->\noutro\n",
        encoding="utf-8",
    )
    target = next(t for t in config.targets if t.kind == "markdown_region")
    text = render_target(target, config.root, PUBLICATION)
    assert "**H-1**" in text
    assert "OLD" not in text
    assert text.startswith("intro\n")
    assert text.endswith("outro\n")


def test_staleness_detects_missing_and_updated(tmp_path):
    config = _config(tmp_path)
    (config.root / "README.md").write_text(
        "<!-- BEGIN GENERATED: research-status -->\n\n"
        "<!-- END GENERATED: research-status -->\n",
        encoding="utf-8",
    )
    # Nothing written yet -> all targets stale.
    stale = stale_targets(config, PUBLICATION)
    assert len(stale) == len(config.targets)
    # Write them, then they are current.
    for path, content in target_files(config, PUBLICATION).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    assert stale_targets(config, PUBLICATION) == []
