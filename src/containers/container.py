import os
import shlex
import subprocess
from typing import Dict, Optional


def _run_cmd(cmd: str, stderr_devnull=False) -> str:
    stderr = None
    if stderr_devnull:
        stderr = subprocess.DEVNULL
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=stderr)
    out, _ = p.communicate()
    return out.decode().strip()


def get_child_pid(unshare_pid: int) -> Optional[int]:
    pids = _run_cmd(f"ps -A -o ppid,pid | grep '^\s*{unshare_pid}'").split("\n")
    for line in pids:
        child_pid = line.strip().split()[1]
        return int(child_pid)
    return None


def get_pid_ns(pid: int) -> int:
    pidns = _run_cmd(f"ls -Li /proc/{pid}/ns/pid | awk '{{print $1}}'")
    return int(pidns)


# Maps from container pid to host pids.
# Note: Containers can have overlapping pid spaces. If you're getting an abitrary PID, you can't know
# which container it might be from.
class PIDMapper:
    def __init__(self, pidns: int):
        self.pidns = pidns
        self._pid_map: Dict[int, int] = {}

    def _refresh(self):
        self._pid_map = {}

        lines = _run_cmd(
            "cat /proc/*/status | grep 'NSpid' | awk '{print $2, $NF}'"
        ).split("\n")
        host_to_container = {int(v.split()[0]): int(v.split()[1]) for v in lines}

        lines = _run_cmd(
            "ls -Li /proc/*/ns/pid | awk -F'[ /]' '{print $1, $4}'", stderr_devnull=True
        ).split("\n")
        host_to_ns = {}
        for v in lines:
            try:
                host_to_ns[int(v.split()[1])] = int(v.split()[0])
            except ValueError:
                pass

        for pid, container_pid in host_to_container.items():
            if pid not in host_to_ns:
                continue
            if host_to_ns[pid] != self.pidns:
                continue
            self._pid_map[container_pid] = pid

    def get(self, container_pid: int) -> Optional[int]:
        if container_pid not in self._pid_map:
            self._refresh()
        if container_pid not in self._pid_map:
            return None
        return self._pid_map[container_pid]


def launch_process_container(
    cmd: list[str], directory: str, env: dict[str, str], pid_offset=0
) -> tuple[int, PIDMapper]:
    """Starts the given command in a new pid namespace.

    When the returned process exits or is killed, all programs in the
    namespace will be killed."""
    # Note: This just sets and env variable requesting a PID offset from clients.
    # This should be fixed to apply the offset before handing over control.
    env["PID_OFFSET"] = str(pid_offset)
    cmd = (
        shlex.split(
            f"unshare -U --map-user={os.getuid()} --map-group={os.getgid()} --mount-proc --fork --pid --kill-child"
        )
        + cmd
    )
    p = subprocess.Popen(cmd, cwd=directory, env=env)
    cmd_pid = get_child_pid(p.pid)
    pidns = get_pid_ns(cmd_pid)
    return p.pid, cmd_pid, PIDMapper(pidns)
