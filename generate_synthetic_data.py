"""
Generate synthetic hyperscanning sourcedata.
3 dyads × 10 tasks — mirrors the real SCAALE pilot structure.
"""

import numpy as np
import struct
from pathlib import Path

BASE = Path(__file__).parent / "sourcedata"

DYADS = [
    {"id": "dyad-001", "group": "non-autism", "mother": "sub-001", "child": "sub-002"},
    {"id": "dyad-002", "group": "autism",     "mother": "sub-003", "child": "sub-004"},
    {"id": "dyad-003", "group": "non-autism", "mother": "sub-005", "child": "sub-006"},
]

TASKS = [
    ("task-01restEyesOpen",    60),
    ("task-02restEyesClosed",  60),
    ("task-03imitation",      120),
    ("task-04verbal",         120),
    ("task-05restEyesOpen",    60),
    ("task-06restEyesClosed",  60),
    ("task-07verbal",         120),
    ("task-08imitation",      120),
    ("task-09restEyesOpen",    60),
    ("task-10restEyesClosed",  60),
]

N_CHANNELS = 128
SFREQ      = 500


def write_xdf(path: Path, dyad: dict) -> None:
    """Write a minimal valid XDF file with 3 LSL streams."""

    def chunk(tag, content):
        n = len(content)
        lb = struct.pack("<BB", 1, n) if n <= 0xFF else struct.pack("<BH", 2, n) if n <= 0xFFFF else struct.pack("<BI", 4, n)
        return struct.pack("<H", tag) + lb + content

    def stream_header(sid, name, stype, n_ch, sfreq):
        xml = (f'<?xml version="1.0"?><info><name>{name}</name><type>{stype}</type>'
               f'<channel_count>{n_ch}</channel_count><nominal_srate>{sfreq}</nominal_srate>'
               f'<channel_format>float32</channel_format>'
               f'<source_id>{name}_{dyad["id"]}</source_id></info>').encode()
        return struct.pack("<I", sid) + xml

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"XDF:")
        f.write(chunk(2, stream_header(1, "EGINetAmp_51", "EEG", N_CHANNELS, SFREQ)))
        f.write(chunk(2, stream_header(2, "EGINetAmp_52", "EEG", N_CHANNELS, SFREQ)))
        f.write(chunk(2, stream_header(3, "SCAALE_Triggers", "Markers", 1, 0)))

        # Minimal EEG samples (10 per stream)
        rng = np.random.default_rng(42)
        n_mini = 10
        for sid in (1, 2):
            samples = rng.standard_normal((n_mini, N_CHANNELS)).astype(np.float32)
            ts = np.linspace(0, n_mini / SFREQ, n_mini, dtype=np.float64)
            raw = b"".join(struct.pack("<d", ts[i]) + samples[i].tobytes() for i in range(n_mini))
            f.write(chunk(3, struct.pack("<I", sid) + raw))

        # Trigger events (task onsets)
        onset, trig = 0.0, b""
        for name, dur in TASKS:
            trig += struct.pack("<d", onset)
            m = name.encode() + b"\x00"
            trig += struct.pack("<I", len(m)) + m
            onset += dur
        f.write(chunk(3, struct.pack("<I", 3) + trig))

        # Stream footers
        total = sum(d for _, d in TASKS)
        for sid in (1, 2, 3):
            footer = (f'<?xml version="1.0"?><info>'
                      f'<first_timestamp>0</first_timestamp>'
                      f'<last_timestamp>{total}</last_timestamp>'
                      f'<sample_count>{n_mini}</sample_count></info>').encode()
            f.write(chunk(6, struct.pack("<I", sid) + footer))


def write_ios(path: Path, sub: str) -> None:
    """Write synthetic IOS ratings TSV — one row per task."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(int(sub.replace("sub-", "")))
    lines = ["session_id\tparticipant_code\tmeasurement_index\tvalue\tlabel"]
    for i, (task_name, _) in enumerate(TASKS, 1):
        lines.append(f"ses-01\t{sub}\t{i}\t{rng.integers(1, 8)}\t{task_name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_videos(dyad_path: Path, dyad_id: str) -> None:
    """Write minimal MP4 placeholder files (valid ftyp box)."""
    video_dir = dyad_path / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    mp4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isomavc1"
    for cam in ("cam-mother", "cam-child", "cam-dyad"):
        (video_dir / f"{cam}_{dyad_id}.mp4").write_bytes(mp4)


def main():
    for dyad in DYADS:
        dyad_path = BASE / dyad["id"]
        print(f"Generating {dyad['id']}...")
        write_xdf(dyad_path / "EEG" / f"{dyad['id']}_eeg.xdf", dyad)
        for sub in (dyad["mother"], dyad["child"]):
            write_ios(dyad_path / "IOS" / f"ios_{sub}.tsv", sub)
        write_videos(dyad_path, dyad["id"])
        print(f"  ✓ XDF + IOS + 3 videos")
    print("\nSourcedata generated!")


if __name__ == "__main__":
    main()
