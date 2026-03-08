#!/usr/bin/env python3
"""
Ceradon Sim — Camera Bridge

Subscribes to Gazebo simulated camera topic and re-publishes as:
1. RTSP stream (for AI systems that expect network cameras)
2. OpenCV-compatible local stream (for direct integration)

Your AI code connects to this the same way it connects to a real camera.
It doesn't know it's in a sim.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import numpy as np

# Configuration from environment
CAMERA_TOPIC = os.environ.get("CAMERA_TOPIC", "/gazebo/camera/image_raw")
RTSP_PORT = int(os.environ.get("RTSP_PORT", "8554"))
STREAM_NAME = os.environ.get("STREAM_NAME", "fpv")
RESOLUTION = os.environ.get("RESOLUTION", "640x480")
FPS = int(os.environ.get("FPS", "30"))

WIDTH, HEIGHT = map(int, RESOLUTION.split("x"))


class CameraBridge:
    """Bridges Gazebo camera topics to standard video streams."""

    def __init__(self):
        self.running = True
        self.frame = None
        self.frame_lock = threading.Lock()
        self.ffmpeg_proc = None

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        print("[CameraBridge] Shutting down...")
        self.running = False
        if self.ffmpeg_proc:
            self.ffmpeg_proc.terminate()

    def start_rtsp_server(self):
        """Start ffmpeg RTSP server that reads from stdin."""
        cmd = [
            "ffmpeg",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", RESOLUTION,
            "-r", str(FPS),
            "-i", "pipe:0",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-f", "rtsp",
            f"rtsp://0.0.0.0:{RTSP_PORT}/{STREAM_NAME}"
        ]

        print(f"[CameraBridge] Starting RTSP stream on rtsp://0.0.0.0:{RTSP_PORT}/{STREAM_NAME}")
        self.ffmpeg_proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )

    def subscribe_gazebo(self):
        """
        Subscribe to Gazebo camera topic.

        TODO: Implement Gazebo Transport subscription.
        For now, generates test frames so the pipeline can be validated.
        In production, this uses gz-transport Python bindings or
        reads from a shared memory buffer.
        """
        print(f"[CameraBridge] Subscribing to Gazebo topic: {CAMERA_TOPIC}")

        try:
            # Try to import Gazebo transport bindings
            from gz.transport import Node as GzNode
            from gz.msgs.image_pb2 import Image as GzImage

            node = GzNode()

            def on_image(msg):
                """Callback for Gazebo camera images."""
                frame = np.frombuffer(msg.data, dtype=np.uint8)
                frame = frame.reshape((msg.height, msg.width, 3))
                with self.frame_lock:
                    self.frame = frame

            node.subscribe(GzImage, CAMERA_TOPIC, on_image)
            print("[CameraBridge] Connected to Gazebo camera topic")

            while self.running:
                time.sleep(0.01)

        except ImportError:
            print("[CameraBridge] Gazebo transport not available — running in test mode")
            print("[CameraBridge] Generating synthetic test frames")
            self._generate_test_frames()

    def _generate_test_frames(self):
        """Generate test frames with a moving target for pipeline validation."""
        frame_count = 0
        target_x, target_y = WIDTH // 2, HEIGHT // 2
        dx, dy = 3, 2

        while self.running:
            # Create frame with gradient background
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            frame[:, :, 0] = 40   # Dark blue background
            frame[:, :, 1] = 60
            frame[:, :, 2] = 30

            # Moving target (red square)
            target_x += dx
            target_y += dy
            if target_x <= 30 or target_x >= WIDTH - 30:
                dx = -dx
            if target_y <= 30 or target_y >= HEIGHT - 30:
                dy = -dy

            # Draw target
            x1, y1 = max(0, target_x - 20), max(0, target_y - 20)
            x2, y2 = min(WIDTH, target_x + 20), min(HEIGHT, target_y + 20)
            frame[y1:y2, x1:x2, 2] = 255  # Red square

            # Add frame counter text area
            frame[10:30, 10:200, :] = 80
            # (Text rendering would need cv2, keeping it simple)

            with self.frame_lock:
                self.frame = frame

            frame_count += 1
            time.sleep(1.0 / FPS)

    def stream_frames(self):
        """Push frames to ffmpeg RTSP server."""
        while self.running:
            with self.frame_lock:
                frame = self.frame

            if frame is not None and self.ffmpeg_proc and self.ffmpeg_proc.stdin:
                try:
                    self.ffmpeg_proc.stdin.write(frame.tobytes())
                except BrokenPipeError:
                    print("[CameraBridge] RTSP pipe broken, restarting...")
                    self.start_rtsp_server()

            time.sleep(1.0 / FPS)

    def run(self):
        """Main entry point."""
        print("=" * 50)
        print("  Ceradon Sim — Camera Bridge")
        print(f"  Resolution: {RESOLUTION} @ {FPS}fps")
        print(f"  RTSP: rtsp://localhost:{RTSP_PORT}/{STREAM_NAME}")
        print(f"  Gazebo Topic: {CAMERA_TOPIC}")
        print("=" * 50)

        self.start_rtsp_server()

        # Run Gazebo subscriber in background thread
        sub_thread = threading.Thread(target=self.subscribe_gazebo, daemon=True)
        sub_thread.start()

        # Stream frames to RTSP in main thread
        self.stream_frames()


if __name__ == "__main__":
    bridge = CameraBridge()
    bridge.run()
