# RCA Edge Cloud

This benchmark is designed to be reused for different targeted system under test with different property and on different infrastructure.

## Benchmarking process

### Prerequisite

1. Have a k8s compatible cluster (we have only test with k3s and k8s). For example, in our experiment, we have a k3s cluster with 3 nodes as edge part and a GKE cluster with 3 nodes as cloud part

- Deploying k3s instruction: can be automated with [k3sup](https://github.com/alexellis/k3sup)
- Deploying k8s instruction: currently we have 2 terraform scripts to deploy k8s with bare compute engine and with GKE, you can use both by:
  - Defining the variable in `terraform.tfvars` that follows `variables.tf`
  - Login to your gcloud
  - Apply the terraform script with `terraform apply`

TODO:

- How to define edge cloud, configuration?

2. Deploy the monitoring stack: we have include all required helm chart with value in `benchmark/helm_charts/` but you can use the cli in `benchmark` by:

- Installing python dependencies using [rye](https://rye.astral.sh/)

```bash
rye sync
source .venv/bin/activate
```

- Run the cli

```bash
python3 cli.py
```

- In the cli, there are many commands to deploy observability tools individually or you can deploy all using command `init_telemetry`
- If you can to remove the observability stack, use command `destroy` or manually use `helm uninstall`

3. Deploy your system under test:

- Deploy it to the `default` namespace
- You should route your trace export in you SUT to otel collector at `http://my-opentelemetry-collector.observe:4318/v1/traces`

4. Define your experiment config

- We have a pydantic model [RCAExperimentConfig](benchmark/experiment/src/experiment/config/anomaly_model.py) that you can use to define your experiment config with yaml or python object. For yaml, you can check an [example](benchmark/experiment/src/experiment/config/examples/network_delay_preprocessing.yaml)

  Do they have to change anything?
  The requirement for SUT?

### Running benchmark

- By using the `RCAExperiment` class, you can run the simplest experiment with the following code which will run the experiment and then export the metrics to csv

```python
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s - %(message)s",
    )
    try:
        config_path = ...
        with open(config_path) as f:
          config_data = yaml.safe_load(f)

          experiment_config = RCAExperimentConfig(**config_data)
          experiment = RCAExperiment(experiment_config)

          experiment.run()

          prom = PrometheusAPI(monitor_config["prometheus_url"])

          # Define time range for exporting metrics
          end_time = datetime.now()
          start_time = end_time - timedelta(minutes=17)
          # injection_time = 1753213321

          prom.query_range(
              ALL_METRICS,
              start_time,
              end_time,
              experiment_name=f"{file.split('.')[0]}_{i}",
              step="1s",
          )
```

- If multiple experiments are run continuously, we should ...
  > TODO:
  >
  > do we clean up or what
  > Dynamic situation with dynamicity, elasticity, model ensemble?
  > Assumption about the application: multimodal, dynamic ensemble with faulty model,

### Post-processing data

Is there any input required?
Collect observability data
Combine and organise to a dataset

### Results analytic

Evaluate the performance of the RCA techniques based on the provided metrics:
Precision
Accuracy
Runtime
Resources usage
Do we have user-defined?
Cross benchmark with different parameter, infrastructure difference comparison
How many dimension: application, parameter, infrastructure, intelligent application?
How problem is defined based on context: contextual cause-effect
