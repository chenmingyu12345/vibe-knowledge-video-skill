"""Inspect videos, make contact sheets, extract audio, check exports."""
import argparse
from fractions import Fraction
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys

def tool(name, root):
    if root:
        package = Path(root) / ("ffmpeg-static" if name == "ffmpeg" else "ffprobe-static")
        binary = name + ".exe" if sys.platform == "win32" else name
        machine = platform.machine().lower()
        arch = "arm64" if machine in ("arm64", "aarch64") else "x64" if machine in ("amd64", "x86_64") else "ia32"
        system = "win32" if sys.platform == "win32" else "darwin" if sys.platform == "darwin" else "linux"
        for p in [package / binary, package / "bin" / system / arch / binary]:
            if p.is_file():
                return str(p.resolve())
    found = shutil.which(name)
    if found:
        return found
    raise ValueError(f"Missing {name}; add to PATH or use --tools-dir node_modules")

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tools-dir")
    subs = p.add_subparsers(dest="command", required=True)
    for name in ("probe", "contact", "audio", "check"):
        s = subs.add_parser(name)
        s.add_argument("input", type=Path)
        if name in ("contact", "audio"):
            s.add_argument("--output", type=Path, required=True)
            s.add_argument("--overwrite", action="store_true")
        if name == "check":
            for key in ("width", "height", "fps", "duration"):
                s.add_argument("--" + key, type=float, required=True)
            s.add_argument("--require-audio", action="store_true")
    a = p.parse_args()
    if not a.input.is_file():
        raise ValueError("Input does not exist")
    data = json.loads(run([tool("ffprobe", a.tools_dir), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(a.input.resolve())]).stdout)
    if a.command == "probe":
        print(json.dumps(data, ensure_ascii=False, indent=2)); return
    vs = [s for s in data["streams"] if s["codec_type"] == "video"]
    aus = [s for s in data["streams"] if s["codec_type"] == "audio"]
    duration = float(data["format"]["duration"])
    if a.command == "check":
        if a.fps <= 0:
            raise ValueError("fps must be positive")
        errors = []
        if not vs:
            errors.append("No video")
        else:
            v = vs[0]
            if (v["width"], v["height"]) != (a.width, a.height): errors.append("Resolution mismatch")
            if abs(float(Fraction(v["avg_frame_rate"])) - a.fps) > .01: errors.append("FPS mismatch")
            if v["codec_name"] != "h264": errors.append("Expected H.264")
        if abs(duration - a.duration) > max(.1, 2/a.fps): errors.append("Duration mismatch")
        if a.require_audio and not aus: errors.append("No audio")
        if aus and aus[0]["codec_name"] != "aac": errors.append("Expected AAC")
        print(json.dumps({"passed": not errors, "duration": duration, "errors": errors}))
        sys.exit(bool(errors))
    if a.output.resolve() == a.input.resolve(): raise ValueError("Output equals input")
    if a.output.exists() and not a.overwrite: raise ValueError("Output exists; use --overwrite")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [tool("ffmpeg", a.tools_dir), "-hide_banner", "-loglevel", "error", "-y" if a.overwrite else "-n", "-i", str(a.input.resolve())]
    if a.command == "audio":
        if not aus: raise ValueError("No audio to extract")
        cmd += ["-map", "0:a:0", "-vn", "-c:a", "pcm_s16le", "-f", "wav"]
    else:
        if not vs or duration <= 0: raise ValueError("No valid video")
        cmd += ["-vf", f"fps={12/duration:.12f},scale=480:-2,tile=4x3", "-frames:v", "1", "-update", "1"]
    run(cmd + [str(a.output.resolve())])
    if not a.output.is_file() or a.output.stat().st_size == 0: raise ValueError("Empty output")
    print(str(a.output.resolve()))

if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        print(str(e), file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError): print(e.stderr, file=sys.stderr)
        sys.exit(1)
