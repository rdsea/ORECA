import os
import pathlib

import yaml
from experiment_controller.config.experiment_config import (
    RCAExperimentConfig,
)
from experiment_controller.config_generator import write_config_to_filepath
from experiment_controller.experiment_controller import RCAExperiment
from experiment_controller.logger import logger

data = {
    # "experiment_name": "network_delay_ensemble",
    "number_of_run": 1,
    "time_between_run": "60s",
    "clean_up": {
        "activate": True,
        "observability_cleanup_script": "/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/observability_cleanup_script.sh",
        "application_cleanup_script": "/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/application_cleanup_script.sh",
    },
    "warm_up_interval": "30s",
    "workload": {
        "type": "docker",
        "config": {
            "image": "rdsea/train_ticket_loadgen:latest",
            "args": {
                "host": "http://<TRAIN_TICKET_HOST_IP>:32677",
                "user": "30",
                "run-time": "120s",
                "spawn-rate": "0.1",
                "locustfile": "main.py",
            },
        },
        "list_of_generator": ["edge-raspi3.cs.aalto.fi", "edge-raspi4.cs.aalto.fi"],
        "ssh_username": "aaltosea",
    },
    "data_collector_config": {
        "metric_url": "http://<METRICS_COLLECTOR_IP>/prometheus",
        "trace_url": "http://<TRACES_COLLECTOR_IP>:3200",
    },
    "observability_cadence_config": {
        "metric_config": {
            "environment": {
                "cloud": {
                    "scrape_interval": "1s",
                    "evaluation_interval": "1s",
                },
            }
        }
    },
    # "elastic_config": {
    #     "environment": {
    #         "cloud": [
    #             {
    #                 "name": "horizontal pod autoscaler",
    #                 "type": "infrastructure",
    #                 "active": True,
    #                 "how_to_activate": "/u/49/anhdun1/unix/git/RCA_Edge_Cloud/benchmark/experiment_controller/docs/train_ticket/scripts/hpa.yaml",
    #                 "how_to_deactivate": "/u/49/anhdun1/unix/git/RCA_Edge_Cloud/benchmark/experiment_controller/docs/train_ticket/scripts/hpa.yaml",
    #             }
    #         ]
    #     },
    # },
}

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
FAULT_ROOT_CAUSE = {
    "network-delay": "service:rtt",
    "resource-cpu": "service:cpu_usage",
    "resource-memory": "service:memory_usage",
}
FAULT_CONFIG = {
    "network-delay": {
        # "name": "network-delay-ensemble",
        "duration": "30s",
        "fault_type": "NetworkFault.DELAY",
        "target": {
            "namespace": "default",
            "environment": ["cloud"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "delay": {"latency": "50ms", "correlation": "0.5", "jitter": "20ms"},
        },
    },
    "resource-cpu": {
        # "name": "resource-cpu-ensemble",
        "duration": "30s",
        "fault_type": "ResourceHog.CPU",
        "target": {
            "namespace": "default",
            "environment": ["cloud"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "stress_cpu": {"workers": 1, "load": 100},
        },
    },
    "resource-memory": {
        # "name": "resource-memory-ensemble",
        "duration": "30s",
        "fault_type": "ResourceHog.MEMORY",
        "target": {
            "namespace": "default",
            "environment": ["cloud"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "stress_memory": {"workers": 1, "size": "150MB"},
        },
    },
}


def generate_config(metric_cadence: str):
    current_path = pathlib.Path(__file__).parent
    for service in SERVICE:
        for fault in FAULT:
            fault_config = FAULT_CONFIG[fault]
            fault_config["name"] = f"{fault}-{service}"
            fault_config["target"]["label_selectors"] = {"app": service}
            fault_config["fault_injection_period"] = "900s"
            data["observability_cadence_config"]["metric_config"]["environment"][
                "cloud"
            ]["scrape_interval"] = metric_cadence
            data["observability_cadence_config"]["metric_config"]["environment"][
                "cloud"
            ]["evaluation_interval"] = metric_cadence
            all_data = {
                **data,
                "fault_config": fault_config,
                "experiment_name": f"{fault}_{service}",
                "root_cause": {
                    "what": service,
                    "where": FAULT_ROOT_CAUSE[fault],
                },
            }
            experiment_path = current_path / "config.local" / f"{service}-{fault}"
            os.makedirs(experiment_path, exist_ok=True)
            write_config_to_filepath(all_data, experiment_path / "config.yaml")


if __name__ == "__main__":
    current_path = pathlib.Path(__file__).parent
    metric_cadences_list = ["1s", "3s", "5s"]
    for metric_cadence in metric_cadences_list:
        generate_config(metric_cadence)
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
                    pathlib.Path(__file__).parent / f"scrape_{metric_cadence}",
                )
                logger.info(f"Starting experiment: {experiment_config.experiment_name}")
                # Uncomment to run
                experiment.run()
                logger.info(f"Finished experiment: {experiment_config.experiment_name}")
