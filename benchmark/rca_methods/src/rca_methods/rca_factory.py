import random
from enum import Enum

from rca_methods.baro import Baro
from rca_methods.base_rca import BaseRCA
from rca_methods.causalai import CausalAI
from rca_methods.circa import Circa
from rca_methods.dummy_rca import DummyRCA

random.seed(42)


class RCAMethodEnum(Enum):
    DUMMY = "dummy"
    BARO = "baro"
    CIRCA = "circa"
    CAUSALAI = "causalai"


class RCAFactory:
    """A factory class for creating instances of various RCA (Root Cause Analysis) methods."""

    @staticmethod
    def create(rca_type: RCAMethodEnum) -> BaseRCA:
        """Creates and returns an instance of the specified RCA method.

        Args:
            rca_type (RCAMethodEnum): The type of RCA method to create.

        Returns:
            BaseRCA: An instance of the requested RCA method.

        Raises:
            ValueError: If an unsupported RCA type is provided.
        """
        if rca_type == RCAMethodEnum.DUMMY:
            return DummyRCA()
        elif rca_type == RCAMethodEnum.CIRCA:
            return Circa()
        elif rca_type == RCAMethodEnum.BARO:
            return Baro()
        elif rca_type == RCAMethodEnum.CAUSALAI:
            return CausalAI()
        raise ValueError(f"Unsupported RCA type: {rca_type}")
