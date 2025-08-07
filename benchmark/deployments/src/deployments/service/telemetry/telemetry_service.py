import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import CalledProcessError

import yaml

from deployments.applications.helm import Helm
from deployments.applications.kubectl import KubeCtl
from deployments.paths import HELM_CHARTS


class TelemetryService(ABC):
    """Abstract base class for all telemetry services."""

    def __init__(self, config_file: Path):
        """Initialize the TelemetryService.

        Args:
            config_file (Path): The path to the service's configuration file.
        """
        self.config_file = config_file
        self.name = None
        self.namespace = None
        self.helm_configs = {}
        self.pvc_config_file = None
        self.locally = False

        self.load_service_json()

    def load_service_json(self):
        """Load service metadata from the JSON configuration file."""
        with open(self.config_file) as file:
            metadata = json.load(file)

        self.name = metadata.get("Name")
        self.namespace = metadata.get("Namespace")
        self.helm_configs = metadata.get("Helm Config", {})
        self.locally = self.helm_configs.get("locally", False)

        if "Helm Config" in metadata:
            if "chart_path" in self.helm_configs:
                values = self.helm_configs["values"]
                self.helm_configs["values"] = str(HELM_CHARTS / values)
                if self.locally:
                    chart_path = self.helm_configs["chart_path"]
                    self.helm_configs["chart_path"] = str(HELM_CHARTS / chart_path)
                else:
                    self.repo_name = self.helm_configs.get("repo_name")
                    self.repo_url = self.helm_configs.get("repo_url")

        pvc = metadata.get("PersistentVolumeClaimConfig")
        if pvc:
            self.pvc_config_file = os.path.join(HELM_CHARTS, pvc)

    def get_service_json(self) -> dict:
        """Get service metadata in JSON format."""
        with open(self.config_file) as file:
            return json.load(file)

    def get_service_summary(self) -> str:
        """Get a summary of the service metadata in string format."""
        data = self.get_service_json()
        summary = (
            f"Telemetry Service Name: {data.get('Name', '')}\n"
            f"Namespace: {data.get('Namespace', '')}\n"
            f"Description: {data.get('Desc', '')}\n"
            f"Supported Operations:\n"
        )
        operations = "\n".join(
            [f"  - {op}" for op in data.get("Supported Operations", [])]
        )
        return summary + operations

    def deploy(self):
        """Deploy the telemetry service."""
        if self._is_service_running():
            print(f"{self.name} is already running. Skipping redeployment.")
            return

        self._delete_pv()
        Helm.uninstall(
            self.helm_configs["release_name"], self.helm_configs["namespace"]
        )

        if self.pvc_config_file:
            pv_name = self._get_pv_name_from_file(self.pvc_config_file)
            if not self._pv_exists(pv_name):
                self._apply_pv()

        if not self.locally:
            Helm.add_repo(self.repo_name, self.repo_url)
        Helm.install(
            release_name=self.helm_configs["release_name"],
            chart_path=self.helm_configs["chart_path"],
            namespace=self.helm_configs["namespace"],
            version=self.helm_configs.get("version"),
            values=self.helm_configs.get("values"),
            locally=self.helm_configs.get("locally", False),
        )
        Helm.assert_if_deployed(self.namespace)

    def teardown(self):
        """Teardown the telemetry service."""
        Helm.uninstall(
            self.helm_configs["release_name"], self.helm_configs["namespace"]
        )
        if self.pvc_config_file:
            self._delete_pv()

    def _apply_pv(self):
        """Apply the PersistentVolume configuration."""
        print(f"Applying PersistentVolume from {self.pvc_config_file}")
        KubeCtl().exec_command(
            f"kubectl apply -f {self.pvc_config_file} -n {self.namespace}"
        )

    def _delete_pv(self):
        """Delete the PersistentVolume."""
        if not self.pvc_config_file:
            return
        pv_name = self._get_pv_name_from_file(self.pvc_config_file)
        result = KubeCtl().exec_command(f"kubectl get pv {pv_name} --ignore-not-found")
        if result:
            print(f"Deleting PersistentVolume {pv_name}")
            KubeCtl().exec_command(f"kubectl delete pv {pv_name}")
        else:
            print(f"PersistentVolume {pv_name} not found. Skipping deletion.")

    def _get_pv_name_from_file(self, pv_config_file):
        """Get the PersistentVolume name from the configuration file."""
        with open(pv_config_file) as file:
            pv_config = yaml.safe_load(file)
            return pv_config["metadata"]["name"]

    def _pv_exists(self, pv_name: str) -> bool:
        """Check if a PersistentVolume exists."""
        try:
            result = KubeCtl().exec_command(f"kubectl get pv {pv_name}")
            if "No resources found" in result or "Error" in result:
                return False
        except CalledProcessError:
            return False
        return True

    @abstractmethod
    def _is_service_running(self) -> bool:
        """Abstract method to check if the telemetry service is running."""
        pass
