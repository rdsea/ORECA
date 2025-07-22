import json
import os
import select
import socket
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from kubernetes import client
from loguru import logger
from observer import (
    get_pod_list,
    get_services_list,
    # monitor_config,
    # root_path,
)


class LokiAPI:
    def __init__(self, namespace: str, application_namespace: str):
        self.loki_namespace = namespace
        self.application_namespace = application_namespace
        self.port = 32000
        self.port_forward_process = None
        self.stop_event = threading.Event()
        self.start_port_forward()
        # self.client = PrometheusConnect(url, disable_ssl=True)
        self.loki_namespace = namespace
        self.pod_list, self.service_list = self.initialize_pod_and_service_lists()

        self.base_url = f"http://localhost:{self.port}"

    def initialize_pod_and_service_lists(self):
        k8s_client = client.CoreV1Api()
        pod_list = [
            pod
            for pod in get_pod_list(k8s_client, namespace=self.application_namespace)
            if not pod.startswith("loadgenerator-") and not pod.startswith("redis-cart")
        ]
        service_list = get_services_list(k8s_client, namespace=self.loki_namespace)
        return pod_list, service_list

    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("XXX.XXX.XXX.XXX", port)) == 0

    def print_output(self, stream):
        """Thread function to print output from a subprocess stream non-blockingly."""
        while not self.stop_event.is_set():
            ready, _, _ = select.select([stream], [], [], 0.1)
            if ready:
                try:
                    line = stream.readline()
                    if line:
                        print(line, end="")
                    else:
                        break
                except ValueError:
                    break

    def start_port_forward(self):
        """Starts port-forwarding to access Prometheus."""
        if self.port_forward_process and self.port_forward_process.poll() is None:
            logger.info("Port-forwarding already active.")
            return

        for attempt in range(3):
            if self.is_port_in_use(self.port):
                logger.info(
                    f"Port {self.port} is already in use. Attempt {attempt + 1} of 3. Retrying in 3 seconds..."
                )
                time.sleep(3)
                continue

            command = f"kubectl port-forward svc/loki-gateway {self.port}:80 -n {self.loki_namespace}"
            self.port_forward_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            thread_out = threading.Thread(
                target=self.print_output, args=(self.port_forward_process.stdout,)
            )
            thread_err = threading.Thread(
                target=self.print_output, args=(self.port_forward_process.stderr,)
            )
            thread_out.start()
            thread_err.start()

            time.sleep(3)  # Wait a bit for the port-forward to establish

            if self.port_forward_process.poll() is None:
                logger.info("Port forwarding established successfully.")
                break
            else:
                logger.info("Port forwarding failed. Retrying...")
        else:
            logger.error("Failed to establish port forwarding after multiple attempts.")

    def query_loki(self, query, start_time, end_time) -> dict | None:
        endpoint = f"{self.base_url}/loki/api/v1/query_range"

        payload = {"query": query, "start": start_time, "end": end_time}

        headers = {
            "Accept": "application/json",
            "X-Scope-OrgID": "1",  # Adjust as per your Loki setup
        }

        logger.info(f"Sending request to: {endpoint}")
        logger.info(f"Payload: {payload}")
        logger.info(f"Headers: {headers}")

        try:
            response = requests.get(endpoint, params=payload, headers=headers)
            logger.info(f"Status code: {response.status_code}")
            logger.info(
                f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}"
            )
            logger.info(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    json_response = response.json()
                    logger.info("Successfully parsed JSON response")
                    return json_response
                except json.JSONDecodeError:
                    logger.error(
                        "Received a 200 status, but response is not valid JSON"
                    )
                    logger.error(
                        f"First 500 characters of response: {response.text[:500]}"
                    )
            else:
                logger.error(
                    f"Received non-200 status code. Response text: {response.text[:500]}"
                )

            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {e}")
            return None

    def stop_port_forward(self):
        """Stops the kubectl port-forward command."""
        if self.port_forward_process:
            self.port_forward_process.terminate()
            self.port_forward_process.wait()
            self.stop_event.set()
            print("Port forwarding stopped.")

    def cleanup(self):
        """Cleanup resources like port-forwarding."""
        self.stop_port_forward()

    def query_loki_now(self):
        query = '{service_name="frontend-6785bdb768-rb6tk"}'
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        start_time = (datetime.now() - timedelta(minutes=300)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        end_time = current_time

        result = self.query_loki(query, start_time, end_time)

        if result:
            logger.debug("Response received and parsed as JSON")
            logger.info(json.dumps(result["data"]["result"], indent=2))
            return result
        else:
            logger.error("No valid result returned")

    def export_all_metrics(self, start_time, end_time, save_path):
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        pod_save_path = os.path.join(save_path, "pod")

        os.makedirs(pod_save_path, exist_ok=True)

        for pod in self.pod_list:
            file_path = os.path.join(pod_save_path, f"{pod}.csv")
            query = f'{{service_name="{pod}"}}'
            # print(file_path, query)
            result = self.query_loki(query, start_time, end_time)
            with open(file_path, "w") as f:
                json.dump(result, f, indent=2)

        self.cleanup()


if __name__ == "__main__":
    loki = LokiAPI("observe", "default")

    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    start_time = (datetime.now() - timedelta(minutes=300)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    end_time = current_time
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    loki.export_all_metrics(start_time, end_time, base_path / "data")
