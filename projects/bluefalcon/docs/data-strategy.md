# BlueFalcon Data Strategy: Multi-Angle Construction Skill Assessment

**Document Version:** 1.0  
**Date:** 2026-02-26  
**Project:** BlueFalcon AI-Powered Skill Assessment System  
**Scope:** Data collection, labeling, and training pipeline for construction trades

---

## Executive Summary

This document outlines the comprehensive data strategy for BlueFalcon's AI-powered skill assessment system targeting three critical construction trades:
- **Steel Fixer** — rebar work
- **Shuttering Carpenter** — formwork
- **Mason** — brick/block laying

The strategy addresses the unique challenges of construction skill assessment: occluded views, dynamic environments, safety equipment interference, and the need for fine-grained motion analysis.

---

## 1. Video Collection Protocols

### 1.1 General Collection Standards

| Parameter | Specification | Rationale |
|-----------|---------------|-----------|
| **Resolution** | Minimum 1080p (1920×1080), preferred 4K (3840×2160) | Captures fine motor details (rebar ties, mortar joints) |
| **Frame Rate** | 30 fps minimum, 60 fps preferred | Smooth motion capture for rapid hand movements |
| **Duration** | 3-8 minutes per task segment | Balances completeness with annotation efficiency |
| **Lighting** | Minimum 300 lux, diffused artificial lighting | Reduces shadows, ensures consistency |
| **Audio** | 48kHz stereo, ambient + lapel mic | Captures tool sounds for multi-modal analysis |

### 1.2 Multi-Angle Camera Configuration

**Standard Setup: 5-Camera Array**

```
         [Overhead - 90°]
              |
    [Left 45°] — [Subject] — [Right 45°]
              |
         [Front 0°]
```

| Camera Position | Angle | Distance | Purpose |
|-----------------|-------|----------|---------|
| **Front** | 0° (eye level) | 2.5m | Primary view, facial expressions, posture |
| **Left Profile** | 45° | 2.0m | Hand-tool interaction, body mechanics |
| **Right Profile** | 45° | 2.0m | Hand-tool interaction, body mechanics |
| **Overhead** | 90° (top-down) | 2.5m | Spatial arrangement, pattern recognition |
| **Close-up** | Variable | 0.8-1.2m | Fine detail capture (optional, movable) |

**Synchronization:**
- Hardware sync via genlock or network time protocol (NTP)
- Audio clapboard or LED flash for post-hoc alignment
- Timestamp overlay on all feeds

### 1.3 Trade-Specific Collection Protocols

#### 1.3.1 Steel Fixer (Rebar Work)

**Task Segments to Capture:**

| Task ID | Task Name | Duration | Key Actions |
|---------|-----------|----------|-------------|
| SF-01 | Rebar Cutting | 3-5 min | Measuring, marking, cutting with cutter |
| SF-02 | Rebar Bending | 3-5 min | Positioning, bending to angle, checking |
| SF-03 | Rebar Placement | 5-8 min | Layout, spacing, chair placement |
| SF-04 | Wire Tying (Single) | 3-5 min | Wire looping, twisting, cutting |
| SF-05 | Wire Tying (Cross) | 3-5 min | Intersection tying, tension control |
| SF-06 | Rebar Splicing | 4-6 min | Overlap measurement, tying, inspection |
| SF-07 | Mesh Installation | 5-8 min | Panel placement, overlap, securing |

**Special Considerations:**
- **PPE Requirements:** Steel-toed boots, gloves, safety glasses, hard hat
- **Background:** Clean, contrasting surface (plywood or concrete)
- **Tool Visibility:** Ensure cutting tools, bending jigs, and tying hooks are visible
- **Hand Coverage:** Gloves may obscure finger movements — capture without gloves for training reference (optional)

**Critical Angles for Rebar:**
- Overhead: Essential for spacing and layout patterns
- 45° side views: Critical for bending angles and tie tightness
- Close-up: Wire twisting technique (2-3 second shots)

#### 1.3.2 Shuttering Carpenter (Formwork)

**Task Segments to Capture:**

| Task ID | Task Name | Duration | Key Actions |
|---------|-----------|----------|-------------|
| SC-01 | Plywood Cutting | 4-6 min | Measuring, marking, circular saw operation |
| SC-02 | Panel Assembly | 5-8 min | Edge alignment, nailing/screwing sequence |
| SC-03 | Vertical Formwork Erection | 6-10 min | Panel lifting, positioning, bracing |
| SC-04 | Horizontal Formwork (Slab) | 6-10 min | Joist placement, plywood laying, securing |
| SC-05 | Tie Rod Installation | 4-6 min | Drilling, inserting, tightening |
| SC-06 | Corner Forming | 4-6 min | Miter cuts, corner assembly, reinforcement |
| SC-07 | Formwork Stripping | 3-5 min | Sequence, prying technique, panel handling |

**Special Considerations:**
- **Scale Reference:** Include measuring tape or known-size objects for dimension verification
- **Tool Variety:** Capture both hand tools (hammers, handsaws) and power tools
- **Material States:** Fresh-cut plywood edges, nail patterns, screw depths
- **Safety:** Hammer swing arcs must be visible for safety assessment

**Critical Angles for Formwork:**
- Front view: Panel alignment and verticality
- Side views: Bracing angles and tie rod placement
- Overhead: Layout patterns and spacing

#### 1.3.3 Mason (Brick/Block Laying)

**Task Segments to Capture:**

| Task ID | Task Name | Duration | Key Actions |
|---------|-----------|----------|-------------|
| MA-01 | Mortar Mixing | 4-6 min | Proportioning, mixing consistency, workability test |
| MA-02 | Mortar Spreading (Bed Joint) | 3-5 min | Load placement, spreading motion, thickness control |
| MA-03 | Brick Laying (Stretcher) | 4-6 min | Buttering, placement, tapping, alignment |
| MA-04 | Brick Laying (Header) | 4-6 min | Orientation, bond pattern, vertical alignment |
| MA-05 | Block Laying | 4-6 min | Handling, mortar application, leveling |
| MA-06 | Joint Finishing | 3-5 min | Tooling technique, profile consistency |
| MA-07 | Corner Building | 6-10 min | Lead construction, level/plumb checking |
| MA-08 | Opening Construction | 5-8 min | Lintel placement, reinforcement, bond pattern |

**Special Considerations:**
- **Mortar Visibility:** Use contrasting mortar color (white/light gray) against red/brown bricks
- **Wet vs. Dry:** Capture both dry layout and actual laying
- **Gauge Reference:** Include story pole or marked line for course height
- **Tool Variety:** Trowel types, jointing tools, levels, lines

**Critical Angles for Masonry:**
- 45° views: Trowel angle and mortar buttering technique
- Front view: Course alignment and bond pattern
- Close-up: Joint profile and mortar consistency

### 1.4 Participant Recruitment

**Skill Level Distribution:**

| Level | Experience | Target % | Rationale |
|-------|------------|----------|-----------|
| **Novice** | < 1 year | 25% | Baseline skill patterns, common errors |
| **Intermediate** | 1-5 years | 35% | Developing proficiency, varied techniques |
| **Expert** | 5+ years | 30% | Reference standard, efficient motions |
| **Master** | 10+ years, certified | 10% | Gold standard, teaching examples |

**Demographic Capture:**
- Age range: 18-60 years
- Hand dominance: Both left and right
- Body metrics: Height, arm span (for ergonomic analysis)
- Certification status: Trade certificates, apprenticeship completion

**Consent and Privacy:**
- Signed video release with specific use cases
- Option for face blurring in training dataset
- Right to withdraw consent with data deletion

---

## 2. Labeling Schema and Scoring Rubric

### 2.1 Multi-Level Annotation Taxonomy

```
Level 1: Task Classification
    └── Level 2: Sub-task Segmentation
            └── Level 3: Action Unit Detection
                    └── Level 4: Quality Metrics
```

#### 2.1.1 Level 1: Task Classification

**Labels:** Task ID from collection protocols (SF-01 through MA-08)

**Annotation:** Single label per video segment

**Format:**
```json
{
  "task_id": "SF-04",
  "task_name": "Wire Tying (Single)",
  "trade": "steel_fixer",
  "confidence": 1.0
}
```

#### 2.1.2 Level 2: Sub-task Segmentation (Temporal)

**Steel Fixer — Wire Tying Example:**

| Sub-task | Description | Typical Duration |
|----------|-------------|------------------|
| SF-04-S1 | Wire selection and positioning | 2-4 sec |
| SF-04-S2 | Loop formation around intersection | 3-5 sec |
| SF-04-S3 | Hook engagement and initial twist | 2-3 sec |
| SF-04-S4 | Tightening (rotations) | 3-6 sec |
| SF-04-S5 | Wire cutting/snapping | 1-2 sec |
| SF-04-S6 | Inspection and adjustment | 2-4 sec |

**Annotation Format:**
```json
{
  "segment_id": "SF-04-001",
  "sub_tasks": [
    {"label": "SF-04-S1", "start": 0.0, "end": 3.2},
    {"label": "SF-04-S2", "start": 3.2, "end": 7.5},
    {"label": "SF-04-S3", "start": 7.5, "end": 10.1},
    {"label": "SF-04-S4", "start": 10.1, "end": 15.8},
    {"label": "SF-04-S5", "start": 15.8, "end": 17.5},
    {"label": "SF-04-S6", "start": 17.5, "end": 21.0}
  ]
}
```

#### 2.1.3 Level 3: Action Unit Detection (Spatial-Temporal)

**Keypoints for Pose Estimation:**

| ID | Keypoint | Relevance by Trade |
|----|----------|-------------------|
| 0 | Nose | All (head position) |
| 1-2 | Eyes | All (gaze direction) |
| 3-4 | Ears | All |
| 5-6 | Shoulders | All (posture) |
| 7-8 | Elbows | All (arm mechanics) |
| 9-10 | Wrists | All (hand position) |
| 11-12 | Hips | All (body stance) |
| 13-14 | Knees | All (lifting posture) |
| 15-16 | Ankles | All (foot placement) |
| 17-22 | Hands (6 points) | All (fine motor) |

**Tool Detection Bounding Boxes:**

| Tool Class | Trades | Notes |
|------------|--------|-------|
| TROWEL | Mason | Blade angle critical |
| HAMMER | Shuttering | Swing arc analysis |
| WIRE_CUTTER | Steel Fixer | Cut position |
| WIRE_HOOK | Steel Fixer | Hook engagement |
| BENDING_JIG | Steel Fixer | Angle measurement |
| CIRCULAR_SAW | Shuttering | Safety zone |
| LEVEL | All | Bubble position |
| TAPE_MEASURE | All | Extension state |
| REBAR | Steel Fixer | Diameter class |
| BRICK | Mason | Orientation |
| BLOCK | Mason | Size class |
| PLYWOOD_PANEL | Shuttering | Size/position |

#### 2.1.4 Level 4: Quality Metrics

**Steel Fixer Scoring Rubric:**

| Metric | Weight | Novice | Intermediate | Expert | Measurement |
|--------|--------|--------|--------------|--------|-------------|
| **Tie Tightness** | 25% | Loose, gaps | Secure, minimal movement | Very tight, no play | Force estimation from wire deformation |
| **Tie Consistency** | 20% | Variable wraps | Mostly uniform | Identical wraps | Count wraps, measure overlap |
| **Wire Waste** | 15% | > 150mm tails | 100-150mm tails | < 100mm tails | Measure tail length |
| **Speed** | 20% | > 45 sec/tie | 30-45 sec/tie | < 30 sec/tie | Time per tie |
| **Posture** | 20% | Awkward, bent | Moderate stance | Ergonomic, balanced | Spine angle, knee bend |

**Shuttering Carpenter Scoring Rubric:**

| Metric | Weight | Novice | Intermediate | Expert | Measurement |
|--------|--------|--------|--------------|--------|-------------|
| **Panel Alignment** | 25% | Gaps > 3mm | Gaps 1-3mm | Seamless | Gap measurement |
| **Bracing Angle** | 20% | < 45° or > 60° | 45-60° | Optimal 45° | Angle from vertical |
| **Fastener Spacing** | 20% | Irregular | Mostly regular | Precise grid | Distance between fasteners |
| **Speed** | 15% | Slow, hesitant | Steady pace | Efficient, no waste | Time per panel |
| **Safety** | 20% | Violations present | Minor issues | Full compliance | PPE, tool handling |

**Mason Scoring Rubric:**

| Metric | Weight | Novice | Intermediate | Expert | Measurement |
|--------|--------|--------|--------------|--------|-------------|
| **Bed Joint Thickness** | 20% | Variable > 15mm | 10-15mm range | Consistent 10mm | Mortar thickness |
| **Perpend Alignment** | 20% | Misaligned | Mostly aligned | Perfect vertical | Plumb measurement |
| **Mortar Consistency** | 15% | Too wet/dry | Workable | Ideal plasticity | Visual texture |
| **Speed (bricks/hour)** | 15% | < 50 | 50-100 | > 100 | Count/time |
| **Joint Profile** | 15% | Irregular | Acceptable | Uniform, tooled | Profile gauge |
| **Waste** | 15% | Excessive mortar | Some waste | Minimal waste | Drop/mortar loss |

### 2.2 Annotation Tools and Workflow

**Recommended Stack:**
- **Temporal:** VIA (VGG Image Annotator) or CVAT for video segmentation
- **Spatial:** LabelStudio or Roboflow for bounding boxes and keypoints
- **Quality:** Custom scoring interface with reference videos

**Annotation Pipeline:**

```
Raw Video → Auto Pre-label (pose + objects) → Human Review → Quality Scoring → Final Export
```

**Auto Pre-labeling:**
- YOLOv8 for tool detection
- MediaPipe or RTMPose for body keypoints
- Temporal segmentation using action recognition model

**Human Review Requirements:**
- Minimum 2 annotators per video for quality metrics
- Inter-annotator agreement target: Cohen's κ > 0.8
- Expert validation for all expert-level skill ratings

---

## 3. Existing Datasets Research

### 3.1 Publicly Available Construction Datasets

| Dataset | Source | Size | Focus | Usability for BlueFalcon |
|---------|--------|------|-------|--------------------------|
| **Construction Meta Action (CMA)** | Yang et al. (2022) | 1,595 clips, 7 classes | Unsafe action detection | Medium — safety focus, limited skill detail |
| **Construction Site Video Dataset** | Kaggle | ~500 videos | General site activity | Low — unlabeled, variable quality |
| **Construction-PPE Dataset** | Ultralytics | 3,000+ images | PPE detection | Medium — pre-training for safety module |
| **Rebar Segmentation Dataset** | ScienceDirect (2025) | 14,805 images | Defect detection | Low — post-construction inspection |
| **MAVSD** | Nature (2025) | Multi-angle plant dataset | Segmentation | Low — different domain, methodology reference |

### 3.2 Domain-Adjacent Datasets

| Dataset | Domain | Relevance |
|---------|--------|-----------|
| **Something-Something V2** | General action | Temporal reasoning pre-training |
| **Kinetics-700** | General video | Action recognition backbone pre-training |
| **EPIC-KITCHENS** | Egocentric manipulation | Tool-hand interaction patterns |
| **Assembly101** | Industrial assembly | Fine-grained action segmentation |
| **FineGym** | Gymnastics | Skill assessment methodology |

### 3.3 Key Findings

**Gap Analysis:**
- **No existing dataset** specifically targets construction skill assessment with multi-angle video
- Most construction datasets focus on **safety compliance** rather than skill quality
- **Temporal granularity** in existing datasets is insufficient for fine-grained skill analysis
- **Multi-modal data** (video + audio + tool sensors) is absent in public datasets

**Recommendations:**
1. Use CMA and Construction-PPE for **safety module pre-training**
2. Use Kinetics-700 for **action recognition backbone**
3. Use Assembly101 methodology for **temporal segmentation approach**
4. Build BlueFalcon dataset as **primary skill assessment resource**

---

## 4. Data Augmentation Strategies

### 4.1 Spatial Augmentations

| Technique | Parameters | Applicability | Trade Notes |
|-----------|------------|---------------|-------------|
| **Random Crop** | 80-100% of frame | All | Avoid cropping critical hand regions |
| **Horizontal Flip** | 50% probability | All | Rebar work: symmetric OK; Masonry: check bond pattern |
| **Rotation** | ±15° | All | Compensate for camera tilt |
| **Color Jitter** | Brightness ±20%, Contrast ±20% | All | Simulate lighting variation |
| **Gaussian Noise** | σ = 0.01-0.05 | All | Simulate compression artifacts |
| **Motion Blur** | Kernel 3-7px | All | Simulate fast movements |

### 4.2 Temporal Augmentations

| Technique | Parameters | Purpose |
|-----------|------------|---------|
| **Temporal Crop** | 80-100% of clip | Variable task duration |
| **Speed Perturbation** | 0.8x - 1.2x | Normalize speed variation |
| **Frame Drop** | Random 1-2 frames | Robustness to frame loss |
| **Temporal Reverse** | 50% probability | Bidirectional learning |
| **Slow-Motion Insertion** | 2x interpolation | Emphasize critical moments |

### 4.3 Multi-Angle Fusion Augmentations

| Technique | Description | Benefit |
|-----------|-------------|---------|
| **View Dropout** | Randomly mask 1-2 camera views | Robustness to occlusions |
| **View Substitution** | Swap similar angles during training | Cross-view generalization |
| **Angle Interpolation** | Synthesize intermediate views | Data efficiency |
| **Multi-View Mixup** | Blend features from different views | Regularization |

### 4.4 Domain-Specific Augmentations

**Steel Fixer:**
- Rebar density variation (synthesize crowded layouts)
- Wire gauge simulation (thickness adjustment)
- Glove type variation (color/texture)

**Shuttering Carpenter:**
- Plywood texture variation
- Nail/screw pattern synthesis
- Shadow simulation for outdoor conditions

**Mason:**
- Brick color/texture variation
- Mortar color adjustment (different mixes)
- Weathering effects on materials

### 4.5 Synthetic Data Generation

**Physics-Based Simulation:**
- Use Unity/Unreal Engine for tool interaction simulation
- Generate ground-truth annotations automatically
- Blend synthetic backgrounds with real tool/hand footage

**Target Ratio:**
- Real data: 70%
- Augmented real: 20%
- Synthetic: 10%

---

## 5. Train/Validation/Test Splits

### 5.1 Overall Distribution

**Primary Split (Stratified by Trade and Skill Level):**

| Split | Percentage | Videos | Purpose |
|-------|------------|--------|---------|
| **Training** | 70% | ~2,100 | Model training |
| **Validation** | 15% | ~450 | Hyperparameter tuning |
| **Test** | 15% | ~450 | Final evaluation |

### 5.2 Stratification Strategy

**By Trade:**

| Trade | Training | Validation | Test | Total |
|-------|----------|------------|------|-------|
| Steel Fixer | 700 | 150 | 150 | 1,000 |
| Shuttering Carpenter | 700 | 150 | 150 | 1,000 |
| Mason | 700 | 150 | 150 | 1,000 |

**By Skill Level (per trade):**

| Level | Training | Validation | Test |
|-------|----------|------------|------|
| Novice | 175 | 37 | 38 |
| Intermediate | 245 | 53 | 52 |
| Expert | 210 | 45 | 45 |
| Master | 70 | 15 | 15 |

### 5.3 Cross-Validation Strategy

**Leave-One-Participant-Out (LOPO):**
- For skill level classification, ensure no participant appears in both train and test
- Critical for generalization assessment

**Temporal Split:**
- For time-series models, maintain chronological order
- Test on most recent data

### 5.4 Geographic/Environmental Splits

**Holdout Sets for Robustness Testing:**

| Condition | Split | Purpose |
|-----------|-------|---------|
| **Indoor/Outdoor** | 90/10 | Lighting variation |
| **Season** | 80/20 (winter holdout) | Weather gear effects |
| **Region** | 85/15 | Cultural technique variation |

---

## 6. Quality Control Measures

### 6.1 Collection Quality

**Pre-Recording Checklist:**
- [ ] All 5 cameras recording and synced
- [ ] Lighting ≥ 300 lux (measure with lux meter)
- [ ] Background clean and contrasting
- [ ] Audio levels checked (peak -12dB)
- [ ] Participant consent signed
- [ ] Skill level verified (certificate check)

**During Recording:**
- [ ] Continuous monitoring of all feeds
- [ ] Real-time blur detection (Laplacian variance > 100)
- [ ] Audio clipping detection
- [ ] Participant comfort check every 10 minutes

**Post-Recording:**
- [ ] Sync verification (all cameras aligned within 1 frame)
- [ ] Resolution check (no downscaling artifacts)
- [ ] Coverage review (all required angles present)
- [ ] Backup to redundant storage

### 6.2 Annotation Quality

**Inter-Annotator Agreement (IAA):**

| Annotation Type | Metric | Target | Action if Below |
|-----------------|--------|--------|-----------------|
| Task Classification | Accuracy | > 95% | Review guidelines |
| Temporal Segmentation | IoU | > 0.85 | Calibration session |
| Keypoints | OKS | > 0.90 | Re-training |
| Quality Scoring | ICC | > 0.80 | Expert arbitration |

**Quality Assurance Workflow:**

```
Annotator A → Annotator B (independent) → Agreement Check → 
  ├─ Pass → Final Label
  └─ Fail → Expert Review → Consensus Label
```

### 6.3 Data Validation Pipeline

**Automated Checks:**

| Check | Threshold | Action |
|-------|-----------|--------|
| Video corruption | 0 frames dropped | Re-record if failed |
| Audio sync drift | < 40ms | Re-sync or discard |
| Annotation completeness | 100% fields | Return to annotator |
| Outlier detection | Z-score < 3 | Expert review |

**Manual Spot Checks:**
- 10% random sample review by project lead
- 100% review of expert-level ratings
- 100% review of failed quality checks

### 6.4 Bias Mitigation

**Demographic Balance Monitoring:**

| Factor | Target Distribution | Check Frequency |
|--------|---------------------|-----------------|
| Age | Match workforce demographics | Weekly |
| Gender | Match trade representation | Weekly |
| Hand dominance | 15% left-handed | Monthly |
| Body type | Representative range | Monthly |

**Technique Bias:**
- Capture multiple valid techniques (not just "textbook")
- Regional variation documentation
- Tool brand/type variation

---

## 7. Dataset Size Recommendations

### 7.1 Minimum Viable Dataset (MVD)

**Phase 1: Proof of Concept (Months 1-3)**

| Trade | Videos | Participants | Hours |
|-------|--------|--------------|-------|
| Steel Fixer | 100 | 10 | 8 |
| Shuttering Carpenter | 100 | 10 | 8 |
| Mason | 100 | 10 | 8 |
| **Total** | **300** | **30** | **24** |

**Coverage:** 3 tasks per trade, 2 skill levels (novice, expert)

### 7.2 Production Dataset

**Phase 2: Full Training (Months 4-12)**

| Trade | Videos | Participants | Hours |
|-------|--------|--------------|-------|
| Steel Fixer | 1,000 | 80 | 80 |
| Shuttering Carpenter | 1,000 | 80 | 80 |
| Mason | 1,000 | 80 | 80 |
| **Total** | **3,000** | **240** | **240** |

**Coverage:** All 7 tasks per trade, 4 skill levels

### 7.3 Scale-Up Projections

| Phase | Videos | Annotations | Storage |
|-------|--------|-------------|---------|
| MVD | 300 | 15,000 | 500 GB |
| Production | 3,000 | 150,000 | 5 TB |
| Expansion | 10,000 | 500,000 | 15 TB |

**Annotation Estimates:**
- Temporal segments: ~50 per video
- Keypoints: ~17 points × 30 fps × duration
- Bounding boxes: ~10 objects per frame

---

## 8. Implementation Timeline

### 8.1 Phase 1: Foundation (Weeks 1-4)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1 | Equipment procurement | 5-camera rigs × 3 |
| 2 | Recording space setup | Studio with lighting |
| 3 | Annotation tool deployment | CVAT + LabelStudio |
| 4 | Pilot recording (10 videos) | Protocol validation |

### 8.2 Phase 2: Collection (Weeks 5-20)

| Week | Activity | Target |
|------|----------|--------|
| 5-8 | Steel Fixer collection | 250 videos |
| 9-12 | Shuttering Carpenter collection | 250 videos |
| 13-16 | Mason collection | 250 videos |
| 17-20 | Fill gaps, re-records | 250 videos |

### 8.3 Phase 3: Annotation (Weeks 12-32)

| Week | Activity | Target |
|------|----------|--------|
| 12-16 | Level 1 & 2 annotation | 1,000 videos |
| 17-24 | Level 3 annotation | 1,500 videos |
| 25-32 | Level 4 quality scoring | 1,500 videos |

### 8.4 Phase 4: Validation (Weeks 28-40)

| Week | Activity | Target |
|------|----------|--------|
| 28-32 | IAA analysis | κ > 0.8 all metrics |
| 33-36 | Model benchmarking | Baseline results |
| 37-40 | Dataset release | v1.0 published |

---

## 9. Tools and Infrastructure

### 9.1 Hardware Requirements

**Per Recording Station:**

| Component | Specification | Quantity | Cost (USD) |
|-----------|---------------|----------|------------|
| 4K Camera | Sony A7 IV or equivalent | 5 | $15,000 |
| Lenses | 24-70mm f/2.8 | 5 | $5,000 |
| Tripods | Manfrotto with fluid head | 5 | $2,500 |
| Lighting | LED panel kit (3-point) | 2 sets | $2,000 |
| Audio | Wireless lapel + recorder | 2 | $1,000 |
| Sync Device | Tentacle Sync or equivalent | 1 | $500 |
| Storage | 4TB SSD (on-site) | 2 | $800 |
| **Station Total** | | | **$26,800** |

**Annotation Workstations:**

| Component | Specification | Quantity | Cost (USD) |
|-----------|---------------|----------|------------|
| Workstation | RTX 4090, 64GB RAM | 5 | $20,000 |
| Monitors | 27" 4K color-calibrated | 10 | $5,000 |
| **Annotation Total** | | | **$25,000** |

### 9.2 Software Stack

| Function | Tool | License |
|----------|------|---------|
| Video annotation | CVAT | Open source |
| Keypoint annotation | LabelStudio | Open source |
| Data versioning | DVC | Open source |
| Storage | MinIO/S3 | Open source/Cloud |
| Workflow | Apache Airflow | Open source |
| Quality metrics | Custom + FiftyOne | Mixed |

### 9.3 Storage Architecture

```
Raw Video (S3 Glacier) → Processed Clips (S3 Standard) → 
  Annotations (PostgreSQL) → Features (Parquet) → 
    Training Cache (Local SSD)
```

**Retention Policy:**
- Raw video: 7 years (compliance)
- Processed clips: Permanent
- Annotations: Permanent + versioned
- Features: Regenerable

---

## 10. Ethical Considerations

### 10.1 Participant Protection

- **Informed Consent:** Clear explanation of data use, retention, and deletion rights
- **Right to Withdraw:** Participants can request data deletion at any time
- **Face Blurring:** Optional for participants concerned about privacy
- **Data Minimization:** Collect only necessary demographic information

### 10.2 Bias Prevention

- **Inclusive Recruitment:** Target underrepresented groups in construction
- **Technique Diversity:** Capture valid regional/cultural variations
- **Fair Assessment:** Regular audit for demographic performance disparities

### 10.3 Data Security

- **Encryption:** At-rest (AES-256) and in-transit (TLS 1.3)
- **Access Control:** Role-based, principle of least privilege
- **Audit Logging:** All data access logged and reviewed
- **Geographic Restrictions:** Data residency compliance

---

## 11. Success Metrics

### 11.1 Data Quality KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Annotation accuracy | > 95% | Expert spot-check |
| Inter-annotator agreement | κ > 0.8 | Cohen's kappa |
| Video quality pass rate | > 98% | Automated checks |
| Participant satisfaction | > 4.5/5 | Post-session survey |

### 11.2 Model Performance Targets

| Task | Metric | Target |
|------|--------|--------|
| Task classification | Accuracy | > 90% |
| Temporal segmentation | F1@0.5 | > 0.85 |
| Keypoint detection | OKS | > 0.85 |
| Skill level classification | Accuracy | > 80% |
| Quality score regression | MAE | < 0.5 (1-5 scale) |

---

## 12. Conclusion

This data strategy provides a comprehensive framework for building BlueFalcon's construction skill assessment dataset. Key success factors:

1. **Rigorous collection protocols** ensure consistent, high-quality video
2. **Multi-level annotation taxonomy** enables fine-grained skill analysis
3. **Stratified splits** support fair evaluation across trades and skill levels
4. **Quality control at every stage** maintains dataset integrity
5. **Ethical practices** protect participants and ensure fair assessment

The phased approach allows for iterative improvement while building toward a production-grade dataset that can train robust, generalizable skill assessment models.

---

## Appendix A: Annotation Schema JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BlueFalcon Video Annotation",
  "type": "object",
  "required": ["video_id", "trade", "task_id", "segments"],
  "properties": {
    "video_id": {"type": "string"},
    "trade": {"enum": ["steel_fixer", "shuttering_carpenter", "mason"]},
    "task_id": {"type": "string"},
    "participant": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "skill_level": {"enum": ["novice", "intermediate", "expert", "master"]},
        "years_experience": {"type": "number"},
        "hand_dominance": {"enum": ["left", "right", "ambidextrous"]}
      }
    },
    "segments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sub_task_id": {"type": "string"},
          "start_time": {"type": "number"},
          "end_time": {"type": "number"},
          "keypoints": {"type": "array"},
          "bounding_boxes": {"type": "array"},
          "quality_scores": {"type": "object"}
        }
      }
    }
  }
}
```

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Bed Joint** | Horizontal mortar joint in masonry |
| **Formwork** | Temporary molds into which concrete is poured |
| **Perpend** | Vertical mortar joint in masonry |
| **Rebar** | Steel reinforcement bar |
| **Shuttering** | Temporary structure supporting concrete until set |
| **Tie Wire** | Wire used to secure intersecting rebar |
| **OKS** | Object Keypoint Similarity (metric) |
| **IoU** | Intersection over Union (metric) |
| **Cohen's κ** | Inter-annotator agreement statistic |

---

*Document maintained by BlueFalcon Data Team. Last updated: 2026-02-26*
