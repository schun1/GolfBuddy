from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import mediapipe as mp
from pathlib import Path
import uuid
import subprocess
import time
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Cleanup old files to prevent disk from filling up
def cleanup_old_files():
    """Delete files older than 2 hours"""
    while True:
        time.sleep(1800)  # Run every 30 minutes
        try:
            current_time = time.time()
            for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    if os.path.isfile(filepath):
                        # Delete files older than 2 hours
                        if os.path.getmtime(filepath) < current_time - 7200:
                            os.remove(filepath)
                            print(f"Cleaned up old file: {filepath}")
        except Exception as e:
            print(f"Cleanup error: {str(e)}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# Initialize MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def convert_to_browser_compatible(input_path, output_path):
    """Convert video to H.264 MP4 using FFmpeg for maximum browser compatibility"""
    try:
        # Use FFmpeg to convert to H.264 with web-friendly settings
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',          # H.264 codec
            '-preset', 'fast',           # Encoding speed
            '-crf', '23',                # Quality (lower = better, 23 is default)
            '-pix_fmt', 'yuv420p',       # Pixel format for compatibility
            '-movflags', '+faststart',   # Enable streaming
            '-y',                        # Overwrite output file
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            return False

        print(f"Video converted successfully: {output_path}")
        return True

    except FileNotFoundError:
        print("FFmpeg not found. Please install FFmpeg.")
        return False
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        return False

def get_video_rotation(input_path):
    """Get video rotation from metadata using FFprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream_tags=rotate',
            '-of', 'default=nw=1:nk=1',
            input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        rotation = result.stdout.strip()
        return int(rotation) if rotation else 0
    except:
        return 0

def rotate_frame(frame, rotation):
    """Rotate frame based on rotation angle"""
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame

def process_video_with_pose(input_path, output_path, manual_rotation=None):
    """Process video and add pose overlay"""
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.8
    )

    # Use manual rotation if provided, otherwise detect from metadata
    if manual_rotation is not None:
        rotation = manual_rotation
        print(f"Using manual rotation: {rotation} degrees")
    else:
        rotation = get_video_rotation(input_path)
        print(f"Detected rotation from metadata: {rotation} degrees")

    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise Exception(f"Failed to open video file: {input_path}")

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Ensure fps is valid
    if fps <= 0:
        fps = 30  # Default to 30fps if detection fails

    # Adjust dimensions if video is rotated 90 or 270 degrees
    if rotation in [90, 270]:
        width, height = height, width
        print(f"Adjusted for rotation: {width}x{height}")

    print(f"Video properties: {width}x{height} @ {fps}fps")

    # Define codec and create VideoWriter - use H.264 for better browser compatibility
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not out.isOpened():
        # Fallback to mp4v if avc1 fails
        print("avc1 codec failed, trying mp4v...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Rotate frame if needed
        if rotation != 0:
            frame = rotate_frame(frame, rotation)

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = pose.process(frame_rgb)

        # Draw pose landmarks on frame
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )

        out.write(frame)
        frame_count += 1

        if frame_count % 30 == 0:
            print(f"Processed {frame_count}/{total_frames} frames")

    cap.release()
    out.release()
    pose.close()

    print(f"Processing complete: {output_path}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get manual rotation if provided
    manual_rotation = request.form.get('rotation')
    if manual_rotation:
        manual_rotation = int(manual_rotation)
    else:
        manual_rotation = None

    # Generate unique filename
    unique_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1]

    input_filename = f"{unique_id}_input{file_ext}"
    temp_output_filename = f"{unique_id}_temp.mp4"
    output_filename = f"{unique_id}_output.mp4"

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    temp_output_path = os.path.join(app.config['PROCESSED_FOLDER'], temp_output_filename)
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

    # Save uploaded file
    file.save(input_path)

    try:
        # Process video with pose detection
        print(f"Processing video: {input_filename}")
        process_video_with_pose(input_path, temp_output_path, manual_rotation)

        # Convert to browser-compatible H.264 format using FFmpeg
        print(f"Converting to browser-compatible format...")
        success = convert_to_browser_compatible(temp_output_path, output_path)

        if success:
            # FFmpeg conversion succeeded, clean up temp file
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
        else:
            # If FFmpeg conversion fails, just use the temp output
            print("FFmpeg conversion failed, using OpenCV output")
            if os.path.exists(temp_output_path):
                os.rename(temp_output_path, output_path)

        return jsonify({
            'success': True,
            'video_id': unique_id,
            'output_filename': output_filename
        })
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        # Clean up temp file if it exists
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/video/<filename>')
def get_video(filename):
    """Serve processed video"""
    video_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    return send_file(video_path, mimetype='video/mp4')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
