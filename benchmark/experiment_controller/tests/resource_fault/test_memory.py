import time

import pytest
import yaml
from experiment_controller.fault_controller.resource import (
    ChaosResourceController,
    ResourcesChaosConfig,
)


@pytest.fixture()
def get_chaos_resource_memory_config():
    with open("./memory_config.yaml") as f:
        return ResourcesChaosConfig.model_validate(yaml.safe_load(f))


def test_load_config_from_yaml(get_chaos_resource_memory_config):
    config = get_chaos_resource_memory_config
    assert isinstance(config, ResourcesChaosConfig)
    assert config.stress_memory and config.stress_memory.workers == 1
    assert config.stress_memory and config.stress_memory.size == "150MB"
    assert config.target.label_selectors == {"app": "preprocessing"}


def test_controller_apply_and_delete(get_chaos_resource_memory_config):
    config = get_chaos_resource_memory_config
    controller = ChaosResourceController(config)
    controller.apply()
    time.sleep(300)
    controller.delete()
