# Agentic-Stitcher Implementation Plan

## 1. Objective

Build the pipeline incrementally, starting with offline reconstruction from the supplied sensor recordings and expanding later to video, photos, damage detection, uncertainty calibration, and the final benchmark requirements.

The first practical milestone is:

> Given one capture folder, produce a dimensioned single-room floor plan and an evaluation report.

The supplied recordings are different scans of the same physical room. They are not three identical repetitions. One emphasizes the floor, one includes ceiling coverage, and one is a shorter room scan. Therefore, they can support robustness testing, but they cannot by themselves provide a perfect train/validation/test split or a true repeatability test.

## 2. Current data

| Folder | Approx. duration | Frames | Intended role |
|---|---:|---:|---|
| `single_scan_with_ceiling` | 215 s | 9,745 | Primary development capture; richest coverage |
| `single_scan_floor_only` | 115 s | 5,251 | Robustness check; floor-focused coverage |
| `single_room` | 37 s | 1,715 | Held-out smoke test; shorter/different trajectory |

Each folder contains:

- `depth/*.png`: 16-bit depth maps, 256×192
- `confidence/*.png`: 8-bit confidence maps
- `odometry.csv`: timestamps, frame IDs, poses, and per-frame intrinsics
- `imu.csv`: accelerometer and gyroscope readings
- `camera_matrix.csv`: camera intrinsic matrix
- `rgb.mp4`: RGB video

Depth units, coordinate conventions, quaternion conventions, and exact RGB-video timestamp alignment still need to be verified.

## 3. Dataset usage strategy

### Development capture

Use `single_scan_with_ceiling` while building the first pipeline because it has the most frames and includes ceiling coverage.

It may be used repeatedly during debugging and parameter development.

### Robustness capture

Use `single_scan_floor_only` to check whether the pipeline still produces a useful floor plan when ceiling information is missing or incomplete.

Do not tune every parameter against this folder and then call it an independent test.

### Held-out capture

Reserve `single_room` until the first version is working. Run it once with frozen parameters and record the result.

This is a useful held-out trajectory check, but it is not a true repeatability test because the room coverage and capture path differ.

### Missing benchmark data

To satisfy the full brief, additional data is still required:

- Laser/tape measurements for walls, openings, ceiling height, and floor area
- At least two captures of the same room at the same tier for repeatability
- A multi-room capture with at least three rooms and a connector
- 2–8 still photos per room for the photo tier
- A furnished room with labelled damage from two damage classes
- Room adjacency and opening annotations

## 4. Phase 0 — Freeze assumptions and create a data dictionary

### Input

All three supplied folders and the assignment Markdown file.

### Work

Document:

- Depth value units
- Camera coordinate axes
- World coordinate axes
- Quaternion order and rotation direction
- Position units
- IMU units and sensor frame
- RGB video frame rate and frame count
- Mapping between RGB frames, depth filenames, and odometry rows
- Which calibration source is authoritative: `camera_matrix.csv` or `odometry.csv`

### Expected output

- `DATA_DICTIONARY.md`
- A machine-readable capture manifest
- A list of confirmed facts and unresolved assumptions

### Evaluation

The validator must report:

- Matching depth, confidence, and odometry frame counts
- Contiguous frame IDs
- Monotonic timestamps
- Missing or duplicate files
- Intrinsic-matrix consistency
- RGB/depth frame alignment status

Gate: no unresolved assumption may be silently used in geometry calculations.

## 5. Phase 1 — Build the ingestion and validation layer

### Input

One capture directory, initially `single_scan_with_ceiling`.

### Work

Create a read-only ingestion layer that:

1. Loads the camera matrix.
2. Loads depth and confidence frames by frame ID.
3. Loads the matching odometry row.
4. Associates IMU samples by timestamp.
5. Validates image dimensions and data types.
6. Produces a normalized in-memory capture object or manifest.

### Expected output

- A validation report
- A normalized capture manifest
- Summary statistics for timestamps, depth, confidence, poses, and intrinsics

### Evaluation

Run the same validator on all three folders. It must complete without manual renaming or editing and must clearly identify any mismatch.

## 6. Phase 2 — Inspect and visualize sensor data

### Input

Validated capture data from Phase 1.

### Work

Create diagnostic visualizations for:

- Normalized depth maps
- Confidence maps
- RGB frames
- Camera trajectory
- Depth coverage over time
- Pose orientation and movement

Depth and confidence PNGs must be normalized for display. Their raw grayscale appearance is not a reliable visual interpretation.

### Expected output

- A small diagnostic report per capture
- Normalized depth/confidence previews
- Trajectory plots
- A record of invalid, zero, or low-confidence depth pixels

### Evaluation

Manually inspect several early, middle, and late frames. Confirm that:

- Depth values change as the camera moves.
- Confidence filtering removes clearly invalid measurements.
- The trajectory is plausible.
- The RGB and depth views are not obviously time-shifted.

## 7. Phase 3 — Reconstruct a single-room point cloud

### Input

One validated capture, camera intrinsics, depth, confidence, and odometry.

### Work

For selected frames:

1. Convert valid depth pixels into camera-space 3D points.
2. Remove zero and low-confidence values.
3. Transform points using odometry poses.
4. Downsample and remove obvious outliers.
5. Accumulate the points into a room-level point cloud.

This phase should initially use classical geometry and does not require a trained vision model.

### Expected output

- A point cloud for `single_scan_with_ceiling`
- A point cloud preview
- Point-count and coverage statistics
- Debug output showing camera trajectory and accumulated points

### Evaluation

Check whether stable walls, floor, and ceiling surfaces appear as coherent planes rather than smeared trails.

This is a qualitative gate first. Metric accuracy comes after collecting ground truth.

## 8. Phase 4 — Extract the single-room plan

### Input

Accumulated point cloud from Phase 3.

### Work

Estimate:

- Floor plane
- Ceiling plane, when visible
- Wall planes
- Wall intersections
- Floor boundary
- Candidate doors and windows
- Room orientation and 2D coordinate system

Calculate wall lengths, floor area, and ceiling height. Keep detections separate from measurements so uncertain or missing surfaces can be reported honestly.

### Expected output

- Dimensioned 2D floor-plan render
- Per-room geometry object
- Wall, opening, floor, and ceiling measurements
- Debug overlay on the point cloud

### Evaluation

Collect laser/tape measurements for the room and compare:

- Each wall length
- Floor area
- Ceiling height
- Each opening width and location

Report absolute error, percentage error, missed detections, and false detections.

Do not claim compliance with the assignment gates until physical ground truth exists.

## 9. Phase 5 — Cross-capture robustness evaluation

### Input

Frozen Phase 4 pipeline and all three captures.

### Work

Run the exact same parameters on:

1. Development capture: `single_scan_with_ceiling`
2. Floor-focused capture: `single_scan_floor_only`
3. Held-out capture: `single_room`

### Expected output

- Three independent plans
- A comparison report
- Failure cases caused by different coverage or missing ceiling information

### Evaluation

Compare plans qualitatively and, where physical measurements are available, quantitatively.

Because these are different trajectories rather than identical repeats, evaluate:

- Recovered room dimensions
- Room footprint consistency
- Surface coverage
- Stability of wall detections
- Failure under missing ceiling data

Do not label this as formal repeatability. Formal repeatability requires two captures of the same room at the same tier with comparable capture conditions.

## 10. Phase 6 — Multi-room stitching and drift correction

### Input

A new benchmark capture containing at least three rooms and a connector.

### Work

Implement:

- Room-level coordinate frames
- Loop closure or pose-graph optimization
- Plane- or wall-based alignment
- Room adjacency detection
- Overlap and collision checks

### Expected output

- Whole-property stitched plan
- Correct room adjacency
- Room-to-room dimensions
- Drift-corrected trajectory
- Drift-on/drift-off ablation result

### Evaluation

Measure:

- Room overlap errors
- Adjacency correctness
- Overall footprint error
- Accumulated drift
- Improvement from drift correction

## 11. Phase 7 — Video and photo tiers

### Video input

Use `rgb.mp4` without depth or odometry as the initial video-tier input. Depth and odometry may be retained as reference data for analysis, but should not be used by the RGB-only pipeline.

### Photo input

Collect 2–8 actual still photos per room. Extracted video frames may be used for early experimentation, but should not automatically be treated as valid photo-tier benchmark data.

### Expected output

Both tiers must eventually produce the same output contract as the LiDAR tier, with wider and honestly calibrated error intervals.

### Evaluation

Use the same physical room measurements and compare each tier separately. Do not mix results from the tiers when calculating accuracy.

## 12. Phase 8 — Damage and concealed-damage modules

### Input

RGB images/video containing staged damage, plus annotations for damage class and extent.

### Work

Detect and measure:

- Damage class
- Surface affected
- Pixel or 3D region
- Metric extent
- Concealed-damage trigger

Pretrained vision models are allowed. Training from scratch is not required. Fine-tuning is optional and depends on the amount of labelled data collected.

### Expected output

- Damage regions overlaid on RGB/plan views
- Damage class and metric extent
- Concealed-damage flag
- Human-readable rule explaining the flag
- Confidence and known limitations

### Evaluation

Compare detections against labelled damage regions and calculate missed detections, false detections, classification errors, and measurement errors.

## 13. Phase 9 — Uncertainty calibration and final packaging

### Input

Results from all tiers and measured ground truth.

### Work

Calibrate confidence intervals using actual validation errors. A model confidence score alone is not sufficient.

Package:

- One-command-per-capture runner
- JSON outputs
- Rendered plans
- Reproduction instructions
- Device matrix
- Capture protocol
- Compliance matrix
- Benchmark report
- Before/after fix-loop bundle
- Technical report of at most six pages

### Evaluation

Run the pipeline on a clean machine and verify that the reported numbers regenerate from the raw inputs. Then perform the unseen walk-in test when a suitable phone is available.

## 14. Immediate next action

Do not begin with machine learning or damage detection.

Start with Phase 0 and Phase 1:

1. Confirm depth units and coordinate conventions.
2. Build the data dictionary.
3. Validate all three captures.
4. Use `single_scan_with_ceiling` for the first reconstruction.
5. Reserve `single_room` for a frozen-parameter check.

The first success criterion is a reproducible single-room point cloud and floor plan, not the complete assignment.
