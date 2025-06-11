"""Inject faults at the application layer: Code, MongoDB, Redis, etc."""

from deployments.applications.kubectl import KubeCtl
from fault_injector.base import FaultInjector


class ApplicationFaultInjector(FaultInjector):
    def __init__(self, namespace: str):
        self.namespace = namespace
        self.kubectl = KubeCtl()


if __name__ == "__main__":
    namespace = "test-hotel-reservation"
    # microservices = ["geo"]
    microservices = ["mongodb-geo"]
    # fault_type = "misconfig_app"
    fault_type = "storage_user_unregistered"
    print("Start injection/recover ...")
    injector = ApplicationFaultInjector(namespace)
    injector._inject(fault_type, microservices)
    injector._recover(fault_type, microservices)
