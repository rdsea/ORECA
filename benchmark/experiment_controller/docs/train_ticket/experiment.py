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

SERVICE = [
    "ts-auth-service",
    "ts-order-service",
    "ts-route-service",
    "ts-train-service",
    "ts-travel-service",
    # "ts-admin-basic-info-service",
    # "ts-admin-order-service",
    # "ts-admin-route-service",
    # "ts-admin-travel-service",
    # "ts-admin-user-service",
    # "ts-assurance-service",
    # "ts-avatar-service",
    # "ts-basic-service",
    # "ts-cancel-service",
    # "ts-common",
    # "ts-config-service",
    # "ts-consign-price-service",
    # "ts-consign-service",
    # "ts-contacts-service",
    # "ts-delivery-service",
    # "ts-execute-service",
    # "ts-food-delivery-service",
    # "ts-food-service",
    # "ts-gateway-service",
    # "ts-inside-payment-service",
    # "ts-news-service",
    # "ts-notification-service",
    # "ts-order-other-service",
    # "ts-payment-service",
    # "ts-preserve-other-service",
    # "ts-preserve-service",
    # "ts-price-service",
    # "ts-rebook-service",
    # "ts-route-plan-service",
    # "ts-seat-service",
    # "ts-security-service",
    # "ts-station-food-service",
    # "ts-station-service",
    # "ts-ticket-office-service",
    # "ts-train-food-service",
    # "ts-travel2-service",
    # "ts-travel-plan-service",
    # "ts-ui-dashboard",
    # "ts-user-service",
    # "ts-verification-code-service",
    # "ts-voucher-service",
    # "ts-wait-order-service",
]
FAULT = [
    "network-delay",
    "resource-cpu",
    "resource-memory",
]


def how_to_activate(namespace="train-ticket"):
    """apply hpa"""
    config.load_kube_config()
    k8s_client = config.new_client_from_config()
    current_path = pathlib.Path(__file__).parent
    hpa_path = str(current_path / "hpa.yaml")
    utils.create_from_yaml(
        k8s_client=k8s_client, yaml_file=hpa_path, namespace=namespace
    )


def how_to_deactivate(namespace="train-ticket"):
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
    for service in SERVICE:
        for fault in FAULT:
            config_path = (
                current_path / "config.local" / f"{service}-{fault}" / "config.yaml"
            )
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            experiment_config = RCAExperimentConfig.model_validate(config_data)
            experiment = RCAExperiment(
                experiment_config,
                pathlib.Path(__file__).parent / "train_ticket_result.local",
            )
            logger.info(f"Starting experiment: {experiment_config.experiment_name}")
            # Uncomment to run
            # experiment.run()
            logger.info(f"Finished experiment: {experiment_config.experiment_name}")

    current_path = pathlib.Path(__file__).parent

    RCA_METHODS_TO_EVALUATE = [
        RCAMethodEnum.BARO,
        RCAMethodEnum.DUMMY,
        # RCAMethodEnum.CAUSALAI,
        # RCAMethodEnum.CAUSALRCA,
        # RCAMethodEnum.CIRCA,
        # RCAMethodEnum.CLOUDRANGER,
    ]

    rca_evaluator = RCAEvaluator(
        current_path / "train_ticket_result.local",
        RCA_METHODS_TO_EVALUATE,
    )

    # rca_evaluator.create_report()
