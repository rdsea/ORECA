import random

from rca_methods.baro import Baro
from rca_methods.base_rca import BaseRCA
from rca_methods.circa import Circa
from rca_methods.dummy_rca import DummyRCA

random.seed(42)


class RCAFactory:
    """A factory class for creating instances of various RCA (Root Cause Analysis) methods."""

    @staticmethod
    def create(rca_type: str) -> BaseRCA:
        """Creates and returns an instance of the specified RCA method.

        Args:
            rca_type (str): The type of RCA method to create (e.g., "dummy", "circa", "baro").

        Returns:
            BaseRCA: An instance of the requested RCA method.

        Raises:
            ValueError: If an unsupported RCA type is provided.
        """
        if rca_type == "dummy":
            return DummyRCA()
        elif rca_type == "circa":
            return Circa()
        elif rca_type == "baro":
            return Baro()
        raise ValueError(f"Unsupported RCA type: {rca_type}")
