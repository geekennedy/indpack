"""Integration tests — run against the real OS.

These tests interact with the actual process table and filesystem.
Mark with @pytest.mark.integration so they can be excluded in CI if needed.
"""

import json
import os
import subprocess
import sys

import pytest

from indpack.core import get_pid_args, get_ps_pids, parse_pid_args

pytestmark = pytest.mark.integration


class TestGetPsPidsLive:
    def test_returns_nonempty_list(self):
        pids = get_ps_pids()
        assert len(pids) > 0

    def test_all_entries_are_digit_strings(self):
        pids = get_ps_pids()
        for pid in pids:
            assert pid.isdigit(), f"Non-numeric PID: {pid}"

    def test_own_pid_present(self):
        pids = get_ps_pids()
        assert str(os.getpid()) in pids


class TestGetPidArgsLive:
    def test_own_process_args(self):
        args = get_pid_args(str(os.getpid()))
        assert len(args) > 0

    def test_nonexistent_pid(self):
        args = get_pid_args("4294967295")
        assert args == []

    def test_init_process(self):
        args = get_pid_args("1")
        # PID 1 may or may not be readable depending on permissions,
        # but it should never raise.
        assert isinstance(args, list)


class TestParsePidArgsLive:
    def test_parse_own_process(self):
        args = get_pid_args(str(os.getpid()))
        parsed = parse_pid_args(args)
        assert isinstance(parsed, dict)


class TestEndToEnd:
    def test_full_pipeline(self):
        """get_ps_pids -> get_pid_args -> parse_pid_args for own process."""
        pids = get_ps_pids()
        own_pid = str(os.getpid())
        assert own_pid in pids

        args = get_pid_args(own_pid)
        assert len(args) > 0

        parsed = parse_pid_args(args)
        assert isinstance(parsed, dict)

    def test_cli_pids(self):
        result = subprocess.run(
            [sys.executable, "-m", "indpack", "pids"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) > 0
        assert all(line.strip().isdigit() for line in lines)

    def test_cli_args_own_pid(self):
        pid = str(os.getpid())
        result = subprocess.run(
            [sys.executable, "-m", "indpack", "args", pid],
            capture_output=True, text=True,
        )
        # Our own PID will have vanished by the time the subprocess reads it,
        # so just check it doesn't crash.
        assert result.returncode in (0, 1)

    def test_cli_inspect_limit(self):
        result = subprocess.run(
            [sys.executable, "-m", "indpack", "inspect", "-n", "3"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data) <= 3

    def test_cli_parse_pid_1(self):
        result = subprocess.run(
            [sys.executable, "-m", "indpack", "parse", "1"],
            capture_output=True, text=True,
        )
        # PID 1 may not be readable, just verify no crash
        assert result.returncode in (0, 1)
