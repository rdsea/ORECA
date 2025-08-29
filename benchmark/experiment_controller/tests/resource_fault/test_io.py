from pathlib import Path

import pytest
import yaml
from experiment_controller.fault_controller.resource import (
    ResourcesChaosConfig,
)


@pytest.fixture()
def get_chaos_resource_io_config():
    config_path = Path(__file__).parent / "io_config.yaml"
    with open(config_path) as f:
        return ResourcesChaosConfig.model_validate(yaml.safe_load(f))


def test_load_io_config_from_yaml(get_chaos_resource_io_config):
    config = get_chaos_resource_io_config
    assert isinstance(config, ResourcesChaosConfig)
    assert config.io_chaos is not None
    assert config.io_chaos.action == "delay"
    assert config.io_chaos.path == "/data"
    assert config.io_chaos.percent == "100"
    assert config.io_chaos.methods is not None
    assert "read" in config.io_chaos.methods


def test_controller_apply_and_delete_io(get_chaos_resource_io_config):
    pass
    # config = get_chaos_resource_io_config
    # controller = ChaosResourceController(config)
    # controller.apply()
    # time.sleep(5)  # let the chaos run
    # controller.delete()
