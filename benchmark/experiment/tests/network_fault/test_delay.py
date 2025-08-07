import time

import pytest
import yaml
from experiment.fault_injector.network import (
    ChaosNetworkInjector,
    NetworkChaosConfig,
)


@pytest.fixture()
def get_chaos_network_delay_config():
    with open("./delay_config.yaml") as f:
        return NetworkChaosConfig.model_validate(yaml.safe_load(f))


def test_load_config_from_yaml(get_chaos_network_delay_config):
    config = get_chaos_network_delay_config
    assert isinstance(config, NetworkChaosConfig)
    assert config.delay and config.delay.latency == "100ms"
    assert config.delay and config.delay.correlation == "0.5"
    assert config.delay and config.delay.jitter == "50ms"
    assert config.target.label_selectors == {"app": "preprocessing"}


def test_injector_apply_and_delete(get_chaos_network_delay_config):
    config = get_chaos_network_delay_config
    injector = ChaosNetworkInjector(config)
    injector.apply()
    time.sleep(30)
    injector.delete()
