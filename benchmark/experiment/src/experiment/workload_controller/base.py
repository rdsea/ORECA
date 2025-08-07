import abc
import logging
import select
from concurrent.futures import ThreadPoolExecutor

import paramiko


class WorkloadController(abc.ABC):
    """Abstract base class for workload controllers."""

    def __init__(self, hosts: list[str], ssh_username: str):
        self.hosts = hosts
        self.ssh_username = ssh_username

    @abc.abstractmethod
    def start(self):
        """Starts the workload generation."""
        pass

    def _ssh_run_command(self, host: str, command: str) -> str:
        """Run a command on a remote machine via SSH and stream output."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=self.ssh_username)

            transport = ssh.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            channel.exec_command(command)

            logging.info(f"--- [{host}] Command started ---")
            while True:
                rl, _, _ = select.select([channel], [], [], 1.0)
                if channel in rl:
                    try:
                        output = channel.recv(1024).decode("utf-8")
                        if output:
                            print(output, end="", flush=True)
                    except Exception as e:
                        logging.error(f"[{host}] Error reading output: {e}")

                if channel.exit_status_ready():
                    break

            exit_status = channel.recv_exit_status()
            ssh.close()

            return f"--- [{host}] Command finished with exit code {exit_status} ---"
        except Exception as e:
            return f"--- [{host}] SSH command failed ---\nError: {e}"

    def _run_on_all_hosts(self, command: str):
        logging.info("Starting load generators on remote nodes...")
        logging.debug(f"Command: {command}")

        if not self.hosts:
            logging.warning("No load generator hosts provided.")
            return

        with ThreadPoolExecutor(max_workers=len(self.hosts)) as executor:
            futures = [
                executor.submit(self._ssh_run_command, host, command)
                for host in self.hosts
            ]

            for future in futures:
                result = future.result()
                print(result)
