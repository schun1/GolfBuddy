import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Frame:
    """Represents a single frame with its pose data"""
    frame_number: int
    image: np.ndarray
    landmarks: Optional[List[Tuple[float, float, float]]] = None
    
class GolfSwingProcessor:
    def __init__(self):
        # Initialize MediaPipe pose estimation
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # Use the most accurate model
            min_detection_confidence=0.5,
            min_tracking_confidence=0.8
        )
        
    def load_video(self, video_path: str) -> Tuple[int, int, int]:
        """
        Load video and return basic information
        Returns: (total_frames, width, height)
        """
        self.video_path = Path(video_path)
        self.cap = cv2.VideoCapture(str(video_path))
        
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return total_frames, width, height
    
    def process_frame(self, frame: np.ndarray) -> Optional[List[Tuple[float, float, float]]]:
        """
        Process a single frame and return pose landmarks
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.pose.process(frame_rgb)
        
        if results.pose_landmarks:
            # Extract 3D landmarks
            landmarks = [(landmark.x, landmark.y, landmark.z) 
                        for landmark in results.pose_landmarks.landmark]
            return landmarks, results.pose_landmarks
        return None, None
    
    def visualize_frame(self, frame: np.ndarray, pose_landmarks) -> np.ndarray:
        """
        Draw pose landmarks on frame
        """
        if pose_landmarks is None:
            return frame
        
        image = frame.copy()
        self.mp_drawing.draw_landmarks(
            image,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        return image
    
    def process_and_play_video(self, playback_speed=2.0):
        """
        Process the video and display the output with pose landmarks in real-time
        """
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Process frame to get pose landmarks
            landmarks, pose_landmarks = self.process_frame(frame)
            
            # Visualize landmarks on frame
            annotated_frame = self.visualize_frame(frame, pose_landmarks)
            
            # Display the frame
            cv2.imshow("Golf Swing Analysis", annotated_frame)
            
            # Adjust delay to control playback speed
            delay = max(int(10 / playback_speed), 1)  # Ensure delay is at least 1 ms
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    # Example usage
    processor = GolfSwingProcessor()
    
    # Replace with your video path
    video_path = "Daddy_driver_front.mp4"
    
    # Load video
    total_frames, width, height = processor.load_video(video_path)
    print(f"Loaded video: {total_frames} frames, {width}x{height}")
    
    # Process and play video
    processor.process_and_play_video()

if __name__ == "__main__":
    main()