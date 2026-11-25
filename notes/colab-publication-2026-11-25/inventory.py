"""Read only pinned local Git objects; write summaries beside this script."""
import collections
import datetime
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()

expected = {
    "freeflow": [f"{c}_{i}" for c in ("SHORT", "MID", "VARY", "OPEN", "LONG") for i in range(1, 26)],
    "values": [f"{c}_{i}" for c, n in (("CTRL1",10),("CTRL2",10),("CTRL3",10),("G1",30),("G2",30),("G3",30)) for i in range(1,n+1)],
}
role = re.compile(r"(?:<\|(?:im_start|user|assistant|system)\|>|(?:^|\n)\s*(?:user|assistant|system)\s*(?:\n|:))", re.I)
pinned = json.loads((OUT/"inventory.json").read_text())
base_ref = pinned["comparison_target"]["sha"]
refs = {b["ref"]: b["sha"] for b in pinned["branches"]}
refs["refs/remotes/origin/reed/colab-yi-34b-chat"] = "b5eac5e383db974d61f91686c88f2fcfeb587a4e"
refs = sorted(refs.items())
report = {"schema_version":1, "generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "comparison_target":{"ref":"refs/remotes/origin/master","sha":base_ref},
          "expected_ids":expected, "branches":[],
          "scope":"Only trace directories newly added against each branch's merge base with pinned origin/master. No network, checkout, or release approval.",
          "flag_policy":{"role_leak":"Heuristic matching capture harness ROLE_RE; flag, not semantic verdict.",
                         "length":"raw.choices[0].finish_reason == length; no inferred word-count threshold.",
                         "empty":"Missing/non-string/whitespace-only result.",
                          "release_qa":"Not performed: semantic quality, full provenance verification, licensing, contamination, duplicate/sampling analysis, and publication sign-off remain separate."},
          "caveats":{"falcon_suffix":"Falcon responses can end with a bare User suffix, which the existing role-leak regex does not catch (it requires a following newline or colon). These suffixes are not added to mechanical flag totals; zero flags is not a clean-content verdict."}}
for ref, sha in refs:
    mb = git("merge-base", base_ref, sha)
    changes = [x.split("\t") for x in git("diff","--name-status",mb,sha).splitlines()]
    added = [p for status,p in changes if status == "A"]
    dirs = sorted({str(Path(p).parent) for p in added if re.match(r"data/traces_(freeflow|values)/[^/]+/[^/]+\.json$",p)})
    b = {"ref":ref,"sha":sha,"merge_base":mb,"pilot":"pilot" in ref,
         "change_status_counts":dict(collections.Counter(s for s,p in changes)),
         "non_trace_changed_paths":[p for s,p in changes if not p.startswith(("data/traces_freeflow/","data/traces_values/"))],
         "trace_directories":[]}
    tree = git("ls-tree","-r",sha).splitlines()
    for directory in dirs:
        if git("ls-tree",mb,"--",directory):
            raise RuntimeError("Candidate is not a wholly added directory: "+directory)
        files = {}
        for line in tree:
            meta,path = line.split("\t",1)
            if path.startswith(directory+"/"):
                files[path] = meta.split()[2]
        probe = "freeflow" if "/traces_freeflow/" in directory else "values"
        ids = {Path(p).stem for p in files if p.endswith(".json") and str(Path(p).parent)==directory}
        d = {"path":directory,"probe":probe,"files":len(files),"expected_count":len(expected[probe]),
             "missing_ids":sorted(set(expected[probe])-ids),"extra_ids":sorted(ids-set(expected[probe])),
             "condition_counts":dict(collections.Counter(i.rsplit("_",1)[0] for i in ids)),
             "flags":[],"models":[],"revisions":[]}
        models=set(); revisions=set()
        bare_user_suffix_count = 0
        proc = subprocess.Popen(["git","cat-file","--batch"],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        for path, oid in files.items():
            proc.stdin.write((oid+"\n").encode()); proc.stdin.flush()
            header=proc.stdout.readline().decode().split()
            raw=proc.stdout.read(int(header[2])); proc.stdout.read(1)
            reasons=[]
            try:
                data=json.loads(raw)
                text=data.get("result")
                choice=((data.get("raw") or {}).get("choices") or [{}])[0]
                if not isinstance(text,str) or not text.strip(): reasons.append("empty")
                if data.get("error"): reasons.append("error")
                if choice.get("finish_reason")=="length": reasons.append("length")
                elif choice.get("finish_reason")!="stop": reasons.append("non_stop_finish")
                if isinstance(text,str):
                    if re.search(r"(?:^|\n)\s*User\s*$", text, re.I):
                        bare_user_suffix_count += 1
                    if role.search(text): reasons.append("role_leak")
                    if (choice.get("message") or {}).get("content")!=text: reasons.append("final_answer_mismatch")
                    for marker,name in (("\ufffd","replacement_character"),("\x00","nul"),("Ġ","tokenizer_marker"),("Ċ","tokenizer_marker")):
                        if marker in text: reasons.append(name)
                if data.get("condition")!=Path(path).stem.rsplit("_",1)[0]: reasons.append("condition_mismatch")
                models.add(str(data.get("model")))
                revisions.add(str((data.get("local_deployment") or {}).get("model_revision")))
            except (ValueError,TypeError,AttributeError):
                reasons.append("invalid_json_or_schema")
            if reasons: d["flags"].append({"path":path,"reasons":sorted(set(reasons))})
        proc.stdin.close(); proc.wait()
        d["models"]=sorted(models); d["revisions"]=sorted(revisions)
        if "colab-falcon-7b-instruct" in ref:
            d["bare_user_suffix_count"] = bare_user_suffix_count
        d["flag_counts"]=dict(collections.Counter(r for f in d["flags"] for r in f["reasons"]))
        d["index_complete"]=not d["missing_ids"] and not d["extra_ids"] and len(files)==len(expected[probe])
        b["trace_directories"].append(d)
    b["missing_probe_directories"] = sorted(set(expected)-{d["probe"] for d in b["trace_directories"]})
    report["branches"].append(b)
all_dirs=[d for b in report["branches"] for d in b["trace_directories"]]
report["totals"]={"branches":len(refs),"added_trace_directories":len(all_dirs),"trace_files":sum(d["files"] for d in all_dirs),
                  "index_complete_directories":sum(d["index_complete"] for d in all_dirs),
                  "flagged_traces":sum(len(d["flags"]) for d in all_dirs),
                  "flags":dict(sum((collections.Counter(d["flag_counts"]) for d in all_dirs),collections.Counter()))}
(OUT/"inventory.json").write_text(json.dumps(report,indent=2)+"\n")
lines=["# Pinned Colab intake — 2026-11-25","",
       f"Comparison target: `origin/master` at `{base_ref}`. All branch SHAs and individual merge bases are in `inventory.json`.",
       "Only wholly added trace directories relative to those merge bases are counted. Pilot is inspected the same way; unrelated inherited baseline data is not counted.",
       "", "## Intake counts", "",json.dumps(report["totals"],sort_keys=True),"",
       "Exact expected IDs: freeflow SHORT/MID/VARY/OPEN/LONG each 1–25 (125); values CTRL1/CTRL2/CTRL3 each 1–10 and G1/G2/G3 each 1–30 (120). Conditions are checked against filenames. Full lists are in JSON.",
       "", "| Branch | Pinned SHA | Freeflow | Values | Flagged traces | Index complete |",
       "|---|---|---:|---:|---:|---|"]
for b in report["branches"]:
    ds=b["trace_directories"]
    counts={p:sum(d["files"] for d in ds if d["probe"]==p) for p in expected}
    lines.append(f"| {b['ref'].split('/')[-1]} | `{b['sha']}` | {counts['freeflow']} | {counts['values']} | {sum(len(d['flags']) for d in ds)} | {bool(ds) and all(d['index_complete'] for d in ds)} |")
lines+=["","## Mechanical flags (not release QA)","",
        "Empty, error, length cap, non-stop finish, role-continuation heuristic, answer mismatch, malformed text markers, and condition mismatch are checked. Exact flagged paths and reasons, missing/extra IDs, models and revisions are in JSON. No response text or endpoint/credential material is copied here.",
        "", "## Release QA remains separate","",
        report["flag_policy"]["release_qa"],
        "An index-complete directory or zero mechanical flags is **not** publication approval. Role leakage is a heuristic; no word-count quality threshold is assumed.",
        "", "Reproduce locally: `python3 notes/colab-publication-2026-11-25/inventory.py` (reuses inventory's pinned heads and comparison target, including the explicit clean Yi-34B pin). Only the missing `reed/colab-yi-34b-chat` branch was fetched for this refresh; no other heads were refreshed, no checkout, commits or posting."]
lines += ["", "## Exceptions and flag breakdown", "",
          "The phi-3-small-8k-instruct ref adds no trace directories: both probes are absent from this intake (not a passing 0/0 cell). Pilot deepseek does add both full directories; its three length flags must not be lost by treating it as an already published baseline.",
          f"All {report['totals']['index_complete_directories']} present directories have exact expected indexes; see JSON for missing/extra IDs and flag categories. There are {report['totals']['flagged_traces']} distinct flagged traces; categories can overlap.",
          report["caveats"]["falcon_suffix"],
          ""]
for b in report["branches"]:
    if "colab-falcon-7b-instruct" in b["ref"]:
        lines.append("Falcon bare `User` suffix counts (separate caveat, not extra flags): "+", ".join(f"{d['probe']} {d['bare_user_suffix_count']}/{d['files']}" for d in b["trace_directories"])+".")
for b in report["branches"]:
    for d in b["trace_directories"]:
        if d["flags"]:
            lines.append(f"- {b['ref'].split('/')[-1]} / {d['probe']}: "+json.dumps(d["flag_counts"],sort_keys=True))
(OUT/"README.md").write_text("\n".join(lines)+"\n")
print(json.dumps(report["totals"]))
