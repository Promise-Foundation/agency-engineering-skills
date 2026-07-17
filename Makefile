.PHONY: research-report research-status research-check

# Run the repo-composition acceptance suite and write the JSON report
# hypothesize reads (see hypothesize.toml's [runner]).
research-report:
	mkdir -p artifacts/research
	python3 -m pytest research/tests -c research/pytest.ini \
		--json-report --json-report-file=artifacts/research/pytest-report.json -q

# Regenerate and WRITE all configured targets (research/generated/research-status.json,
# README.md's generated region). Commit the changes this produces.
research-status: research-report
	hypothesize --root . sync

# Enforce that the committed publication is current. WRITES NOTHING; exits
# non-zero on any stale target or broken traceability. This is what CI runs.
research-check: research-report
	hypothesize --root . check
