# master-thesis

## Running the cli to manage the experiment

- Firstly, create a virtualenv for the project either by [rye](https://rye.astral.sh/) with `rye sync` or create your own virtualenv and install the dependencies by:

```bash
pip install -r requirement.lock
```

- Run the cli by:

```bash
python3 cli.py
```

- Currently we have the following command:

| Command                 | Description                         |
| ----------------------- | ----------------------------------- |
| `init_telemetry`        | Initialize the full telemetry stack |
| `destroy`               | Destroy the entire telemetry stack  |
| `init_metric`           | Start the metrics service           |
| `destroy_metric`        | Stop the metrics service            |
| `init_log`              | Start the logging service           |
| `destroy_log`           | Stop the logging service            |
| `init_visualization`    | Start visualization components      |
| `destroy_visualization` | Stop visualization components       |
| `set_log_level`         | Change logging verbosity            |
| `exit`                  | Exit the CLI                        |

