"""Core process introspection functions."""

import os
import platform
import shlex
import subprocess
import sys


def get_ps_pids() -> list[str]:
    """Return PIDs of all running processes as strings."""
    system = platform.system()

    if system == "Linux":
        return _get_pids_procfs()
    if system == "Darwin":
        return _get_pids_ps()
    if system == "Windows":
        return _get_pids_wmic()

    raise OSError(f"Unsupported platform: {system}")


def get_pid_args(pid) -> list[str]:
    """Return command line arguments for the given PID.

    Args:
        pid: Process ID as a string.

    Returns:
        List of command line argument strings. Empty list if
        the process cannot be read (permissions, vanished, etc).
    """
    system = platform.system()

    if system == "Linux":
        return _get_args_procfs(pid)
    if system == "Darwin":
        return _get_args_ps(pid)
    if system == "Windows":
        return _get_args_wmic(pid)

    raise OSError(f"Unsupported platform: {system}")


def parse_pid_args(args: list[str]) -> dict[str, object]:
    """Parse a command line argument list into a key-value mapping.

    Handles common argument styles:
        --key=value        -> {"key": "value"}
        --key value        -> {"key": "value"}
        -k value           -> {"k": "value"}
        --flag (no value)  -> {"flag": True}
        -f (no value)      -> {"f": True}
        positional args    -> {"_positional": ["arg1", ...]}
        -abc (short flags) -> {"a": True, "b": True, "c": True}

    Args:
        args: List of argument strings (typically from get_pid_args).

    Returns:
        Dictionary mapping argument names to their values.
    """
    result: dict[str, object] = {}
    positional: list[str] = []
    i = 0

    while i < len(args):
        arg = args[i]

        if arg == "--":
            positional.extend(args[i + 1 :])
            break

        if arg.startswith("--"):
            if "=" in arg:
                key, value = arg[2:].split("=", 1)
                result[key] = value
            elif i + 1 < len(args) and not args[i + 1].startswith("-"):
                result[arg[2:]] = args[i + 1]
                i += 1
            else:
                result[arg[2:]] = True

        elif arg.startswith("-") and len(arg) > 1:
            flag = arg[1:]
            if len(flag) == 1:
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    result[flag] = args[i + 1]
                    i += 1
                else:
                    result[flag] = True
            elif "=" in flag:
                key, value = flag.split("=", 1)
                result[key] = value
            else:
                for char in flag:
                    result[char] = True

        else:
            positional.append(arg)

        i += 1

    if positional:
        result["_positional"] = positional

    return result


# -- Linux (procfs) ----------------------------------------------------------

def _get_pids_procfs() -> list[str]:
    return [
        entry for entry in os.listdir("/proc")
        if entry.isdigit()
    ]


def _get_args_procfs(pid: str) -> list[str]:
    try:
        cmdline = _read_text(f"/proc/{pid}/cmdline")
        if not cmdline:
            return []
        return cmdline.rstrip("\x00").split("\x00")
    except (FileNotFoundError, PermissionError):
        return []


# -- macOS (ps) --------------------------------------------------------------

def _get_pids_ps() -> list[str]:
    output = subprocess.check_output(
        ["ps", "-axo", "pid="], text=True,
    )
    return [line.strip() for line in output.splitlines() if line.strip()]


def _get_args_ps(pid: str) -> list[str]:
    try:
        output = subprocess.check_output(
            ["ps", "-p", pid, "-o", "args="], text=True,
        ).strip()
        if not output:
            return []
        return shlex.split(output)
    except (subprocess.CalledProcessError, ValueError):
        return []


# -- Windows (wmic) ----------------------------------------------------------

def _get_pids_wmic() -> list[str]:
    output = subprocess.check_output(
        [
            sys.executable, "-c",
            "import json,subprocess;"
            "r=subprocess.check_output("
            "['wmic','process','get','processid'],text=True);"
            "print(json.dumps([l.strip() for l in r.splitlines() if l.strip().isdigit()]))",
        ],
        text=True,
    )
    import json

    return json.loads(output)


def _get_args_wmic(pid: str) -> list[str]:
    try:
        output = subprocess.check_output(
            [
                sys.executable, "-c",
                "import json,subprocess,sys;"
                f"r=subprocess.check_output("
                f"['wmic','process','where',"
                f"'processid={pid}','get','commandline'],text=True);"
                "lines=[l.strip() for l in r.splitlines() if l.strip()];"
                "print(json.dumps(lines[1:] if len(lines)>1 else []))",
            ],
            text=True,
        )
        import json

        parts = json.loads(output)
        if not parts:
            return []
        return shlex.split(parts[0])
    except (subprocess.CalledProcessError, ValueError):
        return []


def _read_text(path: str) -> str:
    with open(path) as f:
        return f.read()
