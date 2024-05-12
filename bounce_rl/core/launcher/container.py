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


def get_child_pid(parent_pid: int) -> Optional[int]:
    pids = _run_cmd(rf"ps -A -o ppid,pid | grep '^\s*{parent_pid}'")
    if not pids:
        return None

    for line in pids.split("\n"):
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
    cmd: str, directory: str, env: dict[str, str]
) -> tuple[int, int, PIDMapper]:
    """Starts the given commands in a new pid namespace.

    When the returned process exits or is killed, all programs in the
    namespace will be killed."""

    launch_cmd = shlex.split(
        f"unshare -U --map-user={os.getuid()} --map-group={os.getgid()} --mount-proc "
        "--fork --pid --kill-child "
        f"{cmd}"
    )
    print("Parsed popen command: ", launch_cmd, flush=True)
    p = subprocess.Popen(launch_cmd, cwd=directory, env=env, stderr=subprocess.PIPE)
    _ = subprocess.Popen(
        shlex.split('grep -v "libtime_control.*wrong ELF class"'),
        stdin=p.stderr,
        stderr=subprocess.STDOUT,
    )
    unshare_pid = p.pid
    cmd_pid = get_child_pid(unshare_pid)

    print("Root pid:", p.pid, "unshare_pid:", unshare_pid, "cmd_pid:", cmd_pid)

    if cmd_pid is None:
        return -1, -1, PIDMapper(-1)
    pidns = get_pid_ns(cmd_pid)
    return unshare_pid, cmd_pid, PIDMapper(pidns)
