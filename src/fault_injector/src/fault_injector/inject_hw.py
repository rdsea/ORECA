"""Inject faults at the hardware layer."""

from fault_injector.base import FaultInjector


class HWFaultInjector(FaultInjector):
    def _inject(self, microservices: list[str], fault_type: str):
        return NotImplementedError

    ############# FAULT LIBRARY ################

    # H.1
    def hw_bug(self):
        return NotImplementedError

    ############# HELPER FUNCTIONS ################
