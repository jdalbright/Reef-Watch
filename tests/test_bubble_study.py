import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts/prepare-bubble-study.py"
spec = importlib.util.spec_from_file_location("bubble_study", MODULE_PATH)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_rejects_repository_output_and_invalid_label(tmp_path):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="outside"):
        study.prepare(source, MODULE_PATH.parent / "footage", "normal", "2026-09-27")
    with pytest.raises(ValueError, match="label"):
        study.prepare(source, tmp_path / "study", "low-water", "2026-09-27")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg required")
def test_real_encoding_of_synthetic_study_pair(tmp_path):
    source = tmp_path / "synthetic.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=960x540:rate=10",
            "-t",
            "2",
            str(source),
        ],
        check=True,
    )
    output = study.prepare(source, tmp_path / "private-study", "uncertain", "2026-09-27", seconds=2)
    manifest = json.loads((output / "review.json").read_text())
    assert manifest["visible_in_source"] is None
    assert manifest["split"] == "unassigned"
    assert (output.stat().st_mode & 0o777) == 0o700
    for file, shape in (("source-detail.mp4", (960, 540)), ("prototype.mp4", (640, 360))):
        assert ((output / file).stat().st_mode & 0o777) == 0o600
        data = json.loads(
            subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(output / file)]
            )
        )
        stream = data["streams"][0]
        assert (stream["width"], stream["height"]) == shape
        assert stream["codec_type"] == "video"
    assert source.exists()
