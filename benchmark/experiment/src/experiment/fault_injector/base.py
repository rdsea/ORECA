import logging

from pydantic import ValidationError

from experiment.config.anomaly_model import FaultConfig, NetworkFault, ResourceHog
from experiment.fault_injector.network import ChaosNetworkInjector, NetworkChaosConfig


class FaultInjector:
    def __init__(self, fault_config: FaultConfig):
        self.config = fault_config

    def inject(
        self,
        microservices: list[str] | None = None,
    ):
        match self.config.fault_type:
            case ResourceHog.CPU:
                pass
            case ResourceHog.MEMORY:
                pass
            case ResourceHog.IO:
                pass
            case ResourceHog.SOCKET:
                pass
            case NetworkFault.DELAY | NetworkFault.DROP:
                if isinstance(self.config.fault_specific_config, NetworkChaosConfig):
                    self.network_fault_injector = ChaosNetworkInjector(
                        self.config.fault_specific_config
                    )
                else:
                    try:
                        self.network_fault_injector = ChaosNetworkInjector(
                            NetworkChaosConfig.model_validate(
                                self.config.fault_specific_config
                            )
                        )
                    except ValidationError:
                        logging.error(
                            "Can't validate the fault_specific_config for network fault injector"
                        )
                self.network_fault_injector.apply()

    def clean(self):
        match self.config.fault_type:
            case ResourceHog.CPU:
                pass
            case ResourceHog.MEMORY:
                pass
            case ResourceHog.IO:
                pass
            case ResourceHog.SOCKET:
                pass
            case NetworkFault.DELAY | NetworkFault.DROP:
                if hasattr(self, "network_fault_injector"):
                    self.network_fault_injector.delete()
                else:
                    logging.error(
                        "Can't clean Network fault as network_fault_injector is not created yet"
                    )
