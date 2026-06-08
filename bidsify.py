"""
Bidsify: sourcedata/ → rawdata/

Converts synthetic hyperscanning sourcedata to BIDS format.
Demonstrates our proposal: dyad_id column in participants.tsv.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

REPO   = Path(__file__).parent
SOURCE = REPO / "sourcedata"
BIDS   = REPO / "rawdata"

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

SFREQ      = 500
N_CHANNELS = 128
PADDING    = 2.0  # seconds pre/post task


def write_bids_root() -> None:
    BIDS.mkdir(exist_ok=True)

    # dataset_description.json
    (BIDS / "dataset_description.json").write_text(json.dumps({
        "Name": "Synthetic Hyperscanning EEG Dataset",
        "BIDSVersion": "1.10.0",
        "DatasetType": "raw",
        "Authors": ["Anne Monnier", "Guillaume Dumas"],
        "License": "CC0",
        "ReferencesAndLinks": [
            "https://github.com/bids-standard/bids-specification/issues/402"
        ]
    }, indent=2), encoding="utf-8")

    # ── participants.tsv — OUR PROPOSAL ───────────────────────────────────
    rows = []
    for dyad in DYADS:
        for role, sub in [("mother", dyad["mother"]), ("child", dyad["child"])]:
            group = "autistic" if dyad["group"] == "autism" and role == "child" else "non-autistic"
            rows.append({"participant_id": sub, "role": role,
                         "group": group, "dyad_id": dyad["id"]})
    pd.DataFrame(rows).to_csv(BIDS / "participants.tsv", sep="\t", index=False)

    # participants.json
    (BIDS / "participants.json").write_text(json.dumps({
        "role":    {"Description": "Role in the dyad",
                    "Levels": {"mother": "Mother", "child": "Child"}},
        "group":   {"Description": "Diagnostic group",
                    "Levels": {"autistic": "Autistic", "non-autistic": "Non-autistic"}},
        "dyad_id": {"Description": (
            "Dyad identifier linking participants recorded simultaneously. "
            "Proposed BIDS extension for hyperscanning. "
            "See https://github.com/bids-standard/bids-specification/issues/402"
        )}
    }, indent=2), encoding="utf-8")

    # Shared task sidecar JSONs (BIDS inheritance)
    for task_name, duration in TASKS:
        (BIDS / f"{task_name}_eeg.json").write_text(json.dumps({
            "TaskName": task_name,
            "SamplingFrequency": SFREQ,
            "EEGReference": "CMS",
            "PowerLineFrequency": 60,
            "RecordingDuration": duration + 2 * PADDING,
            "EEGChannelCount": N_CHANNELS,
            "ECGChannelCount": 1,
        }, indent=2), encoding="utf-8")

    # events.json schema
    (BIDS / "events.json").write_text(json.dumps({
        "onset":      {"Description": "Task onset in seconds (includes 2s padding)"},
        "duration":   {"Description": "Task duration in seconds"},
        "trial_type": {"Description": "Task label"},
        "IOS_rating": {
            "Description": (
                "Inclusion of the Other in the Self (Aron et al. 1992). "
                "Post-task subjective rating 1-7. "
                "Stored as custom column in events.tsv — our proposed convention."
            ),
            "Units": "Likert 1-7"
        }
    }, indent=2), encoding="utf-8")

    print("BIDS root files written.")


def bidsify_participant(sub: str, dyad: dict) -> None:
    eeg_dir = BIDS / sub / "ses-01" / "eeg"
    eeg_dir.mkdir(parents=True, exist_ok=True)

    # Load IOS ratings
    ios = pd.read_csv(SOURCE / dyad["id"] / "IOS" / f"ios_{sub}.tsv", sep="\t")
    ios_map = dict(zip(ios["label"], ios["value"]))

    scans = []
    onset = PADDING

    for task_name, duration in TASKS:
        base = f"{sub}_ses-01_{task_name}"

        # events.tsv — with IOS_rating (our proposal)
        pd.DataFrame([{
            "onset": onset,
            "duration": duration,
            "trial_type": task_name,
            "IOS_rating": ios_map.get(task_name, "n/a"),
        }]).to_csv(eeg_dir / f"{base}_events.tsv", sep="\t", index=False)

        # channels.tsv
        ch = [{"name": f"EEG{i:03d}", "type": "EEG", "units": "uV",
               "sampling_frequency": SFREQ, "status": "good"}
              for i in range(1, N_CHANNELS + 1)]
        ch.append({"name": "ECG", "type": "ECG", "units": "mV",
                   "sampling_frequency": SFREQ, "status": "good"})
        pd.DataFrame(ch).to_csv(eeg_dir / f"{base}_channels.tsv", sep="\t", index=False)

        # BrainVision triplet
        rec_dur = duration + 2 * PADDING
        n_samples = int(SFREQ * rec_dur)

        (eeg_dir / f"{base}_eeg.vhdr").write_text(
            f"BrainVision Data Exchange Header File Version 1.0\n"
            f"[Common Infos]\nDataFile={base}_eeg.eeg\n"
            f"MarkerFile={base}_eeg.vmrk\n"
            f"DataFormat=BINARY\nDataOrientation=MULTIPLEXED\n"
            f"NumberOfChannels={N_CHANNELS + 1}\n"
            f"SamplingInterval={int(1e6/SFREQ)}\n",
            encoding="utf-8"
        )
        (eeg_dir / f"{base}_eeg.vmrk").write_text(
            "BrainVision Data Exchange Marker File Version 1.0\n"
            f"Mk1=New Segment,,1,1,0\n"
            f"Mk2=Stimulus,{task_name},1,1,0\n",
            encoding="utf-8"
        )
        # Synthetic EEG: minimal placeholder (10 samples only — real data generated by script)
        rng = np.random.default_rng(int(sub.replace("sub-", "")) + hash(task_name) % 1000)
        signal = (rng.standard_normal((N_CHANNELS + 1, 10)) * 10).astype(np.int16)
        (eeg_dir / f"{base}_eeg.eeg").write_bytes(signal.tobytes())

        # Run-level sidecar override
        (eeg_dir / f"{base}_eeg.json").write_text(
            json.dumps({"RecordingDuration": rec_dur}, indent=2), encoding="utf-8"
        )

        scans.append({"filename": f"eeg/{base}_eeg.vhdr", "dyad_id": dyad["id"]})
        onset += duration + 2 * PADDING

    # scans.tsv
    pd.DataFrame(scans).to_csv(
        BIDS / sub / "ses-01" / f"{sub}_ses-01_scans.tsv", sep="\t", index=False
    )
    print(f"  {sub} — {len(TASKS)} tasks written")


def main():
    write_bids_root()
    for dyad in DYADS:
        print(f"\nBIDSifying {dyad['id']}...")
        for role, sub in [("mother", dyad["mother"]), ("child", dyad["child"])]:
            bidsify_participant(sub, dyad)
    print("\nrawdata/ ready!")


if __name__ == "__main__":
    main()
