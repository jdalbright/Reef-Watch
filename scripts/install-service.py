#!/usr/bin/env python3
"""Install/uninstall a login LaunchAgent. Run with the project's virtualenv Python."""

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

LABEL = "local.reefwatch.monitor"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("The login service installer is for macOS only.")
    target = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    domain = f"gui/{os.getuid()}"
    if args.uninstall:
        subprocess.run(
            ["launchctl", "bootout", f"{domain}/{LABEL}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        target.unlink(missing_ok=True)
        print("Login service removed. Recordings and settings have been kept.")
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("Install FFmpeg before installing the service: brew install ffmpeg")
    if sys.prefix == sys.base_prefix:
        parser.error("Use .venv/bin/python scripts/install-service.py")
    root = Path(__file__).resolve().parent.parent
    target.parent.mkdir(parents=True, exist_ok=True)
    support = Path.home() / "Library/Application Support/Reef Watch"
    support.mkdir(parents=True, exist_ok=True, mode=0o700)
    # caffeinate prevents idle system sleep while running; the display may sleep.
    config = {
        "Label": LABEL,
        "ProgramArguments": [
            "/usr/bin/caffeinate",
            "-i",
            sys.executable,
            "-m",
            "reefwatch",
            "--data-dir",
            str(support),
        ],
        "WorkingDirectory": str(root),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 15,
        "Umask": 0o077,
        "EnvironmentVariables": {"PATH": f"{Path(ffmpeg).parent}:/usr/bin:/bin:/usr/sbin:/sbin"},
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": "/dev/null",
    }
    subprocess.run(
        ["launchctl", "bootout", f"{domain}/{LABEL}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    target.write_bytes(plistlib.dumps(config))
    target.chmod(0o600)
    subprocess.run(["launchctl", "bootstrap", domain, str(target)], check=True)
    print("Reef Watch starts at login. Open http://127.0.0.1:8765")
    print("A Mac restart requires login before this LaunchAgent starts.")


if __name__ == "__main__":
    main()
