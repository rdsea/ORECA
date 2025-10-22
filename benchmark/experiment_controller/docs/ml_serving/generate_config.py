import os
import pathlib

from experiment_controller.config_generator import write_config_to_filepath

data = {
    # "experiment_name": "network_delay_ensemble",
    "number_of_run": 1,
    "time_between_run": "60s",
    "clean_up": {
        "activate": True,
        "observability_cleanup_script": "/u/49/anhdun1/unix/git/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/application_cleanup_script.sh",
        "application_cleanup_script": "/u/49/anhdun1/unix/git/RCA_Edge_Cloud/benchmark/experiment_controller/docs/ml_serving/scripts/observability_cleanup_script.sh",
    },
    # "fault_config": {
    #     "name": "network-delay-ensemble",
    #     "duration": "300s",
    #     "fault_type": "NetworkFault.DELAY",
    #     "target": {
    #         "namespace": "default",
    #         "environment": ["edge"],
    #         "label_selectors": {"app": "ensemble"},
    #     },
    #     "fault_specific_config": {
    #         "namespace": "default",
    #         "duration": "300s",
    #         "delay": {"latency": "50ms", "correlation": "0.5", "jitter": "20ms"},
    #     },
    # },
    # "root_cause": {"what": "ensemble", "where": "service:rtt"},
    "anomaly_injection_period": "900s",
    "warm_up_interval": "300s",
    "workload": {
        "type": "docker",
        "config": {
            "image": "rdsea/object_detection_client:latest",
            "args": {
                "host": "http://XXX.XXX.XXX.XXX",
                "user": "5",
                "run-time": "1200s",
                "spawn-rate": "0.1",
            },
        },
        "list_of_generator": ["edge-raspi3.cs.aalto.fi", "edge-raspi4.cs.aalto.fi"],
        "ssh_username": "aaltosea",
    },
    "data_collector_config": {
        "metric_url": "http://XXX.XXX.XXX.XXX/prometheus",
        "trace_url": "http://XXX.XXX.XXX.XXX/tempo",
    },
    "observability_cadence_config": {
        "metric_config": {
            "environment": ["edge", "cloud"],
            "scrape_interval": "1s",
            "evaluation_interval": "1s",
        }
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
            "duration": "300s",
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
            "duration": "300s",
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
            "duration": "300s",
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
current_path = pathlib.Path(__file__).parent
for service in SERVICE:
    for fault in FAULT:
        experiment_name = f"{fault}_{service}"
        fault_config = FAULT_CONFIG[fault]
        fault_config["name"] = f"{fault}_{service}"
        fault_config["target"]["label_selectors"] = {"app": service}
        if fault == "resource-memory":
            fault_config["fault_specific_config"]["stress_memory"]["size"] = (
                SERVICE_MEMORY_CONFIG[service]
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
