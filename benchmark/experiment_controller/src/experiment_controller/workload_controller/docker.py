from experiment_controller.workload_controller.base import WorkloadController


class DockerWorkloadGenerator(WorkloadController):
    """Workload controller using Docker."""

    def __init__(
        self,
        hosts: list[str],
        ssh_username: str,
        docker_image: str,
        docker_args: dict[str, str] | None = None,
    ):
        super().__init__(hosts, ssh_username)
        self.docker_image = docker_image
        self.docker_args = docker_args if docker_args is not None else {}

    def start(self):
        args_str = " ".join([f"--{k} {v}" for k, v in self.docker_args.items()])
        command_to_run = f"docker run {args_str} {self.docker_image}"
        self._run_on_all_hosts(command_to_run)
