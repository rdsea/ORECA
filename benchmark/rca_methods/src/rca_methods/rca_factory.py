import random

from rca_methods.baro import Baro
from rca_methods.base_rca import BaseRCA
from rca_methods.circa import Circa
from rca_methods.dummy_rca import DummyRCA

random.seed(42)


class RCAFactory:
    @staticmethod
    def create(rca_type: str) -> BaseRCA:
        if rca_type == "dummy":
            return DummyRCA()
        elif rca_type == "circa":
            return Circa()
        elif rca_type == "baro":
            return Baro()
        raise ValueError(f"Unsupported RCA type: {rca_type}")
