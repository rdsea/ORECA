from subprocess import CalledProcessError

from deployments.applications.kubectl import KubeCtl
from deployments.paths import CHAOS_MESH_METADATA
from deployments.service.telemetry.telemetry_service import TelemetryService


class ChaosMesh(TelemetryService):
    def __init__(self):
        super().__init__(CHAOS_MESH_METADATA)

    def _is_service_running(self) -> bool:
        """Check if Chaos-mesh is already running in the cluster."""
        command = (
            f"kubectl get pods -n {self.namespace} -l app.kubernetes.io/name=chaos-mesh"
        )
        try:
            result = KubeCtl().exec_command(command)
            if "Running" in result:
                return True
        except CalledProcessError:
            return False
        return False
