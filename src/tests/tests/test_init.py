import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from photobooth import USERDATA_PATH

logger = logging.getLogger(name=None)


def test_main_instance_create_dirs_permission_error():
    from photobooth import _create_basic_folders

    with patch.object(os, "makedirs", side_effect=RuntimeError("effect: failed creating folder")):
        # emulate write access issue and ensure an exception is received to make the app fail starting.
        with pytest.raises(RuntimeError):
            _create_basic_folders()


def test_main_instance_create_dirs_permission_errorreraised_stops_starting_app():
    with patch.object(os, "makedirs", side_effect=PermissionError("effect: failed creating folder")):
        # emulate write access issue and ensure an exception is received to make the app fail starting.
        with pytest.raises(RuntimeError):
            __import__("photobooth.__init__")


def test_init_error_if_demoassets_is_no_symlink():
    target = Path(USERDATA_PATH, "demoassets")
    target.unlink(missing_ok=True)

    target.touch()
    assert target.is_file()

    with pytest.raises(RuntimeError):
        __import__("photobooth.__init__")

    target.unlink(missing_ok=False)


def test_init_userdata_after_init_there_is_demoassets_symlink():
    target = Path(USERDATA_PATH, "demoassets")
    target.unlink(missing_ok=True)

    # starting the app creates the symlink
    __import__("photobooth.__init__")

    if os.name == "nt":
        assert target.is_junction()
    else:
        assert target.is_symlink()


def test_sanitize_event_name():
    from photobooth import sanitize_event_name

    assert sanitize_event_name("Smith-Wedding_2026") == "Smith-Wedding_2026"
    assert sanitize_event_name(" Smith Wedding ") == "Smith_Wedding"
    assert sanitize_event_name("../evil") == "___evil"
    assert sanitize_event_name("") == ""
    assert sanitize_event_name(None) == ""


def test_read_active_event_name(tmp_path, monkeypatch):
    from photobooth import _read_active_event_name

    monkeypatch.chdir(tmp_path)

    # no config file yet
    assert _read_active_event_name() == ""

    Path("config").mkdir()
    Path("config/config.json").write_text('{"common": {"event_name": "Smith Wedding"}}', encoding="utf-8")
    assert _read_active_event_name() == "Smith_Wedding"

    # broken config falls back to default location
    Path("config/config.json").write_text("{broken", encoding="utf-8")
    assert _read_active_event_name() == ""
