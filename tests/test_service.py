"""Unit tests for Navigator service module (systemd integration)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from navigator.service import (
    generate_unit_file,
    get_service_path,
    install_service,
    service_control,
    uninstall_service,
)


class TestGenerateUnitFile:
    """Tests for generate_unit_file()."""

    @patch("navigator.service.shutil.which", return_value="/usr/local/bin/navigator")
    def test_generate_unit_file_content(self, mock_which):
        """Unit file contains correct systemd directives with resolved binary path."""
        content = generate_unit_file()
        assert "ExecStart=/usr/local/bin/navigator daemon" in content
        assert "Restart=on-failure" in content
        assert "RestartSec=5" in content
        assert "WantedBy=default.target" in content
        assert "Type=simple" in content

    @patch("navigator.service.shutil.which", return_value=None)
    def test_generate_unit_file_not_found(self, mock_which):
        """Raises FileNotFoundError when navigator binary is not on PATH."""
        with pytest.raises(FileNotFoundError, match="navigator binary not found"):
            generate_unit_file()


class TestGetServicePath:
    """Tests for get_service_path()."""

    def test_get_service_path(self):
        """Returns path ending with .config/systemd/user/navigator.service."""
        path = get_service_path()
        assert str(path).endswith(".config/systemd/user/navigator.service")


class TestInstallService:
    """Tests for install_service()."""

    @patch("navigator.service.subprocess.run")
    @patch("navigator.service.shutil.which", return_value="/usr/bin/navigator")
    def test_install_service(self, mock_which, mock_run, tmp_path, monkeypatch):
        """install_service writes unit file and runs systemctl + loginctl."""
        service_file = tmp_path / "navigator.service"
        monkeypatch.setattr("navigator.service.get_service_path", lambda: service_file)

        result = install_service()

        assert result == service_file
        assert service_file.exists()
        content = service_file.read_text()
        assert "ExecStart=/usr/bin/navigator daemon" in content

        calls = mock_run.call_args_list
        assert call(["systemctl", "--user", "daemon-reload"], check=True) in calls
        assert call(
            ["systemctl", "--user", "enable", "navigator.service"], check=True
        ) in calls
        assert call(["loginctl", "enable-linger"], check=False) in calls

    @patch("navigator.service.subprocess.run")
    @patch("navigator.service.shutil.which", return_value="/usr/bin/navigator")
    def test_install_service_no_linger(self, mock_which, mock_run, tmp_path, monkeypatch):
        """install_service with enable_linger=False skips loginctl call."""
        service_file = tmp_path / "navigator.service"
        monkeypatch.setattr("navigator.service.get_service_path", lambda: service_file)

        install_service(enable_linger=False)

        calls = mock_run.call_args_list
        for c in calls:
            assert "loginctl" not in str(c)


class TestUninstallService:
    """Tests for uninstall_service()."""

    @patch("navigator.service.subprocess.run")
    def test_uninstall_service(self, mock_run, tmp_path, monkeypatch):
        """uninstall_service removes existing unit file and returns True."""
        service_file = tmp_path / "navigator.service"
        service_file.write_text("[Unit]\nDescription=test\n")
        monkeypatch.setattr("navigator.service.get_service_path", lambda: service_file)

        result = uninstall_service()

        assert result is True
        assert not service_file.exists()

        calls = mock_run.call_args_list
        assert call(
            ["systemctl", "--user", "stop", "navigator.service"], check=False
        ) in calls
        assert call(
            ["systemctl", "--user", "disable", "navigator.service"], check=False
        ) in calls
        assert call(["systemctl", "--user", "daemon-reload"], check=True) in calls

    @patch("navigator.service.subprocess.run")
    def test_uninstall_service_not_installed(self, mock_run, tmp_path, monkeypatch):
        """uninstall_service returns False when unit file doesn't exist."""
        service_file = tmp_path / "nonexistent.service"
        monkeypatch.setattr("navigator.service.get_service_path", lambda: service_file)

        result = uninstall_service()

        assert result is False


class TestServiceControl:
    """Tests for service_control()."""

    @patch("navigator.service.subprocess.run")
    def test_service_control_valid_actions(self, mock_run):
        """service_control calls systemctl --user with valid actions."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        for action in ("status", "start", "stop", "restart"):
            mock_run.reset_mock()
            result = service_control(action)

            mock_run.assert_called_once_with(
                ["systemctl", "--user", action, "navigator.service"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

    def test_service_control_invalid_action(self):
        """service_control raises ValueError for invalid actions."""
        with pytest.raises(ValueError, match="Invalid action"):
            service_control("invalid")
