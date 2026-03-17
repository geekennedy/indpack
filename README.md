# indpack

Cross-platform process introspection library for Python. Enumerates running processes, extracts their command line arguments, and parses those arguments into structured key-value mappings.

Supports Linux (procfs), macOS (ps), and Windows (wmic).

## Install

```bash
uv pip install .
```

Or for development:

```bash
uv sync
```

## Library usage

```python
from indpack import get_ps_pids, get_pid_args, parse_pid_args

# List all PIDs
pids = get_ps_pids()

# Get command line args for a specific PID
args = get_pid_args(pids[0])

# Parse args into a dict
parsed = parse_pid_args(args)
# {"config": "/etc/app.conf", "verbose": True, "_positional": ["/usr/bin/app"]}
```

### `get_ps_pids() -> list[str]`

Returns PIDs of all running processes as strings. Uses `/proc` on Linux, `ps` on macOS, and `wmic` on Windows.

### `get_pid_args(pid: str) -> list[str]`

Returns the command line arguments for a given PID. Returns an empty list if the process is inaccessible (permissions, already exited, etc).

### `parse_pid_args(args: list[str]) -> dict[str, object]`

Parses a list of command line arguments into a dictionary:

| Input style | Result |
|---|---|
| `--key=value` | `{"key": "value"}` |
| `--key value` | `{"key": "value"}` |
| `-k value` | `{"k": "value"}` |
| `--flag` | `{"flag": True}` |
| `-abc` | `{"a": True, "b": True, "c": True}` |
| `positional` | `{"_positional": ["positional"]}` |
| `-- --raw` | `{"_positional": ["--raw"]}` |

## CLI

```bash
# List all PIDs
indpack pids

# Show args for a PID
indpack args 1234

# Parse args into JSON
indpack parse 1234

# Full inspection (all processes or limited)
indpack inspect
indpack inspect -n 10
```

## Testing

```bash
# All tests
uv run pytest -v

# Unit tests only
uv run pytest -v -m "not integration"

# Integration tests only
uv run pytest -v -m integration
```

## Project structure

```
src/indpack/
    __init__.py    # Public API exports
    __main__.py    # python -m indpack support
    core.py        # get_ps_pids, get_pid_args, parse_pid_args
    cli.py         # argparse CLI
tests/
    test_core.py         # Unit tests (mocked platform calls)
    test_cli.py          # Unit tests (mocked library calls)
    test_integration.py  # Live process table tests
```
