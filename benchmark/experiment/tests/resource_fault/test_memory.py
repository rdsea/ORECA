import time

import pytest
import yaml
from experiment.fault_injector.resource import ChaosStressInjector, StressChaosConfig


@pytest.fixture()
def get_chaos_resource_memory_config():
    with open("./memory_config.yaml") as f:
        return StressChaosConfig(**yaml.safe_load(f))


def test_load_config_from_yaml(get_chaos_resource_memory_config):
    config = get_chaos_resource_memory_config
    assert isinstance(config, StressChaosConfig)
    assert config.stress_memory and config.stress_memory.workers == 1
    assert config.stress_memory and config.stress_memory.size == "150MB"
    assert config.target.label_selectors == {"app": "preprocessing"}


def test_injector_apply_and_delete(get_chaos_resource_memory_config):
    config = get_chaos_resource_memory_config
    injector = ChaosStressInjector(config)
    injector.apply()
    time.sleep(300)
    injector.delete()
