from subprocess import CalledProcessError

from deployments.applications.kubectl import KubeCtl
from deployments.paths import JAEGER_METADATA
from deployments.service.telemetry.telemetry_service import TelemetryService


class Jaeger(TelemetryService):
    """Manages the deployment and teardown of the Jaeger tracing service."""

    def __init__(self):
        """Initialize the Jaeger service manager."""
        super().__init__(JAEGER_METADATA)

    def _is_service_running(self) -> bool:
        """Check if Jaeger is already running in the cluster."""
        command = (
            f"kubectl get pods -n {self.namespace} -l app.kubernetes.io/name=jaeger"
        )
        try:
            result = KubeCtl().exec_command(command)
            if "Running" in result:
                return True
        except CalledProcessError:
            return False
        return False
