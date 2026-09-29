#!/usr/bin/env python3
"""Copy and verify local iCloud exports in a Google Drive for Desktop folder."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(root):
    root = Path(root).resolve()
    return [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
             "sha256": digest(p)} for p in sorted(root.rglob("*")) if p.is_file()]


def uploaded(path):
    if sys.platform != "darwin":
        return False
    r = subprocess.run(["fileproviderctl", "evaluate", str(path)], capture_output=True,
                       text=True, timeout=15)
    return r.returncode == 0 and "isUploaded = 1" in r.stdout and "isUploading = 1" not in r.stdout


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="write a source manifest")
    s.add_argument("source", type=Path); s.add_argument("manifest", type=Path)
    c = sub.add_parser("copy", help="copy and hash-check files into Drive for Desktop")
    c.add_argument("source", type=Path); c.add_argument("manifest", type=Path); c.add_argument("drive", type=Path)
    c.add_argument("--wait", action="store_true", help="wait until macOS reports cloud upload complete")
    c.add_argument("--timeout", type=int, default=3600, help="upload wait limit in seconds")
    v = sub.add_parser("verify", help="report cloud-verified files safe to remove from source")
    v.add_argument("source", type=Path); v.add_argument("manifest", type=Path); v.add_argument("drive", type=Path)
    v.add_argument("--delete", action="store_true", help="delete only the verified source files")
    v.add_argument("--min-bytes", type=int, default=0, help="delete nothing unless this verified total is available")
    a = p.parse_args()
    rows = json.loads(a.manifest.read_text()) if a.cmd != "scan" else None
    if a.cmd == "scan":
        rows = scan(a.source); a.manifest.write_text(json.dumps(rows, indent=2) + "\n")
        print(f"manifest: {len(rows)} files, {sum(x['bytes'] for x in rows)} bytes")
        return
    if a.cmd == "copy":
        root = a.source.resolve()
        for x in rows:
            src, dst = root / x["path"], a.drive / x["path"]
            if not src.is_file() or src.stat().st_size != x["bytes"] or digest(src) != x["sha256"]:
                raise SystemExit(f"source changed; stopped: {x['path']}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists(): shutil.copy2(src, dst)
            if dst.stat().st_size != x["bytes"] or digest(dst) != x["sha256"]:
                raise SystemExit(f"copy mismatch; stopped: {x['path']}")
        if a.wait:
            for x in rows:
                dst = a.drive / x["path"]
                deadline = time.monotonic() + a.timeout
                while not uploaded(dst):
                    if time.monotonic() >= deadline: raise SystemExit(f"upload timeout: {x['path']}")
                    time.sleep(2)
        print(f"copied and hash-checked {len(rows)} files")
        return
    good, missing = [], []
    for x in rows:
        src, dst = a.source / x["path"], a.drive / x["path"]
        ok = (src.is_file() and dst.is_file() and src.stat().st_size == dst.stat().st_size == x["bytes"]
              and digest(src) == digest(dst) == x["sha256"] and uploaded(dst))
        (good if ok else missing).append((x, src))
    total = sum(x["bytes"] for x, _ in good)
    print(f"cloud-verified: {len(good)} files, {total} bytes; unverified: {len(missing)}")
    if a.delete and total >= a.min_bytes:
        for _, src in good: src.unlink()
        print(f"deleted {len(good)} verified source files")
    elif a.delete:
        print(f"threshold not met ({total} < {a.min_bytes}); nothing deleted")
    elif good:
        print("dry run; add --delete to remove these verified source files")


if __name__ == "__main__":
    main()
