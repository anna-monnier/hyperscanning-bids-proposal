# Hyperscanning EEG and BIDS: A Practical Proposal

**Authors:** Anne Monnier, Guillaume Dumas — Université de Montréal  
**Contribution to:** [BIDS Issue #402 — Hyperscanning data storage](https://github.com/bids-standard/bids-specification/issues/402)

---

## Overview

This repository presents a concrete, minimal proposal for organizing **hyperscanning EEG data** in BIDS, grounded in a real research project (SCAALE — autism & social neuroscience, CHU Sainte-Justine / UdeM).

We provide:
- A **synthetic dataset** (3 dyads × 10 tasks) mirroring the real SCAALE pilot structure
- A **bidsification script** showing the full `sourcedata/ → rawdata/` transformation
- A **Jupyter notebook** explaining the problem, existing proposals, and our solution

---

## Our Core Proposal

Add a `dyad_id` column to `participants.tsv`:

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

```
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
```

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
Post-task subjective ratings vary per task — stored as a custom column in `events.tsv`.

### Open questions for the community

| Question | Status |
|----------|--------|
| Shared temporal reference (XDF/LSL) | ⚠️ Open |
| Dyad-level derivatives (PLV) | ❌ No convention |
| Raw video (3 cameras, dyad-level) | ❌ No BEP |
| Post-hoc annotations (leader/follower) | ❌ No convention |

---

## References

- Poldrack et al. (2024). The past, present, and future of BIDS. *Imaging Neuroscience*. https://doi.org/10.1162/imag_a_00103
- Pernet et al. (2019). EEG-BIDS. *Scientific Data*. https://doi.org/10.1038/s41597-019-0104-8
- Appelhoff et al. (2019). MNE-BIDS. *JOSS*. https://doi.org/10.21105/joss.01896
- Luke et al. (2025). fNIRS-BIDS. *Scientific Data*. https://www.nature.com/articles/s41597-024-04136-9
- Monnier et al. (2025). Now is the time. *Neuroscience of Consciousness*. https://doi.org/10.1093/nc/niaf052
- BIDS Issue #402: https://github.com/bids-standard/bids-specification/issues/402
- Neurostars: https://neurostars.org/t/bids-structure-for-longitudinal-dyadic-data/26173
