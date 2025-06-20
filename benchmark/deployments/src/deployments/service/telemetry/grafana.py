# DEPRECATED: This module is deprecated because Grafana is now installed as part of the Prometheus chart.
# Do not use this class for new development.
from subprocess import CalledProcessError

from deployments.applications.kubectl import KubeCtl
from deployments.paths import GRAFANA_METADATA
from deployments.service.telemetry.telemetry_service import TelemetryService


class Grafana(TelemetryService):
    """
    DEPRECATED: Grafana is now installed as part of the Prometheus chart.
    This class is no longer needed and will be removed in the future.
    """

    def __init__(self):
        super().__init__(GRAFANA_METADATA)

    def _is_service_running(self) -> bool:
        """Check if Alloy is already running in the cluster."""
        command = (
            f"kubectl get pods -n {self.namespace} -l app.kubernetes.io/name=grafana"
        )
        try:
            result = KubeCtl().exec_command(command)
            if "Running" in result:
                return True
        except CalledProcessError:
            return False
        return False
