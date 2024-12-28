import cv2
import torch
import mediapipe as mp
import numpy as np

def test_environment():
    # Test CUDA availability
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
    # Test OpenCV
    cap = cv2.VideoCapture(0)  # Try to open webcam
    if cap.isOpened():
        print("OpenCV working: Camera accessible")
        cap.release()
    else:
        print("OpenCV working: Camera not accessible (but library loaded)")
    
    # Test MediaPipe
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    print("MediaPipe pose estimation model loaded successfully")

    return "Environment setup complete!"

if __name__ == "__main__":
    print(test_environment())