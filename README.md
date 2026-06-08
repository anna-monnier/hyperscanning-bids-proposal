# Hyperscanning EEG and BIDS: A Practical Proposal

**Author:** Anne Monnier — Université de Montréal  
**Contribution to:** [BIDS Issue #402 — Hyperscanning data storage](https://github.com/bids-standard/bids-specification/issues/402)

---

## Overview

This repository presents a **minimal and practical proposal** for organizing **hyperscanning EEG data** in BIDS, grounded in a real clinical research project (SCAALE — autism & social neuroscience, CHU Sainte-Justine / UdeM).

It is intended for anyone doing multimodal hyperscanning using:
- A **LabRecorder/LSL** setup producing XDF files
- **Behavioral video** recordings (multiple cameras)
- **Subjective ratings** of felt togetherness (e.g. IOS scale — Aron et al., 1992)

We provide:
- A **synthetic dataset** (3 dyads × 10 tasks) mirroring the real SCAALE pilot structure
- A **bidsification script** showing the full `sourcedata/ → rawdata/` transformation
- A **Jupyter notebook** explaining the problem, existing proposals, and our solution

---

## Our Core Proposal

The simplest possible solution: add a `dyad_id` column to `participants.tsv`.

```tsv
participant_id  role    group        dyad_id
sub-001         mother  non-autistic dyad-001
sub-002         child   autistic     dyad-001
sub-003         mother  non-autistic dyad-002
sub-004         child   autistic     dyad-002
```

| Property | Status |
|----------|--------|
| Standard BIDS (custom columns allowed) | ✅ |
| bids-validator compliant | ✅ |
| PyBIDS native | ✅ |
| Longitudinal compatible | ✅ |
| Scalable to triads and larger groups | ✅ |
| Carries role + group metadata | ✅ |

---

## Repository Structure

hyperscanning-bids-proposal/
│
├── generate_synthetic_data.py   ← Step 1: creates sourcedata/
├── bidsify.py                   ← Step 2: sourcedata/ → rawdata/
├── requirements.txt
│
├── sourcedata/                  ← raw data (XDF + IOS + video)
│   ├── dyad-001/
│   │   ├── EEG/dyad-001_eeg.xdf
│   │   ├── IOS/ios_sub-001.tsv
│   │   └── video/cam-*.mp4
│   ├── dyad-002/
│   └── dyad-003/
│
├── rawdata/                     ← BIDS dataset (already generated)
│   ├── dataset_description.json
│   ├── participants.tsv         ← dyad_id proposal
│   ├── participants.json
│   ├── events.json
│   ├── task-01restEyesOpen_eeg.json
│   ├── ... (10 task sidecars)
│   ├── sub-001/ses-01/eeg/
│   │   ├── sub-001_ses-01_task-01restEyesOpen_eeg.vhdr
│   │   ├── sub-001_ses-01_task-01restEyesOpen_events.tsv  ← IOS_rating column
│   │   ├── sub-001_ses-01_task-01restEyesOpen_channels.tsv
│   │   └── ... (10 tasks × 4 files)
│   └── ... (6 participants)
│
└── notebooks/
└── hyperscanning_bids_proposal.ipynb

---

## Getting Started

```bash
git clone https://github.com/anna-monnier/hyperscanning-bids-proposal
cd hyperscanning-bids-proposal
pip install -r requirements.txt

# rawdata/ is already included — open the notebook directly
jupyter notebook notebooks/hyperscanning_bids_proposal.ipynb

# Or regenerate from scratch:
python generate_synthetic_data.py
python bidsify.py
```

---

## Additional Proposals

### IOS ratings → `events.tsv`
Post-task subjective ratings (IOS — Inclusion of the Other in the Self, Aron et al., 1992) vary per task and per session — they are event-level measures, not stable participant traits. We propose storing them as a custom column in `events.tsv` rather than `phenotype/`.

### Behavioral video and dyad-level data
Raw videos remain in `sourcedata/`. Task-segmented videos and dyad-level annotations go into `derivatives/` because they are **shared between both participants** and cannot belong to `sub-001/` or `sub-002/` alone:

derivatives/
video-segmented/dyad-001/    ← shared between both participants
openpose/sub-001/motion/     ← per-subject pose vectors (BIDS Motion ✅)
openpose/sub-002/motion/     ← per-subject pose vectors (BIDS Motion ✅)
video-annotation/dyad-001/   ← leader/follower annotations

### Open questions for the community

| Question | Our position | Status |
|----------|-------------|--------|
| Post-task ratings (IOS) | Custom column in `events.tsv` | ✅ Proposed |
| Shared temporal reference (XDF) | Implicit via `dyad_id` + `sourcedata/` | ✅ Resolved |
| Dyad-level derivatives (PLV) | No BIDS convention needed for local analysis; future BEP for cross-lab sharing | ⚠️ Future BEP |
| Behavioral video | `sourcedata/` raw; `derivatives/video-segmented/dyad-001/` for segmented | ⚠️ Workaround |
| Post-hoc annotations (leader/follower) | `derivatives/video-annotation/dyad-001/` | ⚠️ Workaround |

---

## References

- Aron, A., Aron, E. N., & Smollan, D. (1992). Inclusion of Other in the Self Scale. *Journal of Personality and Social Psychology*, 63(4), 596–612.
- Poldrack et al. (2024). The past, present, and future of BIDS. *Imaging Neuroscience*. https://doi.org/10.1162/imag_a_00103
- Pernet et al. (2019). EEG-BIDS. *Scientific Data*. https://doi.org/10.1038/s41597-019-0104-8
- Appelhoff et al. (2019). MNE-BIDS. *JOSS*. https://doi.org/10.21105/joss.01896
- Luke et al. (2025). fNIRS-BIDS. *Scientific Data*. https://www.nature.com/articles/s41597-024-04136-9
- Monnier et al. (2025). Now is the time. *Neuroscience of Consciousness*. https://doi.org/10.1093/nc/niaf052
- BIDS Issue #402: https://github.com/bids-standard/bids-specification/issues/402
- Neurostars: https://neurostars.org/t/bids-structure-for-longitudinal-dyadic-data/26173
- NeuroBlueprint Issue #4: https://github.com/neuroinformatics-unit/NeuroBlueprint/issues/4