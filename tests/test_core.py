"""Unit tests for indpack.core — parse_pid_args and platform-specific helpers."""

from unittest.mock import mock_open, patch

import pytest

from indpack.core import parse_pid_args


# ---------------------------------------------------------------------------
# parse_pid_args
# ---------------------------------------------------------------------------

class TestParsePidArgs:
    def test_empty_args(self):
        assert parse_pid_args([]) == {}

    def test_long_option_with_equals(self):
        result = parse_pid_args(["--output=/tmp/out"])
        assert result == {"output": "/tmp/out"}

    def test_long_option_with_space(self):
        result = parse_pid_args(["--config", "/etc/app.conf"])
        assert result == {"config": "/etc/app.conf"}

    def test_long_flag_no_value(self):
        result = parse_pid_args(["--verbose"])
        assert result == {"verbose": True}

    def test_short_option_with_value(self):
        result = parse_pid_args(["-o", "/tmp/out"])
        assert result == {"o": "/tmp/out"}

    def test_short_flag_no_value(self):
        result = parse_pid_args(["-v"])
        assert result == {"v": True}

    def test_combined_short_flags(self):
        result = parse_pid_args(["-abc"])
        assert result == {"a": True, "b": True, "c": True}

    def test_short_option_with_equals(self):
        result = parse_pid_args(["-o=/tmp/out"])
        assert result == {"o": "/tmp/out"}

    def test_positional_args(self):
        result = parse_pid_args(["file1.txt", "file2.txt"])
        assert result == {"_positional": ["file1.txt", "file2.txt"]}

    def test_double_dash_separator(self):
        result = parse_pid_args(["--verbose", "--", "--not-a-flag", "file"])
        assert result == {
            "verbose": True,
            "_positional": ["--not-a-flag", "file"],
        }

    def test_mixed_args(self):
        result = parse_pid_args([
            "/usr/bin/app", "--config", "/etc/app.conf",
            "-v", "--port=8080", "-abc", "positional",
        ])
        assert result == {
            "_positional": ["/usr/bin/app", "positional"],
            "config": "/etc/app.conf",
            "v": True,
            "port": "8080",
            "a": True,
            "b": True,
            "c": True,
        }

    def test_long_flag_followed_by_another_flag(self):
        result = parse_pid_args(["--debug", "--verbose"])
        assert result == {"debug": True, "verbose": True}

    def test_short_flag_followed_by_another_flag(self):
        result = parse_pid_args(["-d", "-v"])
        assert result == {"d": True, "v": True}

    def test_equals_with_empty_value(self):
        result = parse_pid_args(["--key="])
        assert result == {"key": ""}

    def test_single_positional(self):
        result = parse_pid_args(["/usr/bin/python3"])
        assert result == {"_positional": ["/usr/bin/python3"]}

    def test_only_double_dash(self):
        result = parse_pid_args(["--"])
        assert result == {}

    def test_double_dash_with_trailing(self):
        result = parse_pid_args(["--", "-v", "--flag"])
        assert result == {"_positional": ["-v", "--flag"]}


# ---------------------------------------------------------------------------
# Linux procfs helpers (mocked)
# ---------------------------------------------------------------------------

class TestLinuxProcfs:
    @patch("indpack.core.os.listdir", return_value=["1", "42", "1337", "self", "net"])
    def test_get_pids_procfs(self, mock_listdir):
        from indpack.core import _get_pids_procfs

        pids = _get_pids_procfs()
        assert pids == ["1", "42", "1337"]
        mock_listdir.assert_called_once_with("/proc")

    @patch(
        "builtins.open",
        mock_open(read_data="/usr/bin/python3\x00-m\x00http.server\x00"),
    )
    def test_get_args_procfs(self):
        from indpack.core import _get_args_procfs

        args = _get_args_procfs("42")
        assert args == ["/usr/bin/python3", "-m", "http.server"]

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_get_args_procfs_missing(self, _mock):
        from indpack.core import _get_args_procfs

        assert _get_args_procfs("99999") == []

    @patch("builtins.open", side_effect=PermissionError)
    def test_get_args_procfs_permission_denied(self, _mock):
        from indpack.core import _get_args_procfs

        assert _get_args_procfs("1") == []

    @patch("builtins.open", mock_open(read_data=""))
    def test_get_args_procfs_empty_cmdline(self):
        from indpack.core import _get_args_procfs

        assert _get_args_procfs("2") == []


# ---------------------------------------------------------------------------
# macOS ps helpers (mocked)
# ---------------------------------------------------------------------------

class TestDarwinPs:
    @patch("indpack.core.subprocess.check_output", return_value="  1\n  42\n  1337\n")
    def test_get_pids_ps(self, mock_co):
        from indpack.core import _get_pids_ps

        pids = _get_pids_ps()
        assert pids == ["1", "42", "1337"]

    @patch(
        "indpack.core.subprocess.check_output",
        return_value="/usr/bin/python3 -m http.server\n",
    )
    def test_get_args_ps(self, _mock):
        from indpack.core import _get_args_ps

        args = _get_args_ps("42")
        assert args == ["/usr/bin/python3", "-m", "http.server"]

    @patch(
        "indpack.core.subprocess.check_output",
        side_effect=__import__("subprocess").CalledProcessError(1, "ps"),
    )
    def test_get_args_ps_missing(self, _mock):
        from indpack.core import _get_args_ps

        assert _get_args_ps("99999") == []


# ---------------------------------------------------------------------------
# Unsupported platform
# ---------------------------------------------------------------------------

class TestUnsupportedPlatform:
    @patch("indpack.core.platform.system", return_value="FreeBSD")
    def test_get_ps_pids_unsupported(self, _mock):
        from indpack.core import get_ps_pids

        with pytest.raises(OSError, match="Unsupported platform"):
            get_ps_pids()

    @patch("indpack.core.platform.system", return_value="FreeBSD")
    def test_get_pid_args_unsupported(self, _mock):
        from indpack.core import get_pid_args

        with pytest.raises(OSError, match="Unsupported platform"):
            get_pid_args("1")
