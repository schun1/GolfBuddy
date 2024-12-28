#!/bin/bash

# Check if Conda is initialized
if ! command -v conda &> /dev/null; then
    echo "Conda is not initialized. Initializing..."
    conda init
    source ~/.zshrc  # or ~/.zshrc depending on your shell
fi

# Create and activate a new conda environment
conda create -n golfbuddy python=3.9 -y
conda activate golfbuddy

# Install PyTorch with CUDA support (adjust CUDA version as needed)
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

# Install computer vision and data processing libraries
pip install opencv-python mediapipe numpy pandas matplotlib
pip install jupyter notebook

# Install video processing libraries
pip install moviepy pafy youtube-dl

# Install additional utilities
pip install tqdm scipy