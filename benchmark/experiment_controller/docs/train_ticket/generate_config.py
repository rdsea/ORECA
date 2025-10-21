import os
import pathlib

from jinja2 import Environment, FileSystemLoader


def format_yaml_args(args_dict):
    """Format a dictionary as properly indented YAML lines"""
    lines = []
    for key, value in args_dict.items():
        # Properly quote strings
        if isinstance(value, str) and not (
            value.startswith('"') or value.startswith("'")
        ):
            formatted_value = f'"{value}"'
        else:
            formatted_value = str(value)
        lines.append(f"      {key}: {formatted_value}")
    return "\n".join(lines)


env = Environment(
    loader=FileSystemLoader("."),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.filters["format_yaml_args"] = format_yaml_args
template = env.get_template("experiment_config_template.yaml.j2")

data = {
    # "experiment_name": "network_delay_ensemble",
    "number_of_run": 1,
    "time_between_run": "60s",
    "clean_up": {
        "activate": True,
        "observability_cleanup_script": "/u/49/anhdun1/unix/git/RCA_Edge_Cloud/benchmark/experiment_controller/docs/train_ticket/scripts/application_cleanup_script.sh",
        "application_cleanup_script": "/u/49/anhdun1/unix/git/RCA_Edge_Cloud/benchmark/experiment_controller/docs/train_ticket/scripts/observability_cleanup_script.sh",
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
    # "ground_truth": "ensemble_service:rtt",
    "anomaly_injection_period": "900s",
    "warm_up_interval": "300s",
    "workload": {
        "type": "docker",
        "config": {
            "image": "rdsea/train_ticket_loadgen:latest",
            "args": {
                "host": "http://XXX.XXX.XXX.XXX:32677",
                "user": "30",
                "run-time": "1200s",
                "spawn-rate": "0.1",
                "locustfile": "main.py",
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
            "environment": ["cloud_big"],
            "scrape_interval": "1s",
            "evaluation_interval": "1s",
        }
    },
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
        "duration": "300s",
        "fault_type": "NetworkFault.DELAY",
        "target": {
            "namespace": "default",
            "environment": ["cloud_big"],
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
            "environment": ["cloud_big"],
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
            "environment": ["cloud_big"],
            # "label_selectors": {"app": "ensemble"},
        },
        "fault_specific_config": {
            "namespace": "default",
            "duration": "300s",
            "stress_memory": {"workers": 1, "size": "150MB"},
        },
    },
}
current_path = pathlib.Path(__file__).parent
for service in SERVICE:
    for fault in FAULT:
        experiment_name = f"{fault}_{service}"
        fault_config = FAULT_CONFIG[fault]
        fault_config["name"] = f"{fault}_{service}"
        fault_config["ground_truth"] = f"{service}_service:rtt"
        fault_config["target"]["label_selectors"] = {"app": service}
        rendered_yaml = template.render(
            {
                **data,
                "fault_config": fault_config,
                "experiment_name": f"{fault}_{service}",
                "ground_truth": f"{service}_{FAULT_ROOT_CAUSE[fault]}",
            }
        )
        experiment_path = current_path / "config.local" / f"{service}-{fault}"
        os.makedirs(experiment_path, exist_ok=True)
        with open(experiment_path / "config.yaml", "w") as f:
            f.write(rendered_yaml)
