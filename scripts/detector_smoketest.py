#!/usr/bin/env python3
"""
Detector Smoke Test Script

Tests if the configured detector backend can initialize properly.
Used to verify dependencies before running the full pipeline.

Exit codes:
  0 - Backend initialized successfully
  1 - Backend initialization failed
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def print_config():
    """Print effective detector configuration."""
    print("\n" + "=" * 60)
    print("DETECTOR CONFIGURATION")
    print("=" * 60)

    config = {
        "DETECTOR_BACKEND": settings.DETECTOR_BACKEND,
        "DETECTION_CONFIDENCE_THRESHOLD": settings.DETECTION_CONFIDENCE_THRESHOLD,
        "FRAME_EXTRACTION_FPS": settings.FRAME_EXTRACTION_FPS,
    }

    # Add backend-specific config
    if settings.DETECTOR_BACKEND in ["yolo", "yolo_ffmpeg"]:
        config.update({
            "YOLO_MODEL": os.getenv("YOLO_MODEL", "keremberke/yolov8n-license-plate"),
            "DETECT_CONFIDENCE": os.getenv("DETECT_CONFIDENCE", "0.30"),
            "DEVICE": os.getenv("DEVICE", "auto-detect"),
        })

        if settings.DETECTOR_BACKEND == "yolo_ffmpeg":
            config.update({
                "MIN_BOX_WIDTH": os.getenv("MIN_BOX_WIDTH", "20"),
                "MIN_BOX_HEIGHT": os.getenv("MIN_BOX_HEIGHT", "10"),
            })

    elif settings.DETECTOR_BACKEND == "remote":
        config.update({
            "REMOTE_INFERENCE_URL": settings.REMOTE_INFERENCE_URL,
            "AUTH_CONFIGURED": bool(settings.REMOTE_INFERENCE_TOKEN),
        })

    for key, value in config.items():
        print(f"  {key:35s} = {value}")

    print("=" * 60 + "\n")


def test_backend_init():
    """Test if the detector backend can initialize."""
    print("Testing detector backend initialization...")
    print(f"Backend: {settings.DETECTOR_BACKEND}\n")

    try:
        if settings.DETECTOR_BACKEND == "mock":
            print("✓ Mock backend selected (no dependencies required)")
            from src.detectors.mock_detector import process_video
            print("✓ Mock detector imported successfully")
            return True

        elif settings.DETECTOR_BACKEND == "yolo":
            print("Testing YOLO backend dependencies...")
            try:
                import cv2
                print(f"✓ cv2 imported (version: {cv2.__version__})")
            except ImportError as e:
                print(f"✗ cv2 import failed: {e}")
                return False

            try:
                import easyocr
                print("✓ easyocr imported")
            except ImportError as e:
                print(f"✗ easyocr import failed: {e}")
                return False

            try:
                from ultralytics import YOLO
                print("✓ ultralytics imported")
            except ImportError as e:
                print(f"✗ ultralytics import failed: {e}")
                return False

            from src.detectors.yolo_easyocr_adapter import process_video
            print("✓ YOLO detector imported successfully")
            return True

        elif settings.DETECTOR_BACKEND == "yolo_ffmpeg":
            print("Testing YOLO+FFmpeg backend dependencies...")

            # Test ffmpeg availability (using shutil.which to avoid Replit timeout issues)
            import shutil
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                print(f"✓ ffmpeg found at: {ffmpeg_path}")
                print("  (version check skipped for Replit compatibility)")
            else:
                print("✗ ffmpeg not found in PATH")
                print("  Install ffmpeg or add it to PATH")
                return False

            # Test Python dependencies
            try:
                import torch
                print(f"✓ torch imported (version: {torch.__version__})")
                print(f"  CUDA available: {torch.cuda.is_available()}")
            except ImportError as e:
                print(f"✗ torch import failed: {e}")
                print("  Hint: Torch not installed. Ensure workflows run 'pip install -r requirements.txt' before starting.")
                return False

            try:
                from ultralytics import YOLO
                print("✓ ultralytics imported")
            except ImportError as e:
                print(f"✗ ultralytics import failed: {e}")
                print("  Hint: Ultralytics not installed. Ensure workflows run 'pip install -r requirements.txt' before starting.")
                return False

            try:
                import easyocr
                print("✓ easyocr imported")
            except ImportError as e:
                print(f"✗ easyocr import failed: {e}")
                print("  Hint: EasyOCR not installed. Ensure workflows run 'pip install -r requirements.txt' before starting.")
                return False

            try:
                from PIL import Image
                import numpy as np
                print("✓ PIL and numpy imported")
            except ImportError as e:
                print(f"✗ PIL/numpy import failed: {e}")
                return False

            # Test detector import
            from src.detectors.yolo_easyocr_ffmpeg import process_video
            print("✓ YOLO+FFmpeg detector imported successfully")

            return True

        elif settings.DETECTOR_BACKEND == "remote":
            print("Testing remote inference backend...")

            # Check that URL is configured
            if not settings.REMOTE_INFERENCE_URL:
                print("✗ REMOTE_INFERENCE_URL is not set")
                print("  Set REMOTE_INFERENCE_URL to the inference service endpoint")
                return False

            print(f"✓ Remote URL configured: {settings.REMOTE_INFERENCE_URL}")

            # Test detector initialization (includes health check)
            try:
                from src.detectors.remote_inference import RemoteInferenceDetector
                print("  Initializing detector (includes health check)...")

                detector = RemoteInferenceDetector()
                print("✓ Remote inference detector initialized successfully")
                print("✓ Health check passed")

            except Exception as e:
                print(f"✗ Failed to initialize remote detector: {e}")
                print(f"  URL: {settings.REMOTE_INFERENCE_URL}")
                print("  Check that the service is running and accessible")
                print("  The service must expose GET /health endpoint")
                return False

            return True

        else:
            print(f"✗ Unknown backend: {settings.DETECTOR_BACKEND}")
            return False

    except Exception as e:
        print(f"\n✗ Backend initialization failed:")
        print(f"  Error: {e}")
        print(f"  Type: {type(e).__name__}")
        import traceback
        print("\nTraceback:")
        traceback.print_exc()
        return False


def main():
    """Main test routine."""
    print("\n" + "=" * 60)
    print("DETECTOR SMOKE TEST")
    print("=" * 60 + "\n")

    if settings.DETECTOR_BACKEND == "yolo_ffmpeg":
        print("!" * 60)
        print("! REAL DETECTOR MODE (YOLO + EasyOCR)")
        print("! Dependencies required: torch, ultralytics, easyocr, ffmpeg")
        print("!" * 60 + "\n")
    elif settings.DETECTOR_BACKEND == "yolo":
        print("!" * 60)
        print("! REAL DETECTOR MODE (YOLO + EasyOCR + cv2)")
        print("! Dependencies required: opencv-python, ultralytics, easyocr")
        print("!" * 60 + "\n")
    elif settings.DETECTOR_BACKEND == "remote":
        print("!" * 60)
        print("! REMOTE INFERENCE MODE")
        print("! Requires: Remote inference service running and accessible")
        print("!" * 60 + "\n")
    elif settings.DETECTOR_BACKEND == "mock":
        print("(Mock detector mode - no ML dependencies required)\n")

    # Print configuration
    print_config()

    # Test backend initialization
    success = test_backend_init()

    # Print result
    print("\n" + "=" * 60)
    if success:
        print("✓ SMOKE TEST PASSED")
        print("=" * 60 + "\n")
        print("The detector backend initialized successfully.")
        print("You can now run the worker or upload videos for processing.\n")
        return 0
    else:
        print("✗ SMOKE TEST FAILED")
        print("=" * 60 + "\n")
        print("The detector backend failed to initialize.")
        print("\nTroubleshooting:")
        print("  1. Check that all required dependencies are installed:")
        print("     pip install -r requirements.txt")
        print("  2. For yolo_ffmpeg backend, verify ffmpeg is installed:")
        print("     which ffmpeg")
        print("  3. Check the error messages above for specific issues")
        print("  4. Consider using DETECTOR_BACKEND=mock for testing\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
