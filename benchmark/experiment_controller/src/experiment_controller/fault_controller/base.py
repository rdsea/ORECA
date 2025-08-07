import logging

from experiment.config.anomaly_model import FaultConfig, NetworkFault, ResourceHog
from experiment.fault_controller.network import (
    ChaosNetworkController,
    NetworkChaosConfig,
)
from pydantic import ValidationError


class FaultController:
    """Injects and cleans up various types of faults based on the provided configuration."""

    def __init__(self, fault_config: FaultConfig):
        """Initialize the FaultController.

        Args:
            fault_config (FaultConfig): The configuration for the fault to be injected.
        """
        self.config = fault_config

    def inject(
        self,
        microservices: list[str] | None = None,
    ):
        """Injects the configured fault.

        Args:
            microservices (list[str], optional): A list of microservices to target. Defaults to None.
        """
        match self.config.fault_type:
            case ResourceHog.CPU:
                pass
            case ResourceHog.MEMORY:
                pass
            case ResourceHog.IO:
                pass
            case ResourceHog.SOCKET:
                pass
            case NetworkFault.DELAY | NetworkFault.LOSS:
                if isinstance(self.config.fault_specific_config, NetworkChaosConfig):
                    self.network_fault_controller = ChaosNetworkController(
                        self.config.fault_specific_config
                    )
                else:
                    try:
                        self.network_fault_controller = ChaosNetworkController(
                            NetworkChaosConfig.model_validate(
                                self.config.fault_specific_config
                            )
                        )
                    except ValidationError:
                        logging.error(
                            "Can't validate the fault_specific_config for network fault controller"
                        )
                self.network_fault_controller.apply()

    def clean(self):
        """Cleans up the injected fault."""
        match self.config.fault_type:
            case ResourceHog.CPU:
                pass
            case ResourceHog.MEMORY:
                pass
            case ResourceHog.IO:
                pass
            case ResourceHog.SOCKET:
                pass
            case NetworkFault.DELAY | NetworkFault.LOSS:
                if hasattr(self, "network_fault_controller"):
                    self.network_fault_controller.delete()
                else:
                    logging.error(
                        "Can't clean Network fault as network_fault_controller is not created yet"
                    )
