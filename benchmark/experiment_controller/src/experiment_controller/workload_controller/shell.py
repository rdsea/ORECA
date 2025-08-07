from experiment.workload_controller.base import WorkloadController


class ShellWorkloadGenerator(WorkloadController):
    """Workload controller using a shell script."""

    def __init__(
        self,
        hosts: list[str],
        ssh_username: str,
        script_path: str,
        script_args: dict[str, str] | None = None,
    ):
        super().__init__(hosts, ssh_username)
        self.script_path = script_path
        self.script_args = script_args if script_args is not None else {}

    def start(self):
        args_str = " ".join([f"--{k} {v}" for k, v in self.script_args.items()])
        command_to_run = f"bash {self.script_path} {args_str}"
        self._run_on_all_hosts(command_to_run)
