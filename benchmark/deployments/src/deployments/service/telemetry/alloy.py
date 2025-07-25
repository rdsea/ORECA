from subprocess import CalledProcessError

from deployments.applications.kubectl import KubeCtl
from deployments.paths import ALLOY_METADATA
from deployments.service.telemetry.telemetry_service import TelemetryService


class Alloy(TelemetryService):
    """Manages the deployment and teardown of the Alloy telemetry service."""

    def __init__(self):
        """Initialize the Alloy service manager."""
        super().__init__(ALLOY_METADATA)

    def _is_service_running(self) -> bool:
        """Check if Alloy is already running in the cluster."""
        command = (
            f"kubectl get pods -n {self.namespace} -l app.kubernetes.io/name=alloy-logs"
        )
        try:
            result = KubeCtl().exec_command(command)
            if "Running" in result:
                return True
        except CalledProcessError:
            return False
        return False
