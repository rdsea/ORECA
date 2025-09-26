import pathlib

import yaml
from experiment_controller.config.experiment_config import (
    RCAExperimentConfig,
)
from experiment_controller.experiment_controller import RCAExperiment
from experiment_controller.logger import logger
from experiment_controller.rca_evaluator import RCAEvaluator
from kubernetes import config, utils
from kubernetes.client import AutoscalingV2Api
from rca_methods.rca_factory import RCAMethodEnum


def how_to_activate(namespace="default"):
    """apply hpa"""
    config.load_kube_config()
    k8s_client = config.new_client_from_config()
    current_path = pathlib.Path(__file__).parent
    hpa_path = str(current_path / "hpa.yaml")
    utils.create_from_yaml(
        k8s_client=k8s_client, yaml_file=hpa_path, namespace=namespace
    )


def how_to_deactivate(namespace="default"):
    """delete hpa"""
    config.load_kube_config()
    k8s_client = config.new_client_from_config()
    current_path = pathlib.Path(__file__).parent
    hpa_path = current_path / "hpa.yaml"
    with open(hpa_path) as f:
        hpa_manifests = yaml.safe_load_all(f)
        api = AutoscalingV2Api(k8s_client)
        for hpa in hpa_manifests:
            if hpa:
                api.delete_namespaced_horizontal_pod_autoscaler(
                    name=hpa["metadata"]["name"], namespace=namespace
                )


if __name__ == "__main__":
    current_path = pathlib.Path(__file__).parent
    EXPERIMENT_CONFIG = [
        # "network_delay_preprocessing.yaml",
        # "network_loss_preprocessing.yaml",
        # "resource_cpu_preprocessing.yaml",
        "resource_memory_preprocessing.yaml",
    ]
    for experiment_name in EXPERIMENT_CONFIG:
        config_path = current_path / "config" / experiment_name
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        experiment_config = RCAExperimentConfig.model_validate(config_data)
        experiment = RCAExperiment(
            experiment_config,
            pathlib.Path(__file__).parent / "example_experiment_result",
        )
        logger.info(f"Starting experiment: {experiment_config.experiment_name}")
        # Uncomment to run
        # experiment.run()
        logger.info(f"Finished experiment: {experiment_config.experiment_name}")

    current_path = pathlib.Path(__file__).parent

    RCA_METHODS_TO_EVALUATE = [RCAMethodEnum.BARO]

    rca_evaluator = RCAEvaluator(
        current_path / "example_experiment_result",
        RCA_METHODS_TO_EVALUATE,
    )

    rca_evaluator.create_report()
