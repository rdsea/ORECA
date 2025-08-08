import pathlib

import yaml

from experiment_controller.config.anomaly_model import (
    RCAExperimentConfig,
)
from experiment_controller.experiment_controller import RCAExperiment
from experiment_controller.logger import logger

if __name__ == "__main__":
    current_path = pathlib.Path(__file__).parent
    config_path = current_path / "config" / "network_delay_preprocessing.yaml"
    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    experiment_config = RCAExperimentConfig.model_validate(config_data)
    experiment = RCAExperiment(experiment_config)
    logger.info(f"Starting experiment: {experiment_config.experiment_name}")
    # Uncomment to run
    # experiment.run()
    logger.info(f"Finished experiment: {experiment_config.experiment_name}")

    # prom = PrometheusAPI(monitor_config["prometheus_url"])
    #
    # # Define time range for exporting metrics
    # end_time = datetime.now()
    # start_time = end_time - timedelta(minutes=17)
    # # injection_time = 1753213321
    #
    # prom.query_range(
    #     ALL_METRICS,
    #     start_time,
    #     end_time,
    #     experiment_name="network_delay_preprocessing",
    #     step="1s",
    # )
    # logger.info("Finished querying metrics")
