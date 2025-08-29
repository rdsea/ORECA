import time
from pathlib import Path

import pytest
import yaml
from experiment_controller.fault_controller.network import (
    ChaosNetworkController,
    NetworkChaosConfig,
)


@pytest.fixture()
def get_chaos_network_loss_config():
    config_path = Path(__file__).parent / "loss_config.yaml"
    with open(config_path) as f:
        return NetworkChaosConfig.model_validate(yaml.safe_load(f))


def test_load_config_from_yaml(get_chaos_network_loss_config):
    config = get_chaos_network_loss_config
    assert isinstance(config, NetworkChaosConfig)
    assert config.loss and config.loss.loss == "10"
    assert config.loss and config.loss.correlation == "0.5"
    assert config.target.label_selectors == {"app": "preprocessing"}


def test_controller_apply_and_delete(get_chaos_network_loss_config):
    config = get_chaos_network_loss_config
    controller = ChaosNetworkController(config)
    controller.apply()
    time.sleep(5)
    controller.delete()
