# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML>=6.0.2,<7"]
# ///
"""Read-only comparison of sources.yaml targets against matching lock records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml


class Unknown(ValueError):
    """Upstream evidence unavailable or malformed."""


def query_json(url: str):
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "agent-manager-check-updates"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = response.read(10_000_001)
            if len(payload) > 10_000_000:
                raise Unknown("Upstream response exceeds safe size")
            return json.loads(payload)
    except HTTPError as error:
        # Never output URLs with credentials, response bodies or headers.
        raise Unknown(f"GitHub HTTP {error.code}") from error
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise Unknown("Upstream query failed or returned invalid JSON") from error


def check_sources(root: Path, query=query_json) -> list[dict[str, str]]:
    sources = yaml.safe_load((root / "sources.yaml").read_text(encoding="utf-8"))
    lock = json.loads((root / "sources.lock.json").read_text(encoding="utf-8"))
    if not isinstance(sources, dict) or not isinstance(sources.get("groups"), dict) or not isinstance(lock, dict) or not isinstance(lock.get("skills"), dict):
        raise Unknown("Cannot safely parse sources / lock mappings")
    commits = {}
    paths = {}
    rows = []
    for group, settings in sources["groups"].items():
        if not isinstance(settings, dict) or not isinstance(settings.get("skills"), list):
            raise Unknown("Invalid source group")
        for source in settings["skills"]:
            if not isinstance(source, dict) or any(not isinstance(source.get(key), str) or not source[key].strip() for key in ("name", "repo", "path", "ref")):
                raise Unknown("Invalid source identity")
            name, repo, path, ref = (source[key] for key in ("name", "repo", "path", "ref"))
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or PurePosixPath(path).is_absolute() or any(part in {"", ".", ".."} for part in path.split("/")) or "\\" in path or ":" in path:
                raise Unknown("Unsafe upstream repository / path")
            record = lock["skills"].get(name, {})
            matches = isinstance(record, dict) and all(record.get(key) == value for key, value in {**source, "group": group}.items())
            current = record.get("commit", "UNKNOWN") if matches else "UNKNOWN"
            if not isinstance(current, str) or not re.fullmatch(r"[0-9a-f]{40}", current):
                current = "UNKNOWN"
            row = {"Name": name, "Type": "Third-party Skill", "Current": current, "Remote": "UNKNOWN", "Status": "UNKNOWN", "Source": f"{repo}:{path}@{ref}", "Reason": ""}
            key = (repo, ref)
            if key not in commits:
                try:
                    payload = query(f"https://api.github.com/repos/{repo}/commits/{quote(ref, safe='')}")
                    commit = payload.get("sha") if isinstance(payload, dict) else None
                    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
                        raise Unknown("No exact upstream commit")
                    commits[key] = (commit, "")
                except Unknown as error:
                    commits[key] = ("UNKNOWN", str(error))
            remote, reason = commits[key]
            row["Remote"] = remote
            if reason:
                row["Reason"] = reason
            else:
                path_key = (repo, remote, path)
                if path_key not in paths:
                    try:
                        payload = query(f"https://api.github.com/repos/{repo}/contents/{quote(path, safe='/')}?ref={remote}")
                        if not isinstance(payload, list):
                            paths[path_key] = ("UPSTREAM PATH MISSING", "Configured path is not a Skill directory")
                        elif not any(isinstance(item, dict) and item.get("name") == "SKILL.md" and item.get("type") == "file" for item in payload):
                            paths[path_key] = ("UPSTREAM PATH MISSING", "Configured directory has no SKILL.md")
                        else:
                            paths[path_key] = ("OK", "")
                    except Unknown as error:
                        # A 404 is missing only after the exact repo commit was verified.
                        status = "UPSTREAM PATH MISSING" if str(error) == "GitHub HTTP 404" else "UNKNOWN"
                        paths[path_key] = (status, str(error))
                path_status, path_reason = paths[path_key]
                if path_status != "OK":
                    row["Status"], row["Reason"] = path_status, path_reason
                elif current == "UNKNOWN":
                    row["Reason"] = "Missing lock commit or source identity differs from lock"
                else:
                    row["Status"] = "LATEST" if current == remote else "UPDATE AVAILABLE"
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("marketplace", type=Path, help="Confirmed agent-marketplace source root")
    args = parser.parse_args()
    try:
        rows = check_sources(args.marketplace.resolve(strict=True))
    except (Unknown, OSError, ValueError, yaml.YAMLError) as error:
        print(json.dumps({"Status": "BLOCKED", "Reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
