"""Unit tests for the CLI interface."""

import json
from unittest.mock import patch

from indpack.cli import main


class TestCliPids:
    @patch("indpack.cli.get_ps_pids", return_value=["10", "1", "100"])
    def test_pids_sorted_output(self, _mock, capsys):
        rc = main(["pids"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out.splitlines() == ["1", "10", "100"]


class TestCliArgs:
    @patch("indpack.cli.get_pid_args", return_value=["/bin/sh", "-c", "echo hi"])
    def test_args_output(self, _mock, capsys):
        rc = main(["args", "42"])
        assert rc == 0
        lines = capsys.readouterr().out.splitlines()
        assert lines == ["/bin/sh", "-c", "echo hi"]

    @patch("indpack.cli.get_pid_args", return_value=[])
    def test_args_empty(self, _mock, capsys):
        rc = main(["args", "99999"])
        assert rc == 1
        assert "No arguments" in capsys.readouterr().err


class TestCliParse:
    @patch(
        "indpack.cli.get_pid_args",
        return_value=["/bin/app", "--verbose", "--port", "8080"],
    )
    def test_parse_output(self, _mock, capsys):
        rc = main(["parse", "42"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["verbose"] is True
        assert data["port"] == "8080"

    @patch("indpack.cli.get_pid_args", return_value=[])
    def test_parse_empty(self, _mock, capsys):
        rc = main(["parse", "99999"])
        assert rc == 1


class TestCliInspect:
    @patch("indpack.cli.get_pid_args", return_value=["/bin/sh"])
    @patch("indpack.cli.get_ps_pids", return_value=["5", "3", "1"])
    def test_inspect_all(self, _mock_pids, _mock_args, capsys):
        rc = main(["inspect"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "1" in data
        assert "3" in data
        assert "5" in data

    @patch("indpack.cli.get_pid_args", return_value=["/bin/sh"])
    @patch("indpack.cli.get_ps_pids", return_value=["5", "3", "1"])
    def test_inspect_limit(self, _mock_pids, _mock_args, capsys):
        rc = main(["inspect", "-n", "2"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert len(data) == 2


class TestCliNoCommand:
    def test_no_command_shows_help(self, capsys):
        rc = main([])
        assert rc == 1
        assert "usage" in capsys.readouterr().out.lower()
