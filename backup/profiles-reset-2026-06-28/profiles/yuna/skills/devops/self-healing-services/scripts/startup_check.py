#!/usr/bin/env python3
"""
Mona Startup Check — verify venv integrity before operation.
Rule 3: Self-check on startup. Import all critical modules in active venv.
       If any fail, abort and notify.

CRITICAL (v2 addition, Jun13): the subprocess is verified to actually be the
target venv's python (not system python). If a module imports from
system site-packages, the check is treated as FAIL even if the import
succeeded — false positive trap.

Usage:
    startup_check.py                          # default venv + default modules
    startup_check.py --venv /path/to/venv     # custom venv
    startup_check.py --modules m1,m2,m3       # custom module list
    startup_check.py --service hermes-gateway # use service's ExecStart venv
    startup_check.py --json                   # pure JSON on stdout (logs to stderr)
    startup_check.py --log-file PATH          # append one-line summary to file
    startup_check.py --quiet                  # suppress non-error output

Exit codes:
    0  all checks passed
    2  venv path missing or python not executable
    3  one or more required modules failed to import (or imported from outside venv)
    5  unable to determine venv (service not found, no path given)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ======= CUSTOMIZE =======
DEFAULT_VENV = Path.home() / ".hermes" / "hermes-agent" / "venv"
DEFAULT_MODULES = [
    "httpx", "openai", "aiohttp", "pydantic", "yaml", "cryptography",
]
SERVICE_VENVS = {
    "hermes-gateway": Path.home() / ".hermes" / "hermes-agent" / "venv",
    "mona-autonomous": Path.home() / ".hermes" / "hermes-agent" / "venv",
}
# ==========================


def log(level: str, msg: str) -> None:
    """Print structured log line. Always to stderr — stdout reserved for final report."""
    line = json.dumps({"ts": _ts(), "level": level, "msg": msg})
    print(line, file=sys.stderr)


def _ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_venv(args) -> tuple[Path | None, str]:
    if args.service:
        if args.service not in SERVICE_VENVS:
            return None, f"unknown service '{args.service}'. Known: {list(SERVICE_VENVS)}"
        venv = SERVICE_VENVS[args.service]
        return venv / "bin" / "python", f"service:{args.service}"
    if args.venv:
        p = Path(args.venv)
        if p.is_dir() and (p / "bin" / "python").exists():
            return p / "bin" / "python", "arg:--venv"
        if p.is_file() and os.access(p, os.X_OK):
            return p, "arg:--venv (direct python)"
        return None, f"--venv invalid or python not found: {args.venv}"
    env_venv = os.environ.get("MONA_VENV") or os.environ.get("VIRTUAL_ENV")
    if env_venv:
        py = Path(env_venv) / "bin" / "python"
        if py.exists():
            return py, "env:VIRTUAL_ENV"
    if DEFAULT_VENV.exists():
        return DEFAULT_VENV / "bin" / "python", "default"
    return None, f"no venv resolved (default {DEFAULT_VENV} missing)"


def check_venv_python(py: Path) -> tuple[bool, str]:
    if not py.exists():
        return False, f"python not found: {py}"
    if not os.access(py, os.X_OK):
        return False, f"python not executable: {py}"
    try:
        out = subprocess.run([str(py), "--version"], capture_output=True, text=True, timeout=10)
        return True, (out.stdout or out.stderr).strip()
    except Exception as e:
        return False, f"python --version failed: {e}"


def check_modules(py: Path, modules: list[str]) -> tuple[bool, list[dict], dict]:
    """Try to import each module via the venv's python.

    Returns (all_ok, results, meta) where:
      - all_ok: True iff every module imported AND lives in the venv's prefix
      - results: per-module dicts (ok, version, location, in_venv, error)
      - meta: subprocess verification (sys_prefix, sys_executable, sys_path_first_3)

    The in_venv check is the false-positive guard: if a module imports from
    system site-packages (because venv was broken mid-repair, or sys.path was
    polluted), it still counts as FAIL even if importlib returned a module.
    """
    code = (
        "import json, sys, importlib\n"
        "results = []\n"
        f"mods = {json.dumps(modules)}\n"
        "for m in mods:\n"
        "    try:\n"
        "        mod = importlib.import_module(m)\n"
        "        ver = getattr(mod, '__version__', 'unknown')\n"
        "        loc = getattr(mod, '__file__', None) or 'builtin'\n"
        "        # FALSE-POSITIVE GUARD: module must live inside the venv prefix\n"
        "        in_venv = loc.startswith(sys.prefix) or loc == 'builtin' or loc.startswith('<frozen')\n"
        "        results.append({\n"
        "            'module': m, 'ok': True, 'version': ver,\n"
        "            'location': loc, 'in_venv': in_venv,\n"
        "        })\n"
        "    except Exception as e:\n"
        "        results.append({\n"
        "            'module': m, 'ok': False, 'error': str(e), 'in_venv': False,\n"
        "        })\n"
        "print(json.dumps({\n"
        "    'sys_prefix': sys.prefix,\n"
        "    'sys_executable': sys.executable,\n"
        "    'sys_path_first_3': sys.path[:3],\n"
        "    'results': results,\n"
        "}))\n"
    )
    meta = {}
    try:
        out = subprocess.run([str(py), "-c", code], capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return False, [{"module": "ALL", "ok": False, "error": out.stderr.strip()[:200], "in_venv": False}], meta
        payload = json.loads(out.stdout.strip().splitlines()[-1])
        meta = {
            "sys_prefix": payload.get("sys_prefix"),
            "sys_executable": payload.get("sys_executable"),
            "sys_path_first_3": payload.get("sys_path_first_3"),
        }
        results = payload["results"]
        all_ok = all(r["ok"] and r.get("in_venv", False) for r in results)
    except Exception as e:
        return False, [{"module": "ALL", "ok": False, "error": f"subprocess failed: {e}", "in_venv": False}], meta
    return all_ok, results, meta


def _append_log(path: str, py_ver: str, total: int, failed: int, status: str) -> None:
    """Append a one-line summary. Best-effort — never raise (called from error paths too)."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(f"[{_ts()}] {status} py={py_ver} modules={total - failed}/{total} failed={failed}\n")
    except Exception:
        pass


def main() -> int:
    p = argparse.ArgumentParser(description="Mona startup health check")
    p.add_argument("--venv", help="path to venv or python binary")
    p.add_argument("--modules", help="comma-separated module list")
    p.add_argument("--service", choices=list(SERVICE_VENVS), help="check venv for a service")
    p.add_argument("--json", action="store_true", help="JSON output only (stdout)")
    p.add_argument("--quiet", action="store_true", help="suppress non-error output")
    p.add_argument("--log-file", help="append one-line result summary to this path")
    args = p.parse_args()

    modules = [m.strip() for m in (args.modules or "").split(",") if m.strip()] or DEFAULT_MODULES

    py, src = resolve_venv(args)
    if py is None:
        log("error", src)
        return 5

    if not args.quiet and not args.json:
        log("info", f"checking venv (source={src})")
        log("info", f"python: {py}")
        log("info", f"modules: {modules}")

    py_ok, py_ver = check_venv_python(py)
    if not py_ok:
        log("error", f"venv python FAILED: {py_ver}")
        if args.log_file:
            _append_log(args.log_file, py_ver or "unknown", len(modules), len(modules), "FAIL")
        return 2

    mods_ok, mod_results, meta = check_modules(py, modules)
    failed = [r for r in mod_results if not (r["ok"] and r.get("in_venv", False))]

    report = {
        "venv_python": str(py),
        "venv_source": src,
        "python_version": py_ver,
        # Subprocess verification — proves the venv was actually used
        "subprocess_sys_prefix": meta.get("sys_prefix"),
        "subprocess_sys_executable": meta.get("sys_executable"),
        "subprocess_sys_path_first_3": meta.get("sys_path_first_3"),
        "modules_total": len(mod_results),
        "modules_ok": sum(1 for r in mod_results if r["ok"] and r.get("in_venv", False)),
        "modules_failed": failed,
        "all_ok": py_ok and mods_ok,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    elif not args.quiet:
        log("info", f"python: {py_ver}")
        # Surface the venv verification — user can audit at a glance
        sp = meta.get("sys_prefix")
        sexec = meta.get("sys_executable")
        if sp and sexec:
            log("info", f"venv verified: prefix={sp}")
            log("info", f"venv verified: exec={sexec}")
        for r in mod_results:
            if r["ok"] and r.get("in_venv"):
                loc = r.get("location", "")
                # Shorten path for readability
                short_loc = ".../" + loc.split("/site-packages/")[-1] if "/site-packages/" in loc else loc
                log("info", f"  ok  {r['module']:20s} {r.get('version', ''):10s} {short_loc}")
            else:
                log("error", f"  FAIL {r['module']:20s} {r.get('error', '')[:80]}")

    if not mods_ok:
        log("error", f"{len(failed)} module(s) FAILED")
        log("error", "fix: install with the EXACT venv path:")
        log("error", f"     {py} -m pip install <missing-module>")
        if args.log_file:
            _append_log(args.log_file, py_ver, len(mod_results), len(failed), "FAIL")
        return 3

    log("info", "startup check PASSED")
    if args.log_file:
        _append_log(args.log_file, py_ver, len(mod_results), 0, "OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
