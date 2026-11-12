#!/usr/bin/env python3
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import validation

REPO = Path(os.environ["LOCAL_PROJECT_DIR"]).resolve()
RESULTS = Path(os.environ["LOCAL_RESULTS_DIR"]).resolve()
POLL_SECONDS = int(os.environ.get("LOCAL_AGENT_POLL_SECONDS", "5"))
STATE_DIR = Path.home() / ".local/state/chatgpt-mamba2-local-agent"
STATE_FILE = STATE_DIR / "last-command-id"
MAX_RESULT_CHARS = 100_000

VALIDATION_ACTIONS = frozenset(validation.ACTION_HANDLERS)


def run(cmd, cwd=REPO, check=True):
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=check,
    )


def record(proc):
    return {
        "command": list(proc.args),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def fetch_control():
    run([
        "git",
        "fetch",
        "origin",
        "local-control:refs/remotes/origin/local-control",
    ])


def fetch_remote_branch(branch):
    branch = str(branch or "").strip()
    if not branch:
        raise RuntimeError("branch is required")
    return run([
        "git",
        "fetch",
        "origin",
        f"{branch}:refs/remotes/origin/{branch}",
    ], check=False)


def read_command():
    proc = run([
        "git", "show",
        "origin/local-control:.local-control/command.json",
    ])
    return json.loads(proc.stdout)


def _clean_status():
    proc = run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        check=False,
    )
    return proc, proc.returncode == 0 and not proc.stdout.strip()


def git_status():
    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    status_proc, clean = _clean_status()
    divergence = None
    if branch:
        fetch_remote_branch(branch)
        remote = run(
            ["git", "rev-parse", "--verify", f"refs/remotes/origin/{branch}"],
            check=False,
        )
        if remote.returncode == 0:
            div = run(
                ["git", "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"],
                check=False,
            )
            if div.returncode == 0:
                divergence = div.stdout.strip()
    return {
        "hostname": socket.gethostname(),
        "repo": str(REPO),
        "branch": branch,
        "head": head,
        "clean": clean,
        "changed_paths": status_proc.stdout.splitlines()[:50],
        "divergence": divergence,
        "time": datetime.now(timezone.utc).isoformat(),
    }


def sync_result(ok, branch, before, after, commands, reason=None):
    return {
        "ok": ok,
        "action": "sync",
        "data": {
            "branch": branch,
            "before_sha": before,
            "after_sha": after,
            "reason": reason,
            "commands": commands,
        },
    }


def git_sync(fetch=True):
    commands = []

    before_proc = run(["git", "rev-parse", "HEAD"], check=False)
    commands.append(record(before_proc))
    before = before_proc.stdout.strip()
    if before_proc.returncode != 0:
        return sync_result(False, "", before, before, commands, "cannot resolve HEAD")

    if fetch:
        proc = run(["git", "fetch", "origin"], check=False)
        commands.append(record(proc))
        if proc.returncode != 0:
            return sync_result(False, "", before, before, commands, "git fetch origin failed")

    status_proc, clean = _clean_status()
    commands.append(record(status_proc))
    if not clean:
        return sync_result(False, "", before, before, commands, "refusing dirty worktree")

    branch_proc = run(["git", "branch", "--show-current"], check=False)
    commands.append(record(branch_proc))
    branch = branch_proc.stdout.strip()
    if branch_proc.returncode != 0 or not branch:
        return sync_result(False, branch, before, before, commands, "refusing detached HEAD")

    branch_fetch = fetch_remote_branch(branch)
    commands.append(record(branch_fetch))
    if branch_fetch.returncode != 0:
        return sync_result(False, branch, before, before, commands, "failed to refresh current remote branch")

    remote_ref = f"refs/remotes/origin/{branch}"
    remote_proc = run(["git", "rev-parse", "--verify", remote_ref], check=False)
    commands.append(record(remote_proc))
    if remote_proc.returncode != 0:
        return sync_result(False, branch, before, before, commands, f"origin/{branch} missing")

    div_proc = run(
        ["git", "rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"],
        check=False,
    )
    commands.append(record(div_proc))
    if div_proc.returncode != 0:
        return sync_result(False, branch, before, before, commands, "cannot determine divergence")
    try:
        local_only, remote_only = map(int, div_proc.stdout.split())
    except ValueError:
        return sync_result(False, branch, before, before, commands, "invalid divergence output")

    if local_only and remote_only:
        return sync_result(
            False, branch, before, before, commands,
            f"refusing diverged branch ({local_only} local-only, {remote_only} remote-only)",
        )

    if not remote_only:
        return sync_result(True, branch, before, before, commands)

    status2, clean2 = _clean_status()
    commands.append(record(status2))
    if not clean2:
        return sync_result(False, branch, before, before, commands, "worktree changed during sync validation")

    pull = run(["git", "pull", "--ff-only", "origin", branch], check=False)
    commands.append(record(pull))
    after_proc = run(["git", "rev-parse", "HEAD"], check=False)
    commands.append(record(after_proc))
    after = after_proc.stdout.strip() or before

    if pull.returncode != 0:
        return sync_result(False, branch, before, after, commands, "ff-only pull failed")
    return sync_result(True, branch, before, after, commands)


def switch_result(ok, target, before_branch, after_branch, before, after, commands, reason=None):
    return {
        "ok": ok,
        "action": "switch_branch",
        "data": {
            "target_branch": target,
            "before_branch": before_branch,
            "after_branch": after_branch,
            "before_sha": before,
            "after_sha": after,
            "reason": reason,
            "commands": commands,
        },
    }


def git_switch_branch(target, fetch=True):
    commands = []
    target = str(target or "").strip()

    branch_proc = run(["git", "branch", "--show-current"], check=False)
    head_proc = run(["git", "rev-parse", "HEAD"], check=False)
    commands.extend([record(branch_proc), record(head_proc)])
    before_branch = branch_proc.stdout.strip()
    before = head_proc.stdout.strip()

    if not before_branch:
        return switch_result(False, target, before_branch, before_branch, before, before, commands, "refusing detached HEAD")
    if not target:
        return switch_result(False, target, before_branch, before_branch, before, before, commands, "target branch is required")

    check_ref = run(["git", "check-ref-format", "--branch", target], check=False)
    commands.append(record(check_ref))
    if check_ref.returncode != 0:
        return switch_result(False, target, before_branch, before_branch, before, before, commands, "invalid branch name")

    status_proc, clean = _clean_status()
    commands.append(record(status_proc))
    if not clean:
        return switch_result(False, target, before_branch, before_branch, before, before, commands, "refusing dirty worktree")

    if fetch:
        fetch_proc = fetch_remote_branch(target)
        commands.append(record(fetch_proc))
        if fetch_proc.returncode != 0:
            return switch_result(False, target, before_branch, before_branch, before, before, commands, "failed to refresh target remote branch")

    remote_ref = f"refs/remotes/origin/{target}"
    remote_proc = run(["git", "rev-parse", "--verify", remote_ref], check=False)
    commands.append(record(remote_proc))
    if remote_proc.returncode != 0:
        return switch_result(False, target, before_branch, before_branch, before, before, commands, f"origin/{target} missing")

    if target == before_branch:
        payload = git_sync(fetch=False)
        data = payload.get("data", {})
        return switch_result(
            payload.get("ok", False),
            target,
            before_branch,
            before_branch,
            before,
            data.get("after_sha", before),
            commands + data.get("commands", []),
            data.get("reason"),
        )

    local_ref = f"refs/heads/{target}"
    local_proc = run(["git", "rev-parse", "--verify", local_ref], check=False)
    commands.append(record(local_proc))

    if local_proc.returncode == 0:
        div = run(
            ["git", "rev-list", "--left-right", "--count", f"{local_ref}...{remote_ref}"],
            check=False,
        )
        commands.append(record(div))
        if div.returncode != 0:
            return switch_result(False, target, before_branch, before_branch, before, before, commands, "cannot inspect target divergence")
        try:
            local_only, remote_only = map(int, div.stdout.split())
        except ValueError:
            return switch_result(False, target, before_branch, before_branch, before, before, commands, "invalid target divergence output")
        if local_only:
            return switch_result(
                False, target, before_branch, before_branch, before, before, commands,
                f"target has {local_only} local-only commit(s)",
            )

        switch = run(["git", "switch", target], check=False)
        commands.append(record(switch))
        if switch.returncode != 0:
            return switch_result(False, target, before_branch, before_branch, before, before, commands, "git switch failed")
        if remote_only:
            pull = run(["git", "pull", "--ff-only", "origin", target], check=False)
            commands.append(record(pull))
            if pull.returncode != 0:
                return switch_result(False, target, before_branch, target, before, before, commands, "target ff-only pull failed")
    else:
        switch = run(["git", "switch", "--track", "-c", target, f"origin/{target}"], check=False)
        commands.append(record(switch))
        if switch.returncode != 0:
            return switch_result(False, target, before_branch, before_branch, before, before, commands, "tracking branch creation failed")

    after_branch_proc = run(["git", "branch", "--show-current"], check=False)
    after_head_proc = run(["git", "rev-parse", "HEAD"], check=False)
    final_status, final_clean = _clean_status()
    commands.extend([record(after_branch_proc), record(after_head_proc), record(final_status)])
    after_branch = after_branch_proc.stdout.strip()
    after = after_head_proc.stdout.strip()

    if after_branch != target or not final_clean:
        return switch_result(False, target, before_branch, after_branch, before, after, commands, "unexpected final branch/worktree state")

    return switch_result(True, target, before_branch, after_branch, before, after, commands)



def audit_m028_record():
    """Read only the existence and non-sensitive metadata of the October paper record."""
    record_path = Path.home() / ".local/share/mamba2-forward-paper/2026-10-decision.json"
    data = {
        "record_exists": record_path.is_file(),
        "record_directory_exists": record_path.parent.is_dir(),
        "read_only": True,
        "broker_initialized": False,
        "order_api_called": False,
        "strategy_economics_computed": False,
    }
    if not record_path.is_file():
        return {"ok": True, "action": "m028_record_audit", "data": data}
    raw = record_path.read_bytes()
    data["record_sha256"] = hashlib.sha256(raw).hexdigest()
    data["record_bytes"] = len(raw)
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        data["parse_error"] = type(exc).__name__
        return {"ok": False, "action": "m028_record_audit", "data": data}
    if not isinstance(record, dict):
        data["parse_error"] = "record_not_object"
        return {"ok": False, "action": "m028_record_audit", "data": data}
    plan = record.get("plan") or {}
    costs = plan.get("cost_evidence") or {}
    data.update({
        "decision_id": record.get("decision_id"),
        "scheduled_decision_utc": record.get("scheduled_decision_utc"),
        "created_at_utc": record.get("created_at_utc"),
        "feature_sha": record.get("feature_sha"),
        "plan_status": plan.get("status"),
        "source_gate_pass": record.get("source_gate_pass"),
        "holding_period_return_exists": record.get("holding_period_return") is not None,
        "net_pnl_exists": costs.get("net_pnl") is not None,
    })
    return {"ok": True, "action": "m028_record_audit", "data": data}



def diagnose_mt5_wine_compat():
    """Read-only Wine/MT5 compatibility triage; no Wine terminal launch."""
    import re
    from datetime import datetime, timezone

    info = {
        "read_only": True,
        "mt5_started": False,
        "mt5_initialized": False,
        "order_api_called": False,
        "wine_prefix_modified": False,
    }
    try:
        proc = subprocess.run(
            ["wine", "--version"],
            check=False, text=True, capture_output=True, timeout=8,
        )
        info["wine_version"] = (proc.stdout.strip() or proc.stderr.strip())[:128]
        info["wine_version_exit"] = proc.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        info["wine_version_error"] = type(exc).__name__

    # Only inspect explicit standard prefixes, never enumerate private files.
    candidates = [
        Path.home() / ".mt5",
        Path.home() / ".wine",
        Path.home() / ".mt5-wine",
    ]
    seen = set()
    prefixes = []
    for prefix in candidates:
        if prefix in seen or not prefix.is_dir():
            continue
        seen.add(prefix)
        item = {"prefix_label": prefix.name}
        for rel in (
            "drive_c/Program Files/MetaTrader 5/terminal64.exe",
            "drive_c/Program Files (x86)/MetaTrader 5/terminal64.exe",
        ):
            exe = prefix / rel
            if exe.is_file():
                stat = exe.stat()
                item["terminal_exe_exists"] = True
                item["terminal_exe_size_bytes"] = stat.st_size
                item["terminal_exe_mtime_utc"] = datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat()
                break
        reg = prefix / "system.reg"
        if reg.is_file() and reg.stat().st_size < 25_000_000:
            # Only return a Windows product label, never registry contents.
            try:
                src = reg.read_text(encoding="utf-8", errors="replace")
                section = re.search(
                    r'(?m)^\[Software\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\].*?\n(?=\[|\Z)',
                    src,
                    re.S,
                )
                if section:
                    product = re.search(r'^"ProductName"="([^"\r\n]{1,100})"', section.group(), re.M)
                    if product:
                        item["windows_product_name"] = product.group(1)
            except (OSError, UnicodeError):
                pass
        prefixes.append(item)
    info["prefixes"] = prefixes

    # Read kernel process names and TracerPid only. No command lines,
    # environment, credentials, trading accounts or terminal logs.
    processes = []
    root = Path("/proc")
    for entry in root.iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            comm = (entry / "comm").read_text().strip()
            if comm.lower() not in {
                "terminal64.exe", "metatrader64.exe", "wineserver", "winedbg",
                "gdb", "strace", "lldb",
            }:
                continue
            lines = (entry / "status").read_text().splitlines()
            tracer = next(
                (line.split(":", 1)[1].strip() for line in lines
                 if line.startswith("TracerPid:")),
                "unknown",
            )
            processes.append({"process": comm, "tracer_pid": tracer})
        except (OSError, UnicodeError):
            continue
    info["processes"] = processes[:35]
    return {"ok": True, "action": "diagnose_mt5_wine_compat", "data": info}



def probe_mt5_pe_version():
    """Read only the MT5 executable's embedded Windows file version."""
    import mmap
    import struct

    root = Path.home() / ".mt5" / "drive_c" / "Program Files" / "MetaTrader 5"
    exe = root / "terminal64.exe"
    if not exe.is_file():
        return {"ok": False, "action": "probe_mt5_pe_version",
                "data": {"reason": "exe_not_present"}}
    versions = []
    with exe.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as buf:
            pattern = b"\xbd\x04\xef\xfe"  # VS_FIXEDFILEINFO signature
            pos = buf.find(pattern)
            checks = 0
            while pos >= 0 and checks < 300:
                checks += 1
                if pos + 16 < len(buf):
                    fixed_ver, hi, lo = struct.unpack_from("<III", buf, pos + 4)
                    major, minor = hi >> 16, hi & 0xFFFF
                    build, patch = lo >> 16, lo & 0xFFFF
                    if (fixed_ver in (0x00010000, 0x00010001)
                            and major == 5 and minor <= 2
                            and 1000 <= build < 30000):
                        versions.append(f"{major}.{minor}.{build}.{patch}")
                        break
                pos = buf.find(pattern, pos + 4)
    return {"ok": True, "action": "probe_mt5_pe_version",
            "data": {"read_only": True, "exe_version": versions[0] if versions else None,
                     "version_present": bool(versions),
                     "terminal_launched": False, "order_api_called": False}}


def m029_stage3b_isolated_preflight():
    """Bounded, read-only inventory of isolated Wine 11 and Python candidates.

    Never initializes Wine/MT5, executes a Python interpreter, reads account
    data, copies files, or modifies an existing prefix.
    """
    import re

    home = Path.home()
    original = (home / ".mt5").resolve()
    forbidden = {
        original,
        (home / ".wine").resolve(),
        (home / ".mamba2-mt5").resolve(),
    }
    result = {
        "read_only": True,
        "wine_started": False,
        "terminal_started": False,
        "python_started": False,
        "broker_initialized": False,
        "account_data_read": False,
        "real_order_api_called": False,
        "prefix_modified": False,
    }

    binaries = [
        Path("/opt/wine-staging/bin/wine"),
        Path("/opt/wine-staging/bin/wine64"),
        Path("/opt/wine-devel/bin/wine"),
        Path("/opt/wine-stable/bin/wine"),
        Path("/usr/bin/wine-staging"),
        Path("/usr/local/bin/wine-staging"),
        Path("/usr/bin/wine"),
    ]
    try:
        opt = Path("/opt")
        for folder in opt.iterdir():
            if len(binaries) >= 32:
                break
            if not folder.is_dir():
                continue
            if any(word in folder.name.lower() for word in ("wine", "staging")):
                binaries.append(folder / "bin" / "wine")
    except OSError:
        pass

    found = []
    for binary in dict.fromkeys(binaries):
        if not binary.is_file():
            continue
        try:
            proc = subprocess.run(
                [str(binary), "--version"], capture_output=True, text=True,
                check=False, timeout=7,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        version = (proc.stdout.strip() or proc.stderr.strip())[:90]
        if proc.returncode == 0:
            found.append({"binary": str(binary), "version": version})
    result["wine_candidates"] = found

    paths = []
    roots = [home, Path("/tmp"), home / "Dev", home / ".local" / "share"]
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for item in root.iterdir():
                if len(paths) >= 150:
                    break
                lower = item.name.lower()
                if not any(
                    token in lower
                    for token in ("wine", "mt5", "mamba", "compat", "isolat")
                ):
                    continue
                try:
                    if item.is_symlink() or not item.is_dir():
                        continue
                    resolved = item.resolve()
                    if resolved in forbidden:
                        continue
                    if not (resolved / "system.reg").is_file():
                        continue
                    paths.append(resolved)
                except OSError:
                    continue
        except OSError:
            continue
    # A hidden prefix may be under the project root from the smoke test.
    paths = list(dict.fromkeys(paths))
    prefixes = []
    py_rels = (
        "drive_c/Python310/python.exe",
        "drive_c/Python310/pythonw.exe",
        "drive_c/Python311/python.exe",
        "drive_c/Python312/python.exe",
        "drive_c/Program Files/Python310/python.exe",
    )
    for prefix in paths[:30]:
        python_paths = []
        for rel in py_rels:
            exe = prefix / rel
            if exe.is_file() and not exe.is_symlink():
                python_paths.append(str(exe))
        regfile = prefix / "system.reg"
        product_name = None
        try:
            if regfile.stat().st_size < 30_000_000:
                registry = regfile.read_text(
                    encoding="utf-8", errors="replace"
                )
                section = re.search(
                    r'(?ms)^\[Software\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\].*?(?=^\[|\Z)',
                    registry,
                )
                if section:
                    match = re.search(
                        r'^"ProductName"="([^"\r\n]{1,100})"',
                        section.group(), re.M,
                    )
                    if match:
                        product_name = match.group(1)
        except OSError:
            pass
        prefixes.append({
            "prefix": str(prefix),
            "windows_product_name": product_name,
            "bridge_python_candidates": python_paths,
            "terminal_copy_present": any(
                (prefix / rel).is_file()
                for rel in (
                    "drive_c/Program Files/MetaTrader 5/terminal64.exe",
                    "drive_c/Program Files (x86)/MetaTrader 5/terminal64.exe",
                )
            ),
        })
    result["isolated_prefix_candidates"] = prefixes
    result["isolated_python_available"] = any(
        bool(p["bridge_python_candidates"]) for p in prefixes
    )
    return {
        "ok": True,
        "action": "m029_stage3b_isolated_preflight",
        "data": result,
    }



def m029_stage3b_targeted_discovery():
    """Bounded metadata-only search for Wine 11 test artifacts.

    No shell, home-wide search, Wine prefix execution or account reads.
    Only known temporary/installer-related roots and shallow package metadata.
    """
    import os

    home = Path.home()
    roots = [
        Path("/tmp"), Path("/var/tmp"), Path("/opt"),
        home / "Downloads", home / "Dev",
        home / ".local", home / ".cache",
    ]
    ignore = {
        (home / ".mt5").resolve(),
        (home / ".wine").resolve(),
        (home / ".mamba2-mt5").resolve(),
    }
    visited = 0
    max_dirs = 3000
    found_wine = []
    found_prefixes = []
    found_python = []
    for root in roots:
        if not root.is_dir():
            continue
        stack = [(root, 0)]
        while stack and visited < max_dirs:
            folder, depth = stack.pop()
            visited += 1
            try:
                if folder.is_symlink() or folder.resolve() in ignore:
                    continue
                with os.scandir(folder) as scanner:
                    entries = list(scanner)
            except (OSError, PermissionError):
                continue
            if (folder / "system.reg").is_file() and folder.resolve() not in ignore:
                found_prefixes.append(str(folder.resolve()))
            if depth > 6:
                continue
            for item in entries:
                try:
                    if item.is_symlink():
                        continue
                    if item.is_file(follow_symlinks=False):
                        name = item.name.lower()
                        if name == "wine" and (
                            "/bin/" in item.path or "/usr/" in item.path
                        ):
                            if os.access(item.path, os.X_OK):
                                found_wine.append(item.path)
                        if name == "python.exe" and (
                            "python310" in item.path.lower()
                            or "python311" in item.path.lower()
                        ):
                            found_python.append(item.path)
                        continue
                    if not item.is_dir(follow_symlinks=False):
                        continue
                    if depth >= 2 and not any(
                        key in str(item.path).lower()
                        for key in (
                            "wine", "staging", "mt5", "mamba2", "python",
                            "compat", "isolate", "scratch", "test",
                            "debian", "ubuntu", "work", "tmp",
                        )
                    ):
                        continue
                    if depth <= 5:
                        stack.append((Path(item.path), depth + 1))
                except (OSError, PermissionError):
                    continue

    package_info = []
    try:
        proc = subprocess.run(
            ["dpkg-query", "-W", "winehq-staging", "wine-staging",
             "wine-staging-amd64", "winehq-devel", "wine-devel"],
            capture_output=True, text=True, check=False, timeout=8,
        )
        package_info = [
            line[:160] for line in proc.stdout.splitlines()
            if "wine" in line.lower()
        ][:20]
    except (OSError, subprocess.TimeoutExpired):
        pass
    wine_versions = []
    for path in list(dict.fromkeys(found_wine))[:20]:
        try:
            proc = subprocess.run(
                [path, "--version"], capture_output=True, text=True,
                check=False, timeout=7,
            )
            if proc.returncode == 0:
                wine_versions.append({
                    "path": path,
                    "version": proc.stdout.strip()[:80],
                })
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {
        "ok": True,
        "action": "m029_stage3b_targeted_discovery",
        "data": {
            "read_only": True,
            "search_bounded": True,
            "directories_examined": visited,
            "wine_binaries": wine_versions,
            "isolated_prefix_paths": list(dict.fromkeys(found_prefixes))[:20],
            "python_exe_paths": list(dict.fromkeys(found_python))[:20],
            "wine_package_metadata": package_info,
            "terminal_launched": False,
            "mt5_imported": False,
            "broker_initialized": False,
            "account_data_read": False,
            "order_api_called": False,
        },
    }



def m029_branch_divergence_report():
    """Read-only summary of diverged M029 HEAD, without file content."""
    branch = run(["git", "branch", "--show-current"], check=False).stdout.strip()
    if branch != "prospective-paper-recovery":
        return {
            "ok": False, "action": "m029_branch_divergence_report",
            "data": {"reason": "WRONG_BRANCH", "branch": branch},
        }
    commands = {}
    specs = {
        "heads": ["git", "rev-parse", "HEAD", "origin/prospective-paper-recovery"],
        "counts": ["git", "rev-list", "--left-right", "--count",
                   "HEAD...origin/prospective-paper-recovery"],
        "commits": ["git", "log", "--left-right", "--format=%h%x09%s",
                    "--max-count=16",
                    "HEAD...origin/prospective-paper-recovery"],
        "changes": ["git", "diff", "--name-status",
                    "HEAD...origin/prospective-paper-recovery"],
        "clean": ["git", "status", "--porcelain", "--untracked-files=all"],
    }
    for name, cmd in specs.items():
        proc = run(cmd, check=False)
        commands[name] = {
            "ok": proc.returncode == 0,
            "lines": proc.stdout.splitlines()[:35],
        }
    return {
        "ok": all(v["ok"] for v in commands.values()),
        "action": "m029_branch_divergence_report",
        "data": {
            "read_only": True,
            "branch": branch,
            "checks": commands,
            "git_mutation": False,
            "strategy_computed": False,
        },
    }



def m029_stage3b_known_runtime_probe():
    """Read-only inspection of the exact isolated paths provided by operator."""
    root = Path("/home/joel/.local/share/mamba2-mt5-wine1121")
    wine = root / "runtime/opt/wine-staging/bin/wine"
    prefix = root / "prefix"
    terminal = root / "app/terminal64.exe"
    original = (Path.home() / ".mt5").resolve()

    if root.is_symlink() or prefix.is_symlink() or wine.is_symlink():
        return {"ok": False, "action": "m029_stage3b_known_runtime_probe",
                "data": {"reason": "ISOLATED_PATH_SYMLINK"}}
    if prefix.resolve() == original or prefix.resolve() == (Path.home()/".wine").resolve():
        return {"ok": False, "action": "m029_stage3b_known_runtime_probe",
                "data": {"reason": "SHARED_PREFIX_REFUSED"}}
    if not (wine.is_file() and prefix.is_dir() and terminal.is_file()):
        return {"ok": False, "action": "m029_stage3b_known_runtime_probe",
                "data": {
                    "reason": "REQUIRED_ISOLATED_PATH_MISSING",
                    "wine_exists": wine.is_file(),
                    "prefix_exists": prefix.is_dir(),
                    "terminal_exists": terminal.is_file(),
                }}
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)
    env["WINEDEBUG"] = "-all"
    try:
        check = subprocess.run(
            [str(wine), "--version"], text=True, capture_output=True,
            env=env, check=False, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "action": "m029_stage3b_known_runtime_probe",
                "data": {"reason": "WINE_VERSION_PROBE_FAILED",
                         "error_class": type(exc).__name__}}
    if check.returncode != 0 or "11.21" not in check.stdout:
        return {"ok": False, "action": "m029_stage3b_known_runtime_probe",
                "data": {"reason": "WINE_VERSION_MISMATCH",
                         "reported_wine_version": check.stdout.strip()[:80]}}

    candidates = [
        "drive_c/Python310/python.exe",
        "drive_c/Python311/python.exe",
        "drive_c/Python312/python.exe",
        "drive_c/Program Files/Python310/python.exe",
        "drive_c/users/joel/AppData/Local/Programs/Python/Python310/python.exe",
        "drive_c/users/joel/AppData/Local/Programs/Python/Python311/python.exe",
        "drive_c/Program Files (x86)/Python310/python.exe",
    ]
    # Top-level Python executables only, no user directory inspection.
    py = []
    for rel in candidates:
        p = prefix / rel
        if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root.resolve()):
            py.append(str(p))
    reg = prefix/"system.reg"
    version_11 = None
    if reg.is_file() and reg.stat().st_size < 25000000:
        try:
            import re
            content = reg.read_text(encoding="utf-8", errors="replace")
            match = re.search(r'(?m)^"ProductName"="([^"\r\n]{1,120})"', content)
            if match:
                version_11 = match.group(1)
        except OSError:
            pass
    return {
        "ok": True, "action": "m029_stage3b_known_runtime_probe",
        "data": {
            "wine_version": check.stdout.strip()[:100],
            "wine_binary": str(wine),
            "wine_prefix": str(prefix),
            "isolated_terminal_present": True,
            "prefix_windows_product": version_11,
            "python_candidates": py,
            "isolated_bridge_python_present": bool(py),
            "wine_terminal_started": False,
            "python_import_attempted": False,
            "mt5_initialized": False,
            "account_data_read": False,
            "broker_quote_read": False,
            "order_api_called": False,
            "prefix_modified_by_probe": False,
        },
    }


def execute(command):
    action = command.get("action")
    if action == "status":
        return {"ok": True, "action": action, "data": git_status()}
    if action == "m028_record_audit":
        return audit_m028_record()
    if action == "diagnose_mt5_wine_compat":
        return diagnose_mt5_wine_compat()
    if action == "probe_mt5_pe_version":
        return probe_mt5_pe_version()
    if action == "m029_stage3b_isolated_preflight":
        return m029_stage3b_isolated_preflight()
    if action == "m029_stage3b_targeted_discovery":
        return m029_stage3b_targeted_discovery()
    if action == "m029_branch_divergence_report":
        return m029_branch_divergence_report()
    if action == "m029_stage3b_known_runtime_probe":
        return m029_stage3b_known_runtime_probe()
    if action == "sync":
        return git_sync()
    if action == "switch_branch":
        return git_switch_branch((command.get("args") or {}).get("branch"))
    if action == "m028_stage3_first_decision":
        # The October paper decision was prospective, not retroactive.
        # Reusing an existing immutable record is safe; creating one after
        # the scheduled UTC calendar day would violate the frozen protocol.
        October_decision_day = datetime(2026, 10, 7, tzinfo=timezone.utc).date()
        existing_record = (
            Path.home() / ".local/share/mamba2-forward-paper/2026-10-decision.json"
        )
        if (
            not existing_record.is_file()
            and datetime.now(timezone.utc).date() > October_decision_day
        ):
            return {
                "ok": False,
                "action": action,
                "data": {
                    "ok": False,
                    "reason": "MISSED_OCTOBER_DECISION_NO_BACKFILL",
                    "scheduled_decision_utc": "2026-10-07T12:00:00Z",
                    "record_exists": False,
                    "strategy_economics_computed": False,
                    "broker_initialized": False,
                    "real_order_api_called": False,
                },
            }
    if action in VALIDATION_ACTIONS:
        data = validation.execute(action)
        return {"ok": bool(data.get("ok")), "action": action, "data": data}
    raise ValueError(f"unsupported action: {action!r}")


def _bound(value):
    if isinstance(value, (bytes, bytearray, memoryview)):
        value = bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, str):
        if len(value) <= MAX_RESULT_CHARS:
            return value
        return "[publisher truncated output]\n" + value[-MAX_RESULT_CHARS:]
    if isinstance(value, (list, tuple)):
        return [_bound(item) for item in value]
    if isinstance(value, dict):
        return {key: _bound(item) for key, item in value.items()}
    return value


def publish_result(command, payload):
    run([
        "git",
        "fetch",
        "origin",
        "local-control-results:refs/remotes/origin/local-control-results",
    ], cwd=RESULTS)
    run(["git", "reset", "--hard", "origin/local-control-results"], cwd=RESULTS)

    out_dir = RESULTS / ".local-control"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "version": 1,
        "command_id": command.get("id"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        **_bound(payload),
    }
    (out_dir / "result.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    run(["git", "add", ".local-control/result.json"], cwd=RESULTS)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=RESULTS, check=False)
    if staged.returncode == 0:
        return

    run([
        "git", "-c", "user.name=ChatGPT Mamba2 Local Agent",
        "-c", "user.email=mamba2-local-agent@localhost",
        "commit", "-m", f"local-agent: result {command.get('id', 'unknown')}"
    ], cwd=RESULTS)
    run(["git", "push", "origin", "HEAD:local-control-results"], cwd=RESULTS)


def load_last_id():
    try:
        return STATE_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def save_last_id(command_id):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(command_id + "\n", encoding="utf-8")


def process_current_command_once(force=False):
    fetch_control()
    sync_payload = git_sync(fetch=False)
    sync_data = sync_payload.get("data", {})
    if sync_payload.get("ok") and sync_data.get("before_sha") != sync_data.get("after_sha"):
        print(
            f"auto-sync {sync_data.get('branch')}: "
            f"{sync_data.get('before_sha','')[:12]} -> "
            f"{sync_data.get('after_sha','')[:12]}",
            flush=True,
        )
    elif not sync_payload.get("ok"):
        print(
            f"auto-sync refused: {sync_data.get('reason')}",
            file=sys.stderr,
            flush=True,
        )

    command = read_command()
    command_id = str(command.get("id", "")).strip()
    if not command_id:
        raise RuntimeError("current command has no id")
    if command_id == load_last_id() and not force:
        print(f"already processed {command_id}", flush=True)
        return 0

    try:
        payload = execute(command)
    except Exception as exc:
        payload = {
            "ok": False,
            "action": command.get("action"),
            "error": f"{type(exc).__name__}: {exc}",
        }

    publish_result(command, payload)
    save_last_id(command_id)
    print(
        f"processed once {command_id}: {payload.get('ok')}",
        flush=True,
    )
    # A validation/business result may legitimately be ok=false while the
    # worker itself completed successfully and published deterministic
    # evidence. Keep systemd healthy; reserve non-zero exit for worker/runtime
    # failures that prevent command processing/publication.
    return 0


def main():
    print(f"mamba2-local-agent starting repo={REPO} poll={POLL_SECONDS}s", flush=True)
    previous_sync = None
    while True:
        try:
            fetch_control()
            sync_payload = git_sync(fetch=False)
            sync_signature = json.dumps({
                "ok": sync_payload.get("ok"),
                "data": sync_payload.get("data", {}).get("reason"),
                "after": sync_payload.get("data", {}).get("after_sha"),
            }, sort_keys=True)
            if sync_signature != previous_sync:
                data = sync_payload.get("data", {})
                if sync_payload.get("ok") and data.get("before_sha") != data.get("after_sha"):
                    print(
                        f"auto-sync {data.get('branch')}: "
                        f"{data.get('before_sha','')[:12]} -> {data.get('after_sha','')[:12]}",
                        flush=True,
                    )
                elif not sync_payload.get("ok"):
                    print(
                        f"auto-sync refused: {data.get('reason')}",
                        file=sys.stderr,
                        flush=True,
                    )
                previous_sync = sync_signature

            command = read_command()
            command_id = str(command.get("id", "")).strip()
            if command_id and command_id != load_last_id():
                try:
                    payload = execute(command)
                except Exception as exc:
                    payload = {
                        "ok": False,
                        "action": command.get("action"),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                publish_result(command, payload)
                save_last_id(command_id)
                print(f"processed {command_id}: {payload.get('ok')}", flush=True)
        except Exception as exc:
            print(
                f"agent loop error: {type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    if "--force-once" in sys.argv:
        raise SystemExit(process_current_command_once(force=True))
    if "--once" in sys.argv:
        raise SystemExit(process_current_command_once())
    main()
