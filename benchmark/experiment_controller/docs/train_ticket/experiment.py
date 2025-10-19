import pathlib

import yaml
from experiment_controller.config.experiment_config import (
    RCAExperimentConfig,
)
from experiment_controller.experiment_controller import RCAExperiment
from experiment_controller.logger import logger
from experiment_controller.rca_evaluator import RCAEvaluator
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
