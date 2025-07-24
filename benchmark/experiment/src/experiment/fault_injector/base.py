from experiment.config.anomaly_model import FaultConfig, NetworkFault, ResourceHog


class FaultInjector:
    def __init__(self, testbed):
        self.testbed = testbed

    def inject(
        self,
        fault_config: FaultConfig,
        microservices: list[str] | None = None,
    ):
        match fault_config.fault_type:
            case ResourceHog.CPU:
                pass
            case ResourceHog.MEMORY:
                pass
            case ResourceHog.IO:
                pass
            case ResourceHog.SOCKET:
                pass
            case NetworkFault.DELAY:
                pass
            case NetworkFault.DROP:
                pass
        pass
