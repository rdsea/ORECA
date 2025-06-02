from datetime import datetime

import cv2
import rclpy
import requests
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

# Replace with your actual FastAPI ingestion server endpoint
FASTAPI_ENDPOINT = "http://<server_ip>:5010/preprocessing"  # Example: http://localhost:8000/preprocessing


class ImageTransmitter(Node):
    def __init__(self):
        super().__init__("image_transmitter")

        self.subscription = self.create_subscription(
            Image,
            "camera",  # Update this if using a different topic
            self.image_callback,
            10,
        )

        self.bridge = CvBridge()
        self.get_logger().info("ImageTransmitter node started.")

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV BGR image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

            # Encode the image as JPEG
            success, img_encoded = cv2.imencode(".jpg", cv_image)
            if not success:
                self.get_logger().error("Failed to encode image.")
                return

            # Prepare headers
            timestamp = datetime.utcnow().isoformat()
            headers = {"Timestamp": timestamp}

            # Use 'multipart/form-data' for UploadFile compatibility
            files = {"file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")}

            # Send request to FastAPI `/preprocessing` endpoint
            response = requests.post(
                FASTAPI_ENDPOINT, files=files, headers=headers, timeout=10
            )

            if response.status_code == 200:
                self.get_logger().info("Image successfully sent.")
            else:
                self.get_logger().warn(
                    f"Failed to send image: {response.status_code} - {response.text}"
                )

        except Exception as e:
            self.get_logger().error(f"Exception while sending image: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ImageTransmitter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
