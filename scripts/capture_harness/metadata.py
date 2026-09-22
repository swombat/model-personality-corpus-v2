#!/usr/bin/env python3
"""Write sourced model metadata and merge release dates without guessing from listing dates."""

import argparse, datetime, fcntl, json
from pathlib import Path
from engine import atomic


def write_metadata(config, validate=False):
    c = config
    date = c.get("release_date")
    if date:
        assert datetime.date.fromisoformat(date).isoformat() == date
        assert c.get("release_date_source"), "release date needs an explicit source"
    record = {
        k: c.get(k)
        for k in (
            "model",
            "slug",
            "label",
            "family",
            "or_provider",
            "quantization",
            "release_date",
            "release_date_source",
            "endpoint_snapshot",
        )
    }
    record["release_date_status"] = "sourced" if date else "unknown"
    path = Path(c["phase"]) / "model_metadata.json"
    registry = (
        Path(c["analysis_root"]) / "website/src/generated/model-release-dates.json"
    )
    sources = registry.with_name("model-release-date-sources.json")
    if validate:
        assert json.loads(path.read_text()) == record
        if date:
            assert json.loads(registry.read_text())[c["slug"]] == date
            assert (
                json.loads(sources.read_text())[c["slug"]] == c["release_date_source"]
            )
        return
    lock = Path(c["analysis_root"]) / "logs/capture-harness-metadata.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        dates = json.loads(registry.read_text()) if registry.exists() else {}
        provenance = json.loads(sources.read_text()) if sources.exists() else {}
        if date:
            assert dates.get(c["slug"], date) == date, (
                "conflicting existing release date"
            )
            assert (
                provenance.get(c["slug"], c["release_date_source"])
                == c["release_date_source"]
            ), "conflicting source"
            dates[c["slug"]] = date
            provenance[c["slug"]] = c["release_date_source"]
            atomic(registry, dates)
            atomic(sources, provenance)
        atomic(path, record)
    write_metadata(c, True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("config", type=Path)
    p.add_argument("--validate", action="store_true")
    a = p.parse_args()
    write_metadata(json.loads(a.config.read_text()), a.validate)
