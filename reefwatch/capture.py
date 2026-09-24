import asyncio
import shutil

import numpy as np

WIDTH, HEIGHT, FPS = 640, 360, 2


def camera_command(url: str, ffmpeg="ffmpeg"):
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-rtsp_transport",
        "tcp",
        "-timeout",
        "10000000",
        "-i",
        url,
        "-an",
        "-vf",
        f"fps={FPS},scale={WIDTH}:{HEIGHT}",
        "-pix_fmt",
        "rgb24",
        "-f",
        "rawvideo",
        "pipe:1",
    ]


async def stop_process(process):
    if process and process.returncode is None:
        try:
            process.terminate()
        except ProcessLookupError:
            return
        try:
            await asyncio.wait_for(process.wait(), 3)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()


class Camera:
    """One decoder. A wall-clock watchdog also covers hangs outside RTSP socket I/O."""

    def __init__(self, url, ffmpeg="ffmpeg"):
        self.url = url
        self.ffmpeg = ffmpeg

    async def frames(self):
        process = None
        try:
            if not shutil.which(self.ffmpeg):
                raise RuntimeError("FFmpeg is not installed")
            # Never log argv, exception text or decoder stderr: they may contain credentials.
            process = await asyncio.create_subprocess_exec(
                *camera_command(self.url, self.ffmpeg),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                limit=WIDTH * HEIGHT * 3 * 2,
            )
            while True:
                raw = await asyncio.wait_for(process.stdout.readexactly(WIDTH * HEIGHT * 3), 12)
                yield np.frombuffer(raw, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)
        finally:
            await stop_process(process)


class DemoCamera:
    """Clearly labelled synthetic test pattern, never simulated animal observations."""

    async def frames(self):
        n = 0
        rng = np.random.default_rng(11)
        while True:
            frame = np.full((HEIGHT, WIDTH, 3), (22, 63, 79), dtype=np.uint8)
            frame[18:100] = rng.integers(25, 125, (82, WIDTH, 3), dtype=np.uint8)
            x = (n * 7) % (WIDTH - 80)
            frame[180:240, x : x + 80] = (67, 177, 152)
            n += 1
            yield frame
            await asyncio.sleep(1 / FPS)


async def encode_clip(jpegs, destination, ffmpeg="ffmpeg"):
    """Encode the preceding <=15 s of sampled frames, without audio, into an MP4."""
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "image2pipe",
            "-framerate",
            str(FPS),
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(destination),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(process.communicate(b"".join(jpegs)), 20)
        if process.returncode != 0:
            raise RuntimeError("Clip encoding failed")
    finally:
        await stop_process(process)
