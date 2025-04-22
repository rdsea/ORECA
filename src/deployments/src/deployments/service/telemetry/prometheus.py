from subprocess import CalledProcessError

from deployments.applications.kubectl import KubeCtl
from deployments.paths import PROMETHEUS_METADATA
from deployments.service.telemetry.telemetry_service import TelemetryService


class Prometheus(TelemetryService):
    def __init__(self):
        super().__init__(PROMETHEUS_METADATA)

    def _is_service_running(self) -> bool:
        """Check if Prometheus is already running in the cluster."""
        command = (
            f"kubectl get pods -n {self.namespace} -l app.kubernetes.io/name=prometheus"
        )
        try:
            result = KubeCtl().exec_command(command)
            if "Running" in result:
                return True
        except CalledProcessError:
            return False
        return False
