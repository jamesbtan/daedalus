import io

from pyinfra.facts.server import Command
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server, systemd

from pyinfra import host, logger

files.put(
    name="Configure passwordless sudo for james",
    src=io.StringIO("james ALL=(ALL) NOPASSWD: ALL\n"),
    dest="/etc/sudoers.d/james",
    mode="0440",
    user="root",
    group="root",
    _sudo=True,
)


def configure_pi():
    rpi_swap = apt.packages(
        name="Remove rpi-swap package",
        packages=["rpi-swap"],
        present=False,
        purge=True,
        _sudo=True,
    )

    orphaned = host.get_fact(
        Command,
        command="apt-get --dry-run autoremove | grep '^Remv ' || true",
    )
    if orphaned:
        logger.info(orphaned)
        server.shell(
            name="Autoremove and purge unused apt dependencies",
            commands=["apt-get autoremove --purge -y"],
            _env={"DEBIAN_FRONTEND": "noninteractive"},
            _sudo=True,
        )

    if rpi_swap.changed or orphaned:
        systemd.daemon_reload(_sudo=True)
        server.shell(
            name="Disable active swap",
            commands=["/usr/sbin/swapoff -a"],
            _sudo=True,
        )

    journald_dropin = files.put(
        name="Configure volatile journald storage",
        src=io.StringIO("[Journal]\nStorage=volatile\nRuntimeMaxUse=64M\n"),
        dest="/etc/systemd/journald.conf.d/volatile.conf",
        create_remote_dir=True,
        _sudo=True,
    )

    if journald_dropin.changed:
        systemd.service(
            name="Restart systemd-journald",
            service="systemd-journald",
            restarted=True,
            _sudo=True,
        )

    # 2. Ensure cgroup memory flags are present on the single line in /boot/firmware/cmdline.txt
    if host.get_fact(File, path="/boot/firmware/cmdline.txt"):
        cmdline = host.get_fact(Command, command="cat /boot/firmware/cmdline.txt")
        if cmdline:
            required_flags = [
                "cgroup_enable=cpuset",
                "cgroup_enable=memory",
                "cgroup_memory=1",
            ]
            current_tokens = cmdline.strip().split()
            missing_flags = [f for f in required_flags if f not in current_tokens]

            if missing_flags:
                updated_cmdline = " ".join(current_tokens + missing_flags) + "\n"
                files.put(
                    name="Enable cgroup memory flags in cmdline.txt",
                    src=io.StringIO(updated_cmdline),
                    dest="/boot/firmware/cmdline.txt",
                    _sudo=True,
                )


if host.data.get("raspberry_pi"):
    configure_pi()

def configure_laptop():
    logind_dropin = files.put(
        name="Ignore laptop lid switch events",
        src=io.StringIO(
            "[Login]\n"
            "HandleLidSwitch=ignore\n"
            "HandleLidSwitchExternalPower=ignore\n"
            "HandleLidSwitchDocked=ignore\n"
        ),
        dest="/etc/systemd/logind.conf.d/ignore-lid.conf",
        create_remote_dir=True,
        _sudo=True,
    )

    if logind_dropin.changed:
        systemd.service(
            name="Restart systemd-logind",
            service="systemd-logind",
            restarted=True,
            _sudo=True,
        )

if host.data.get("laptop"):
    configure_laptop()
