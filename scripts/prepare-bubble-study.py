#!/usr/bin/env python3
"""Prepare private, labelled clip pairs for human microbubble visibility evaluation.

No detector, camera connection, equipment control, or water-level inference.
"""

import argparse
import os
import shutil
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

from reefwatch.config import default_data_dir, save_json


def prepare(source, output_root, label, recorded_day, start=0, seconds=20, ffmpeg="ffmpeg"):
    source = Path(source).resolve(strict=True)
    if not source.is_file():
        raise ValueError("Choose an existing local video file.")
    root = Path(output_root).resolve()
    checkout = Path(__file__).resolve().parent.parent
    if root == checkout or checkout in root.parents:
        raise ValueError("Study footage must be outside the repository.")
    date.fromisoformat(recorded_day)
    if label not in ("normal", "natural-bubbles", "uncertain"):
        raise ValueError("Choose a study label.")
    if not 0 <= start or not 2 <= seconds <= 60:
        raise ValueError("Choose a nonnegative start and a 2–60 second sample.")
    folder = root / uuid.uuid4().hex
    folder.mkdir(parents=True, mode=0o700)
    folder.chmod(0o700)
    try:
        for name, filters in (
            ("source-detail.mp4", "fps=10,pad=ceil(iw/2)*2:ceil(ih/2)*2"),
            ("prototype.mp4", "fps=2,scale=640:360"),
        ):
            target = folder / name
            command = [
                ffmpeg,
                "-nostdin",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-ss",
                str(start),
                "-i",
                str(source),
                "-t",
                str(seconds),
                "-an",
                "-vf",
                filters,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-map_metadata",
                "-1",
                str(target),
            ]
            subprocess.run(
                command,
                check=True,
                timeout=180,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            target.chmod(0o600)
        save_json(
            folder / "review.json",
            {
                "label": label,
                "recorded_day": recorded_day,
                "start_seconds": start,
                "requested_seconds": seconds,
                "source_detail": "source-detail.mp4",
                "prototype": "prototype.mp4",
                "lighting": None,
                "return_roi": None,
                "visible_in_source": None,
                "visible_in_prototype": None,
                "confounders": [],
                "review_notes": "",
                "split": "unassigned",
                "warning": "Human visibility review only. No detection or water-level measurement.",
            },
        )
    except Exception:
        # Only remove this newly generated UUID directory, never the original footage.
        shutil.rmtree(folder)
        raise RuntimeError("Clip preparation failed. Check the local file and FFmpeg.") from None
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Local exported video, never an RTSP URL")
    parser.add_argument(
        "--label", choices=("normal", "natural-bubbles", "uncertain"), required=True
    )
    parser.add_argument("--recorded-day", required=True, help="Actual recording date, YYYY-MM-DD")
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--seconds", type=int, default=20)
    parser.add_argument("--output-root", type=Path, default=default_data_dir() / "bubble-study")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        folder = prepare(
            args.source, args.output_root, args.label, args.recorded_day, args.start, args.seconds
        )
    except (OSError, ValueError, RuntimeError):
        print(
            "Unable to prepare clips. Check the local source, date, duration, and private output directory.",
            file=sys.stderr,
        )
        return 1
    print(f"Private review clips saved to: {folder}")
    print("Review both clips and complete review.json. No detector has been evaluated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
