# Automatic Video Sync Using Pose Estimation

## Overview
Use MediaPipe pose landmarks to automatically align golf swing videos by detecting key swing positions.

## Approach 1: Key Pose Detection (Recommended)

### Concept
Identify key swing positions (address, top of backswing, impact, follow-through) and use them as sync points.

### Implementation Steps

1. **Extract Key Poses During Processing** (Modify `app.py`)
   ```python
   def detect_swing_key_frames(landmarks_sequence):
       """
       Analyze pose landmarks to find key swing positions
       Returns: dict with frame numbers for each key position
       """
       key_frames = {
           'address': None,
           'backswing_top': None,
           'impact': None,
           'follow_through': None
       }

       # Example: Detect impact position (arms extended, club at ball)
       # Look for when hands are lowest and moving fastest
       for i, landmarks in enumerate(landmarks_sequence):
           left_wrist = landmarks[15]  # MediaPipe landmark index
           right_wrist = landmarks[16]

           # Calculate wrist height and velocity
           avg_wrist_y = (left_wrist[1] + right_wrist[1]) / 2

           # Detect impact: wrists at lowest point in downswing
           if is_impact_position(landmarks):
               key_frames['impact'] = i

       return key_frames
   ```

2. **Identify Swing Phases**
   - **Address**: Body relatively still, club behind ball
     - Check shoulder rotation angle near 0°
     - Hands positioned low

   - **Top of Backswing**: Maximum shoulder rotation
     - Calculate angle between shoulders and hips
     - Detect when left shoulder (for right-handed) is lowest

   - **Impact**: Club meets ball
     - Wrists at lowest point
     - Maximum downward velocity
     - Hips rotated toward target

   - **Follow-through**: Arms extended after impact
     - Right shoulder (for right-handed) at lowest point
     - Maximum club velocity

3. **Calculate Angles and Velocities**
   ```python
   def calculate_shoulder_rotation(landmarks):
       left_shoulder = landmarks[11]
       right_shoulder = landmarks[12]
       left_hip = landmarks[23]
       right_hip = landmarks[24]

       # Calculate shoulder line angle
       shoulder_angle = math.atan2(
           right_shoulder[1] - left_shoulder[1],
           right_shoulder[0] - left_shoulder[0]
       )

       # Calculate hip line angle
       hip_angle = math.atan2(
           right_hip[1] - left_hip[1],
           right_hip[0] - left_hip[0]
       )

       # Rotation difference
       rotation = shoulder_angle - hip_angle
       return math.degrees(rotation)
   ```

4. **Store Metadata with Videos**
   - Save key frame indices in JSON file alongside video
   ```python
   metadata = {
       'video_id': unique_id,
       'key_frames': {
           'address': 15,
           'backswing_top': 45,
           'impact': 78,
           'follow_through': 95
       },
       'total_frames': 150,
       'fps': 30
   }
   ```

5. **Frontend Auto-Sync**
   ```javascript
   function autoSyncVideos() {
       // Load metadata for both videos
       const video1Meta = loadMetadata(video1_id);
       const video2Meta = loadMetadata(video2_id);

       // Align videos at impact frame
       const video1ImpactTime = video1Meta.key_frames.impact / video1Meta.fps;
       const video2ImpactTime = video2Meta.key_frames.impact / video2Meta.fps;

       // Set both videos to impact position
       video1.currentTime = video1ImpactTime;
       video2.currentTime = video2ImpactTime;

       // Or calculate offset for synchronized playback
       const offset = video1ImpactTime - video2ImpactTime;
   }
   ```

## Approach 2: Dynamic Time Warping (DTW)

### Concept
Compare entire pose sequences and find optimal alignment, accounting for different swing speeds.

### Implementation
```python
import numpy as np
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

def align_videos_with_dtw(landmarks_seq1, landmarks_seq2):
    """
    Use DTW to find optimal alignment between two swing sequences
    """
    # Convert landmarks to feature vectors (e.g., joint angles)
    features1 = extract_features(landmarks_seq1)
    features2 = extract_features(landmarks_seq2)

    # Calculate DTW alignment
    distance, path = fastdtw(features1, features2, dist=euclidean)

    # path contains frame mappings: [(frame1_idx, frame2_idx), ...]
    return path

def extract_features(landmarks_sequence):
    """Extract key angles and positions as features"""
    features = []
    for landmarks in landmarks_sequence:
        # Example features:
        shoulder_rotation = calculate_shoulder_rotation(landmarks)
        hip_rotation = calculate_hip_rotation(landmarks)
        wrist_height = (landmarks[15][1] + landmarks[16][1]) / 2

        features.append([shoulder_rotation, hip_rotation, wrist_height])

    return np.array(features)
```

## Approach 3: Optical Flow + Pose (Hybrid)

Combine pose landmarks with optical flow to detect rapid movements (club swing).

### Key Benefits
- More robust to pose estimation errors
- Can detect club movement even if body landmarks are occluded

## Recommended Implementation Plan

### Phase 1: Basic Key Frame Detection
1. Modify `process_video_with_pose()` to extract landmarks for all frames
2. Implement `detect_swing_key_frames()` to find impact frame
3. Save metadata JSON file with video
4. Add "Auto-Sync" button in UI that aligns videos at impact

### Phase 2: Enhanced Detection
1. Detect all 4 key poses (address, backswing, impact, follow-through)
2. Let user choose which key pose to sync on
3. Add visual indicators on timeline showing key poses

### Phase 3: Full DTW Alignment
1. Implement DTW-based alignment
2. Calculate frame-by-frame mapping
3. Adjust playback speeds dynamically to maintain sync

## Code Locations to Modify

1. **Backend (`app.py`)**
   - Line 83: Modify `process_video_with_pose()` to extract and analyze landmarks
   - Add new function: `detect_swing_key_frames()`
   - Add new endpoint: `/api/sync-videos` to calculate alignment

2. **Frontend (`templates/index.html`)**
   - Add "Auto-Sync" button in controls section
   - Add metadata loading function
   - Add sync calculation and application function

## Additional Requirements

```txt
# Add to requirements.txt
fastdtw==0.3.4
scipy==1.11.4
```

## Estimated Effort
- **Phase 1 (Basic)**: 4-6 hours
- **Phase 2 (Enhanced)**: 6-8 hours
- **Phase 3 (Full DTW)**: 10-15 hours

## Challenges & Solutions

**Challenge**: Different camera angles affect landmark positions
**Solution**: Use relative angles (shoulder-to-hip rotation) rather than absolute positions

**Challenge**: Different swing speeds
**Solution**: DTW handles this naturally; for key frame approach, only sync at specific poses

**Challenge**: Partial body occlusion
**Solution**: Use multiple key poses and pick the most reliable one based on landmark confidence scores

## Testing Approach
1. Test with same golfer, different swings
2. Test with different golfers (different heights/body proportions)
3. Test with different camera angles
4. Validate against manual sync to measure accuracy
