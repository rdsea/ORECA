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
    "number_of_run": 3,
    "time_between_run": "60s",
    "clean_up": {
        "activate": True,
        "observability_cleanup_script": "/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/observability_cleanup_script.sh",
        "application_cleanup_script": "/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/application_cleanup_script.sh",
    },
    "warm_up_interval": "300s",
    "workload": {
        "type": "docker",
        "config": {
            "image": "rdsea/object_detection_client:latest",
            "args": {
                "host": "http://XXX.XXX.XXX.XXX",
                "user": "10",
                "run-time": "1200s",
                "spawn-rate": "1",
            },
        },
        "list_of_generator": ["edge-raspi3.cs.aalto.fi", "edge-raspi4.cs.aalto.fi"],
        "ssh_username": "aaltosea",
    },
    "data_collector_config": {
        "metric_url": "http://XXX.XXX.XXX.XXX/prometheus",
        "trace_url": "http://XXX.XXX.XXX.XXX:3200",
    },
    "observability_cadence_config": {
        "metric_config": {
            "environment": {
                "edge": {
                    "scrape_interval": "5s",
                    "evaluation_interval": "5s",
                },
                "cloud": {
                    "scrape_interval": "5s",
                    "evaluation_interval": "5s",
                },
            }
        }
    },
    "elastic_config": {
        "environment": {
            "edge": [
                {
                    "name": "horizontal pod autoscaler",
                    "type": "infrastructure",
                    "active": True,
                    "how_to_activate": "/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/hpa_activate.sh",
                    "how_to_deactivate": "/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/hpa_deactivate.sh",
                }
            ]
        },
    },
}

SERVICE = [
    "ensemble",
    "preprocessing",
    "inference-mobilenetv2",
    "inference-efficientnetb0",
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
FAULT_CONFIG: dict = {
    "network-delay": {
        # "name": "network-delay-ensemble",
        "duration": "300s",
        "fault_type": "NetworkFault.DELAY",
        "target": {
            "namespace": "default",
            "environment": ["edge"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "delay": {"latency": "50ms", "correlation": "0.5", "jitter": "20ms"},
        },
    },
    "resource-cpu": {
        # "name": "resource-cpu-ensemble",
        "duration": "300s",
        "fault_type": "ResourceHog.CPU",
        "target": {
            "namespace": "default",
            "environment": ["edge"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "stress_cpu": {"workers": 1, "load": 100},
        },
    },
    "resource-memory": {
        # "name": "resource-memory-ensemble",
        "duration": "300s",
        "fault_type": "ResourceHog.MEMORY",
        "target": {
            "namespace": "default",
            "environment": ["edge"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "stress_memory": {"workers": 1, "size": "150MB"},
        },
    },
}

SERVICE_MEMORY_CONFIG = {
    "ensemble": "150MB",
    "preprocessing": "100MB",
    "inference-mobilenetv2": "600MB",
    "inference-efficientnetb0": "600MB",
}


def generate_config(hpa_config: str):
    current_path = pathlib.Path(__file__).parent
    for service in SERVICE:
        for fault in FAULT:
            fault_config = FAULT_CONFIG[fault]
            fault_config["name"] = f"{fault}-{service}"
            fault_config["target"]["label_selectors"] = {"app": service}
            fault_config["fault_injection_period"] = "900s"
            data["elastic_config"]["environment"]["edge"][0]["how_to_activate"] = (
                f"/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/hpa_{hpa_config}_activate.sh"
            )

            data["elastic_config"]["environment"]["edge"][0]["how_to_deactivate"] = (
                f"/home/aaltosea/Dung/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/hpa_{hpa_config}_activate.sh"
            )

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
    # metric_cadences_list = ["1s", "3s", "5s"]
    hpa_config_list = [
        "50",
        #     "70", "50_mem"
    ]
    for hpa_config in hpa_config_list:
        generate_config(hpa_config)
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
                    pathlib.Path(__file__).parent
                    / "elastic_effect"
                    / f"hpa_{hpa_config}",
                )
                logger.info(f"Starting experiment: {experiment_config.experiment_name}")
                # Uncomment to run
                # experiment.run()
                logger.info(f"Finished experiment: {experiment_config.experiment_name}")
