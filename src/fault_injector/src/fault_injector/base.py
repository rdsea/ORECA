import time


class FaultInjector:
    def __init__(self, testbed):
        self.testbed = testbed

    def inject(
        self,
        fault_type: str,
        microservices: list[str] | None = None,
        duration: str | None = None,
    ):
        if duration:
            self._invoke_method("inject", fault_type, microservices, duration)
        elif microservices:
            self._invoke_method("inject", fault_type, microservices)
        else:
            self._invoke_method("inject", fault_type)
        time.sleep(6)

    def recover(
        self,
        fault_type: str,
        microservices: list[str] | None = None,
    ):
        if microservices and fault_type:
            self._invoke_method("recover", fault_type, microservices)
        elif fault_type:
            self._invoke_method("recover", fault_type)
        time.sleep(6)

    def _invoke_method(self, action_prefix, *args):
        """helper: injects/recovers faults based on name"""
        method_name = f"{action_prefix}_{args[0]}"
        method = getattr(self, method_name, None)
        if method:
            method(*args[1:])
        else:
            print(f"Unknown fault type: {args[0]}")
