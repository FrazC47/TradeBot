# BlueFalcon Computer Vision Research Report
## AI-Powered Skill Assessment for Construction Trades

**Date:** February 2026  
**Prepared for:** BlueFalcon Development Team  
**Scope:** Pose estimation, action recognition, and multi-camera systems for construction worker skill assessment

---

## Executive Summary

This report provides comprehensive recommendations for computer vision approaches to analyze multi-angle video of construction workers performing skilled tasks. The target trades include Steel Fixers (rebar work), Shuttering Carpenters (formwork assembly), and Masons (brick/block laying).

**Key Recommendations:**
- **Primary Pose Estimation:** YOLO11 Pose (best accuracy-speed tradeoff)
- **Edge Deployment:** MediaPipe Pose (lightweight, mobile-optimized)
- **Action Recognition:** Skeleton + Video Fusion with Transformer-based fusion
- **Multi-Camera:** Triangulation-based 3D pose estimation with synchronized industrial cameras

---

## 1. Pose Estimation Model Comparison

### 1.1 Model Overview

| Model | Type | Keypoints | mAP@0.5 (COCO) | Speed (FPS) | Resource Needs | Best For |
|-------|------|-----------|----------------|-------------|----------------|----------|
| **YOLO11 Pose (m)** | Single-stage CNN | 17 (COCO) | 89.4% | 30+ (T4) | Medium GPU | Production, accuracy-critical |
| **YOLO11 Pose (n)** | Single-stage CNN | 17 (COCO) | ~85% | 60+ (T4) | Low GPU/CPU | Edge deployment, speed-critical |
| **MediaPipe Pose** | BlazePose | 33 (heavy) | ~80% | 30+ (mobile) | Mobile/Edge | Real-time mobile apps |
| **MoveNet Thunder** | CNN | 17 (COCO) | ~80% | 30 (mobile CPU) | Mobile/Edge | Balanced mobile performance |
| **MoveNet Lightning** | CNN | 17 (COCO) | ~75% | 60+ (mobile CPU) | Mobile/Edge | Ultra-fast mobile inference |
| **OpenPose** | Bottom-up PAF | 25/135 | 67-75% | 10-20 (GPU) | High GPU | Multi-person, research |
| **HRNet** | High-res CNN | 17 (COCO) | 77.8% | 15-20 (GPU) | High GPU | High-precision static images |
| **ViTPose** | Vision Transformer | 17 (COCO) | 80.9% | 10-15 (GPU) | High GPU | State-of-art accuracy |
| **DETR Pose** | Transformer | 17 (COCO) | ~78% | 8-12 (GPU) | High GPU | End-to-end detection |

### 1.2 Detailed Analysis

#### YOLO11 Pose (Recommended Primary)
- **Strengths:**
  - Best accuracy-speed tradeoff for production
  - Single-stage architecture: detection + pose in one forward pass
  - Multiple size variants (n/s/m/l/x) for different deployment targets
  - Easy fine-tuning on custom datasets via Ultralytics API
  - Strong multi-person detection in crowded scenes
  - 30+ FPS on NVIDIA T4 for real-time assessment

- **Limitations:**
  - Requires GPU for optimal performance
  - Less detailed keypoints than MediaPipe (17 vs 33)

- **Deployment Targets:**
  - Cloud/Server: YOLO11m or YOLO11l
  - Edge: YOLO11n or YOLO11s
  - Mobile: Not recommended (use MediaPipe instead)

#### MediaPipe Pose (Recommended for Edge/Mobile)
- **Strengths:**
  - 33 keypoints including facial features and hand details
  - Optimized for mobile and edge devices (TensorFlow Lite)
  - Real-time performance on mid-range smartphones
  - Cross-platform (Android, iOS, Web, Python)
  - Built-in world coordinate 3D pose estimation
  - Minimal dependencies

- **Limitations:**
  - Single-person focus (multi-person requires additional logic)
  - Lower accuracy than YOLO11 on COCO benchmarks
  - Limited customization compared to YOLO

- **Deployment Targets:**
  - Mobile apps
  - Raspberry Pi / Jetson Nano
  - Browser-based assessment tools

#### OpenPose (Legacy/Research)
- **Strengths:**
  - Pioneer in multi-person pose estimation
  - Part Affinity Fields (PAFs) for robust skeleton formation
  - Large body of research and community support

- **Limitations:**
  - Slower inference (10-20 FPS even on GPU)
  - Higher computational requirements
  - Being superseded by newer architectures

#### MoveNet (Google TensorFlow)
- **Strengths:**
  - Two variants: Thunder (accurate) and Lightning (fast)
  - Optimized for TensorFlow Lite deployment
  - Good accuracy on mobile devices
  - 25-35ms inference on mobile CPU (Thunder)

- **Limitations:**
  - Single-person detection
  - Less accurate than YOLO11 on construction-specific poses

### 1.3 Recommendation by Use Case

| Use Case | Recommended Model | Variant | Rationale |
|----------|-------------------|---------|-----------|
| Server-side assessment | YOLO11 Pose | m or l | Best accuracy, handles multi-person |
| Edge gateway (site office) | YOLO11 Pose | s or n | Balanced speed/accuracy |
| Mobile supervisor app | MediaPipe Pose | Full | Native mobile optimization |
| Quick field check | MoveNet Lightning | - | Fastest mobile inference |
| Research/Experimentation | ViTPose or HRNet | Base | Maximum accuracy for analysis |

---

## 2. Action Recognition Frameworks

### 2.1 Approach Categories

For construction worker skill assessment, we recommend a **dual-modality approach** combining skeleton sequences with video frames.

#### Skeleton-Based Methods
- **Graph Convolutional Networks (GCN):** ST-GCN, 2s-AGCN
  - Model body joint relationships as graphs
  - Good for repetitive motion patterns
  - Lightweight compared to video methods

- **CNN-based:** HCN, ClsNet
  - Treat skeleton sequences as pseudo-images
  - Easier to implement but less interpretable

- **Transformer-based:** PoseFormer, MixSTE
  - Capture long-range temporal dependencies
  - State-of-the-art for skeleton-only tasks

#### Video-Based Methods
- **Two-Stream Networks:** TSN, TRN
  - RGB + Optical Flow streams
  - Good for appearance-based actions

- **3D CNNs:** I3D, S3D
  - Direct spatiotemporal feature learning
  - High accuracy but computationally expensive

- **SlowFast Networks:**
  - Dual pathway: slow (spatial) + fast (temporal)
  - Excellent for construction activities with varying speeds
  - Recommended for multi-time scale action recognition

#### Skeleton-Video Fusion (Recommended)
Based on recent research (Mahdavian et al., 2024), fusion approaches outperform single modalities:

**Architecture:**
```
Skeleton Stream → Skeleton Encoder →
                                      → Fusion Module → Classification
Video Stream   → Video Encoder    →
```

**Fusion Strategies:**
1. **Early Fusion:** Concatenate features before classification
2. **Late Fusion:** Separate classifiers with weighted averaging
3. **Attention-based Fusion:** Learn importance weights per modality (Recommended)
4. **Transformer Fusion:** Cross-attention between modalities (Best accuracy)

### 2.2 Recommended Stack for Construction Tasks

| Component | Recommendation | Notes |
|-----------|----------------|-------|
| Skeleton Feature Extraction | YOLO11 Pose or MediaPipe | 17-33 keypoints |
| Temporal Modeling | SlowFast or Transformer | Captures varying speeds |
| Fusion Strategy | Attention-based Transformer | Prioritizes informative frames |
| Classification | Linear + Softmax or Contrastive Learning | For skill scoring |

### 2.3 Training Data Requirements

- **Minimum:** 100 samples per action class
- **Recommended:** 500+ samples per class with variations
- **Augmentation:** Spatial (crop, flip), Temporal (speed variation, frame dropout)
- **Annotation:** Action labels + skill scores for supervised learning

---

## 3. Multi-Camera Synchronization & View Fusion

### 3.1 Camera Configuration

For comprehensive skill assessment, we recommend a **4-camera setup**:

```
        [Camera 1: Front]
              ↓
    [Camera 2: Left] — [Worker] — [Camera 3: Right]
              ↑
        [Camera 4: Overhead/Back]
```

**Camera Angles:**
- **Front (0°):** Primary view for hand/tool interactions
- **Left/Right (90°):** Depth perception, side motion analysis
- **Overhead (Top-down):** Workspace layout, material placement

### 3.2 Synchronization Methods

| Method | Accuracy | Complexity | Cost | Recommendation |
|--------|----------|------------|------|----------------|
| **Hardware Sync (Genlock)** | <1ms | Medium | High | Professional setups |
| **NTP/PTP Network Sync** | 1-10ms | Low | Low | Recommended for most cases |
| **Audio/Clapboard Sync** | ~16ms | Low | None | Post-processing backup |
| **Self-Supervised Learning** | Variable | High | None | Research environments |

**Recommended Approach:** PTP (Precision Time Protocol) over local network for sub-millisecond synchronization.

### 3.3 3D Pose Estimation from Multi-View

#### Method 1: Triangulation (Recommended for Construction)
1. Detect 2D poses in each camera view
2. Use calibrated camera parameters (intrinsic + extrinsic)
3. Triangulate 3D joint positions from 2D correspondences
4. Handle occlusions via view selection

**Advantages:**
- Simple and interpretable
- Works with any 2D pose estimator
- Real-time capable

**Challenges:**
- Requires accurate camera calibration
- Occlusions in individual views

#### Method 2: Volumetric Fusion
1. Generate 2D heatmaps from each view
2. Project into 3D voxel space
3. Aggregate across views
4. Regress 3D joints from volume

**Advantages:**
- Handles occlusions better
- Soft correspondence matching

**Challenges:**
- Higher computational cost
- Memory intensive

#### Method 3: Learned Multi-View Fusion
- Train network to directly predict 3D pose from multi-view 2D
- Examples: VoxelPose, MVS-Fuse

**Advantages:**
- End-to-end trainable
- Can learn to handle occlusions

**Challenges:**
- Requires training data
- Less interpretable

### 3.4 Camera Calibration

**Intrinsic Parameters (per camera):**
- Focal length (fx, fy)
- Principal point (cx, cy)
- Distortion coefficients (k1, k2, p1, p2, k3)

**Extrinsic Parameters (camera-to-world):**
- Rotation matrix (R)
- Translation vector (t)

**Calibration Method:**
1. Use checkerboard or ChArUco pattern
2. Capture 20+ images per camera from different angles
3. Solve for parameters using OpenCV
4. Refine with bundle adjustment

---

## 4. Key Body Landmarks & Motion Patterns by Trade

### 4.1 Steel Fixer — Rebar Tying, Placement, Bending

**Critical Landmarks:**
- **Hands/Wrists (4 points):** Tool manipulation, wire tying
- **Elbows (2 points):** Bending motion, leverage
- **Shoulders (2 points):** Lifting, carrying heavy rebar
- **Spine/Torso:** Posture during bending (safety critical)
- **Knees (2 points):** Squatting, kneeling positions

**Key Motion Metrics:**

| Metric | Description | Assessment Criteria |
|--------|-------------|---------------------|
| **Tying Speed** | Cycles per minute | >15 ties/min = proficient |
| **Hand Coordination** | Bilateral symmetry | <10% variance between hands |
| **Bend Angle** | Torso flexion angle | <30° = good posture |
| **Wire Twist Consistency** | Rotation pattern variance | <5° variance = expert |
| **Rebar Placement Precision** | Distance from target | <2cm = acceptable |
| **Fatigue Indicators** | Posture degradation over time | Slope of bend angle increase |

**Action Classes:**
1. Measuring/Cutting rebar
2. Placing rebar in position
3. Tying wire (single/double wrap)
4. Bending rebar (manual/tool-assisted)
5. Lifting/Carrying rebar bundles

### 4.2 Shuttering Carpenter — Formwork Assembly, Leveling, Concrete Prep

**Critical Landmarks:**
- **Hands/Wrists:** Tool grip, fastener manipulation
- **Shoulders:** Panel lifting, overhead work
- **Torso/Hips:** Posture during assembly
- **Feet/Ankles:** Stance stability on uneven surfaces
- **Head:** Visual attention direction

**Key Motion Metrics:**

| Metric | Description | Assessment Criteria |
|--------|-------------|---------------------|
| **Panel Alignment Speed** | Time to position panel | <30s per panel = proficient |
| **Fastener Tightening Pattern** | Torque application sequence | Consistent pattern = expert |
| **Leveling Precision** | Bubble level reading accuracy | <1mm over 1m = acceptable |
| **Overhead Work Duration** | Time with arms above 90° | <20% of task = good ergonomics |
| **Stance Adjustments** | Foot repositioning frequency | <3 per minute = stable |
| **Tool Transition Time** | Time between tool switches | <2s = efficient |

**Action Classes:**
1. Panel positioning and alignment
2. Fastener installation (nails, screws, clamps)
3. Leveling and plumbing
4. Bracing installation
5. Concrete release agent application
6. Formwork inspection

### 4.3 Mason — Brick/Block Laying, Mortar Application, Alignment

**Critical Landmarks:**
- **Hands/Wrists:** Trowel manipulation, brick placement
- **Elbows:** Trowel motion arc, striking
- **Shoulders:** Material handling
- **Torso:** Bending and reaching patterns
- **Head:** Visual attention (line checking)

**Key Motion Metrics:**

| Metric | Description | Assessment Criteria |
|--------|-------------|---------------------|
| **Laying Rate** | Units per hour | >50 bricks/hour = proficient |
| **Mortar Consistency** | Spread pattern uniformity | Even coverage = expert |
| **Joint Thickness Consistency** | Variance in mortar bed | <2mm variance = acceptable |
| **Trowel Motion Efficiency** | Arc smoothness, minimal re-dips | <3 strokes per brick = efficient |
| **Plumb/Level Accuracy** | Vertical/horizontal alignment | <3mm over 1m = acceptable |
| **Material Handling** | Brick pickup to placement time | <3s = efficient |

**Action Classes:**
1. Mortar mixing/retempering
2. Mortar spreading (bed joint)
3. Brick/block placement
4. Joint tooling/finishing
5. Line checking and adjustment
6. Cutting bricks (manual/saw)

---

## 5. Hardware & Camera Setup Recommendations

### 5.1 Camera Specifications

| Specification | Minimum | Recommended | Premium |
|--------------|---------|-------------|---------|
| **Resolution** | 1080p (1920×1080) | 4K (3840×2160) | 4K + HDR |
| **Frame Rate** | 30 FPS | 60 FPS | 60+ FPS |
| **Lens** | 2.8mm (wide) | 2.8-12mm varifocal | Motorized zoom |
| **Protection** | IP66 | IP67 | IP67 + IK10 |
| **Temperature** | -10°C to 50°C | -20°C to 60°C | -30°C to 70°C |
| **Connectivity** | Ethernet | PoE Ethernet | PoE + WiFi backup |
| **Low Light** | 0.1 lux | 0.01 lux (Starlight) | Color night vision |

### 5.2 Recommended Camera Models

**Budget Option:**
- Hikvision DS-2CD2143G2-I (4MP, IP67, PoE)
- Cost: ~$150 per camera

**Mid-Range (Recommended):**
- Axis P3265-V (4MP, IP52, Lightfinder)
- Cost: ~$600 per camera

**Industrial/Rugged:**
- Bosch FLEXIDOME IP starlight 8000i
- Cost: ~$1,200 per camera

### 5.3 Computing Hardware

**Edge Gateway (On-site):**
- NVIDIA Jetson AGX Orin (64GB)
  - 275 TOPS AI performance
  - Supports 8+ camera streams
  - Industrial temperature range
  - Cost: ~$1,500

**Alternative Edge:**
- Intel NUC 13 Pro + Coral TPU
  - Good for 2-4 camera streams
  - Cost: ~$800

**Server/Cloud:**
- NVIDIA RTX A6000 or A100
  - For centralized processing
  - Multi-worker assessment capability

### 5.4 Camera Placement Guidelines

**General Principles:**
1. **Height:** 2.5-3m for worker visibility, minimize occlusion
2. **Distance:** 3-5m from work area for optimal coverage
3. **Overlap:** 20-30% overlap between adjacent cameras
4. **Lighting:** Avoid backlighting, use IR illuminators for low light
5. **Protection:** Weather housings, vibration dampening

**Trade-Specific Placement:**

| Trade | Primary Camera | Secondary Cameras | Special Considerations |
|-------|---------------|-------------------|------------------------|
| **Steel Fixer** | Front (hand level) | Side (bending angle), Overhead (workspace) | Capture wire tying from front; bending posture from side |
| **Shuttering Carpenter** | Front (panel work) | Side (alignment), Overhead (layout) | Wide angle for panel movement; level checking visibility |
| **Mason** | Front (trowel work) | Side (wall alignment), 45° (joint work) | Close-up capability for mortar work; line visibility |

**Mounting Recommendations:**
- Tripods with sandbags for temporary setups
- Wall/pole mounts with vibration isolation for semi-permanent
- Ceiling drops with cable management for permanent installations

### 5.5 Network & Storage

**Network Requirements:**
- Minimum: Gigabit Ethernet backbone
- Recommended: 10GbE for 4+ 4K cameras
- Latency: <5ms between cameras and processing unit

**Storage (per hour of assessment):**
- Raw 4K @ 60FPS: ~45GB/hour per camera
- Compressed H.265: ~9GB/hour per camera
- Pose data only: ~50MB/hour per worker

**Recommended:** Store raw video for 30 days, pose data indefinitely.

---

## 6. Recommended Technology Stack

### 6.1 By Deployment Scenario

#### Scenario A: Fixed Assessment Station (Recommended)
**Use Case:** Training center, certification facility

| Component | Technology |
|-----------|------------|
| Pose Estimation | YOLO11 Pose (Medium) |
| 3D Reconstruction | Multi-view triangulation |
| Action Recognition | SlowFast + Skeleton Fusion |
| Cameras | 4× Industrial IP cameras (4K) |
| Edge Compute | NVIDIA Jetson AGX Orin |
| Framework | PyTorch + Ultralytics |
| Deployment | Docker containers |

#### Scenario B: Mobile Field Unit
**Use Case:** On-site skill verification

| Component | Technology |
|-----------|------------|
| Pose Estimation | MediaPipe Pose |
| 3D Reconstruction | Monocular depth (if single camera) or stereo |
| Action Recognition | Lightweight TSN or LSTM on skeleton |
| Cameras | 2× Rugged action cameras or phone cameras |
| Edge Compute | Laptop with RTX GPU or Jetson NX |
| Framework | TensorFlow Lite + MediaPipe |
| Deployment | Portable case with battery |

#### Scenario C: Cloud-Based Processing
**Use Case:** Large-scale assessment, historical analysis

| Component | Technology |
|-----------|------------|
| Pose Estimation | YOLO11 Pose (Large) |
| 3D Reconstruction | Cloud-based bundle adjustment |
| Action Recognition | Full Transformer architecture |
| Storage | Cloud object storage (S3/MinIO) |
| Compute | Kubernetes cluster with GPU nodes |
| Framework | PyTorch + Ray |
| Deployment | Microservices architecture |

### 6.2 Software Dependencies

```python
# Core stack
ultralytics>=8.0.0      # YOLO11 Pose
mediapipe>=0.10.0       # MediaPipe Pose
opencv-python>=4.8.0    # Image processing
numpy>=1.24.0           # Numerical computing
scipy>=1.11.0           # Scientific computing

# Deep learning
torch>=2.0.0            # PyTorch
torchvision>=0.15.0     # Vision utilities
tensorflow>=2.13.0      # TensorFlow (for MoveNet/MediaPipe)

# 3D processing
open3d>=0.17.0          # 3D visualization
cvkit                   # Camera calibration

# Action recognition
pytorchvideo            # Video models
mmaction2               # Action recognition toolkit

# Deployment
fastapi>=0.100.0        # API server
docker>=24.0.0          # Containerization
redis>=4.6.0            # Caching/queue
```

---

## 7. Implementation Roadmap

### Phase 1: MVP (Months 1-2)
- Single camera setup with YOLO11 Pose
- Basic skeleton extraction and visualization
- Simple action classification (rule-based)
- One trade (recommend starting with Steel Fixer)

### Phase 2: Multi-Camera (Months 3-4)
- 4-camera synchronized setup
- 3D pose triangulation
- Improved action recognition with SlowFast
- All three trades supported

### Phase 3: Production (Months 5-6)
- Edge deployment optimization
- Real-time skill scoring
- Dashboard and reporting
- Integration with certification system

### Phase 4: Scale (Months 7-12)
- Multiple assessment stations
- Cloud analytics and benchmarking
- Mobile field unit
- AI-powered coaching feedback

---

## 8. Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Occlusions** | Multi-camera setup; view fusion algorithms |
| **Lighting Variations** | HDR cameras; IR illuminators; adaptive preprocessing |
| **Worker Privacy** | Anonymization; local processing; consent protocols |
| **Environmental Conditions** | IP67 cameras; temperature-rated hardware |
| **Model Drift** | Regular retraining; domain adaptation techniques |
| **Calibration Errors** | Automated calibration checks; redundancy |

---

## 9. References

1. Ultralytics. (2024). YOLO11 Documentation. https://docs.ultralytics.com
2. Google. (2024). MediaPipe Pose. https://developers.google.com/mediapipe
3. Mahdavian, M., Loni, M., & Chen, M. (2024). Construction Worker Action Recognition as a Use-Case. arXiv:2410.01962.
4. Feichtenhofer, C., et al. (2019). SlowFast Networks for Video Recognition. ICCV.
5. Cao, Z., et al. (2017). OpenPose: Realtime Multi-Person 2D Pose Estimation. TPAMI.
6. Sarafianos, N., et al. (2016). 3D Human Pose Estimation: A Survey. arXiv.
7. Iskakov, K., et al. (2019). Learnable Triangulation of Human Pose. ICCV.

---

## Appendix A: Keypoint Definitions

### COCO Format (17 keypoints)
```
0:  nose
1:  left_eye
2:  right_eye
3:  left_ear
4:  right_ear
5:  left_shoulder
6:  right_shoulder
7:  left_elbow
8:  right_elbow
9:  left_wrist
10: right_wrist
11: left_hip
12: right_hip
13: left_knee
14: right_knee
15: left_ankle
16: right_ankle
```

### MediaPipe BlazePose (33 keypoints)
Includes COCO keypoints plus:
- Additional facial landmarks
- Hand landmarks (simplified)
- Foot landmarks (heel, foot index, pinky)

---

*Document Version: 1.0*  
*Next Review: March 2026*
