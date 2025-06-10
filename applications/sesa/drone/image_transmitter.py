import asyncio
from datetime import datetime
from enum import Enum

import aiohttp
import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

FASTAPI_ENDPOINT = (
    "http://<server_ip>:5010/preprocessing"  # Replace with actual endpoint
)


class Mode(Enum):
    IMAGE_TRANSMITTER = "image_transmitter"
    LOCAL_INFERENCE = "local_inference"
    SAVE_TO_LOCAL = "save_to_local"


class ImageTransmitter(Node):
    def __init__(self, mode: Mode):
        super().__init__("image_transmitter")

        self.subscription = self.create_subscription(
            Image,
            "camera",
            self.image_callback,
            10,
        )

        self.bridge = CvBridge()
        self.loop = asyncio.get_event_loop()
        self.get_logger().info("ImageTransmitter node started.")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            success, img_encoded = cv2.imencode(".jpg", cv_image)
            if not success:
                self.get_logger().error("Failed to encode image.")
                return

            timestamp = datetime.utcnow().isoformat()
            headers = {"Timestamp": timestamp}
            image_bytes = img_encoded.tobytes()

            # Run the async HTTP request in the event loop
            self.loop.run_until_complete(self.send_image(image_bytes, headers))

        except Exception as e:
            self.get_logger().error(f"Exception while processing image: {e}")

    def local_inference(self, data):
        """
        Callback function to do local inference instead of sending to server
        """

        from ultralytics import YOLO  # YOLO library

        model = YOLO("yolov8m.pt")
        # Display the message on the console
        self.get_logger().info("Receiving video frame")

        # Convert ROS Image message to OpenCV image
        current_frame = self.br.imgmsg_to_cv2(data, desired_encoding="bgr8")
        image = current_frame
        # Object Detection
        results = model.predict(image, classes=[0, 2])
        img = results[0].plot()
        # Show Results
        cv2.imshow("Detected Frame", img)
        cv2.waitKey(1)

    async def send_image(self, image_bytes, headers):
        try:
            data = aiohttp.FormData()
            data.add_field(
                "file", image_bytes, filename="frame.jpg", content_type="image/jpeg"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    FASTAPI_ENDPOINT, data=data, headers=headers, timeout=10
                ) as resp:
                    if resp.status == 200:
                        self.get_logger().info("Image successfully sent.")
                    else:
                        text = await resp.text()
                        self.get_logger().warn(
                            f"Failed to send image: {resp.status} - {text}"
                        )
        except Exception as e:
            self.get_logger().error(f"Exception in aiohttp request: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ImageTransmitter(Mode.IMAGE_TRANSMITTER)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
