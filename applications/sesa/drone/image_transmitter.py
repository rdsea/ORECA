import asyncio
from datetime import datetime

import aiohttp
import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

FASTAPI_ENDPOINT = (
    "http://<server_ip>:5010/preprocessing"  # Replace with actual endpoint
)


class ImageTransmitter(Node):
    def __init__(self):
        super().__init__("image_transmitter")

        self.subscription = self.create_subscription(
            Image,
            "camera",
            self.image_callback,
            10,
        )

        self.bridge = CvBridge()
        self.queue = asyncio.Queue(maxsize=10)  # Prevent memory overload
        self.loop = asyncio.get_event_loop()

        # Start background async task
        self.loop.create_task(self.image_sender())

        self.get_logger().info("ImageTransmitter node started.")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            success, img_encoded = cv2.imencode(".jpg", cv_image)
            if not success:
                self.get_logger().error("Failed to encode image.")
                return

            image_bytes = img_encoded.tobytes()
            timestamp = datetime.utcnow().isoformat()
            headers = {"Timestamp": timestamp}

            # Enqueue the image and headers (non-blocking)
            if not self.queue.full():
                self.loop.call_soon_threadsafe(
                    self.queue.put_nowait, (image_bytes, headers)
                )
            else:
                self.get_logger().warn("Image queue full, dropping frame.")

        except Exception as e:
            self.get_logger().error(f"Exception in image_callback: {e}")

    async def image_sender(self):
        async with aiohttp.ClientSession() as session:
            while rclpy.ok():
                try:
                    image_bytes, headers = await self.queue.get()

                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        image_bytes,
                        filename="frame.jpg",
                        content_type="image/jpeg",
                    )

                    async with session.post(
                        FASTAPI_ENDPOINT, data=data, headers=headers, timeout=10
                    ) as resp:
                        if resp.status == 200:
                            self.get_logger().info("Image sent successfully.")
                        else:
                            text = await resp.text()
                            self.get_logger().warn(
                                f"Failed to send image: {resp.status} - {text}"
                            )

                except Exception as e:
                    self.get_logger().error(f"Exception in image_sender: {e}")
