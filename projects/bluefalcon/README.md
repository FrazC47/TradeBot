# BlueFalcon Project

## Overview
AI-powered skill assessment system for construction trades using multi-angle video analysis and computer vision.

## Target Trades
1. **Steel Fixer** - Rebar work, tying, placement
2. **Shuttering Carpenter** - Formwork assembly, concrete preparation
3. **Mason** - Brick/block laying, mortar work

## Project Structure

```
bluefalcon/
├── analysis/          # Video analysis outputs and reports
├── models/            # Trained CV models and checkpoints
├── training-data/     # Labeled video datasets
├── outputs/           # Assessment results and visualizations
└── docs/              # Documentation and research notes
```

## Technical Stack
- **Computer Vision:** OpenCV, MediaPipe, YOLO
- **Video Processing:** FFmpeg, frame extraction
- **AI/ML:** Pose estimation, action recognition
- **Multi-angle:** Sync and fusion from multiple camera feeds

## Goals
1. Extract skill metrics from video (speed, precision, technique)
2. Compare against trade standards
3. Generate assessment reports
4. Identify training gaps

## Status
- [ ] Data collection strategy
- [ ] Model selection
- [ ] Training pipeline
- [ ] Assessment framework

---
*Created: 2026-02-26*
