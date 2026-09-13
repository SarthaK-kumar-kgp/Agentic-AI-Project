# Phase 6 — Multi-room stitching prototype

## Goal

Phase 6 uses the full `single_scan_with_ceiling` capture as a first multi-room experiment.

The camera trajectory shows a long walk with revisited areas. This phase turns that trajectory into a simple pose graph and finds places where the camera came close to an earlier location. Those places are possible loop closures and can later help reduce drift.

This is the first Phase 6 prototype. It does not yet claim to know the exact room boundaries because no room-transition labels were supplied.

```text
Odometry trajectory
        ↓
Sample camera poses
        ↓
Find non-neighbor poses that come close again
        ↓
Build a provisional pose graph
        ↓
Mark candidate turning/transition regions
        ↓
Create diagnostic images and JSON/CSV outputs
```

## Input

The script reads:

- `single_scan_with_ceiling/odometry.csv`
- Phase 1's capture loader

The RGB video is not automatically used for room labels in this prototype. The video can later help us manually confirm which candidate frame belongs to which room.

## Important terminology

### Pose graph

A pose graph is a set of camera locations connected by motion constraints.

- A **node** is a sampled camera pose.
- A **consecutive edge** connects neighboring poses from odometry.
- A **loop-closure edge** connects two non-neighbor poses that appear to revisit the same place.

If the same physical area is seen again, the loop-closure information can eventually correct accumulated drift.

### Candidate loop closure

This phase only finds candidates from nearby odometry positions. It does not yet prove that the two views see the same geometry. A later step must verify each candidate using depth registration or visual matching.

### Candidate transition

A sharp trajectory turn may happen near a doorway or room transition, but it may also be a normal movement inside a room. Therefore, turning points are hints for inspection, not room labels.

## Expected outputs

- `phase_6_report.json`: graph statistics and candidate events
- `pose_graph.csv`: sampled nodes and their graph coordinates
- `loop_closure_candidates.csv`: non-neighbor pose pairs that came close again
- `turning_point_candidates.csv`: large trajectory-turn candidates
- `trajectory_pose_graph.png`: trajectory with loop-closure edges
- `trajectory_turning_points.png`: trajectory with candidate turns

The CSV keeps all retained loop candidates, while the pose-graph image draws only the closest 80 candidates so the graph remains readable.

## Current verification result

The 500 odometry-based loop candidates were checked against the actual depth clouds. This was an independent diagnostic run using the Phase 1 loader and Phase 3 depth projection.

- 101 candidates showed moderate geometric support.
- 6 candidates showed strong geometric support.
- 399 candidates were not reliable enough to use.

The strong candidates were:

| Earlier frame | Later frame | Depth-registration RMSE |
|---:|---:|---:|
| 2760 | 7530 | 9.7 cm |
| 5040 | 9600 | 8.3 cm |
| 4560 | 9120 | 9.8 cm |
| 3720 | 8400 | 8.0 cm |
| 3720 | 8430 | 3.9 cm |
| 2790 | 7560 | 8.7 cm |

The strongest pair is frame `3720 → 8430`. Its depth-cloud RMSE improved from approximately 48.5 cm before registration to 3.9 cm after registration, with all sampled source points finding a close target point.

This confirms that the long capture contains genuine revisited geometry and is suitable for a Phase 6 loop-closure experiment. These pairs are still called candidates because depth-only matching can occasionally align to a large flat surface by accident. The next step is to use only the validated candidates as loop-closure edges in a pose-graph optimizer and measure whether global drift decreases.

## Phase 6B — Pose-graph optimization result

Phase 6B was implemented using the six depth-verified candidates as inputs. A further safety check rejected loop matches with large pose corrections, leaving two loop edges for optimization:

- `5040 → 9600`
- `3720 → 8430`

Their loop translation errors decreased from approximately 1.19 m and 0.88 m to approximately 0.04 cm each after optimization. This shows that the graph can satisfy the selected loop constraints.

However, the global point cloud did not improve:

- Raw odometry dominant-plane ratio: `7.9%`
- Optimized pose-graph ratio: `4.4%`

Therefore, the raw odometry cloud remains the recommended reconstruction for now. The pose graph is useful diagnostically, but it should not yet replace the raw trajectory. The likely issue is that even the accepted loop measurements do not provide enough reliable global constraints for this depth-only, provisional-coordinate dataset.

The numerical solver also stopped at its function-evaluation limit rather than reporting full convergence, so this remains an experimental result rather than a final stitched map.

Phase 6B outputs are stored under `outputs_optimized/` and include the raw/optimized clouds, trajectory comparison, and loop-error comparison.

## How to evaluate it

This phase passes its basic diagnostic gate when:

- Pose nodes are ordered by frame ID.
- Consecutive edges form one connected chain.
- The trajectory is finite and has non-zero movement.
- Loop candidates are separated in time from their neighboring frames.
- The candidate list can be manually checked against the RGB video.

It does **not** yet prove:

- The number of rooms
- Room boundaries
- Correct global dimensions
- Correct loop closure alignment
- Final floor-plan accuracy

For those, we need to verify candidates against depth/RGB geometry and eventually compare the stitched result with the real floor layout.

## Run

From the `Agentic-Stitcher` folder:

```bash
python3 "phase 6/build_pose_graph.py"
```

The script uses the full `single_scan_with_ceiling` capture by default and writes files under:

```text
phase 6/outputs/
```

No GPU, trained vision model, or annotation dataset is required for this first prototype.
