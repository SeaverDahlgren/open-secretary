from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path


def _service_plist_path(label: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def _write_launchd_plist(
    plist_path: Path,
    project_root: Path,
    label: str,
    module: str,
    log_name: str,
) -> None:
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    log_dir = Path.home() / "Library" / "Logs"
    plist = {
        "Label": label,
        "ProgramArguments": [sys.executable, "-m", module],
        "WorkingDirectory": str(project_root),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(log_dir / log_name),
        "StandardErrorPath": str(log_dir / log_name),
        "EnvironmentVariables": {
            "PYTHONPATH": str(project_root),
        },
    }
    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle)


def _bootstrap_launchd(plist_path: Path, label: str) -> None:
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", target, str(plist_path)], check=False)
    subprocess.run(["launchctl", "bootstrap", target, str(plist_path)], check=True)
    subprocess.run(["launchctl", "kickstart", "-k", f"{target}/{label}"], check=False)


def install_service(config_path: Path) -> None:
    if sys.platform != "darwin":
        raise SystemExit("install-service is only supported on macOS.")

    project_root = Path(__file__).resolve().parents[2]
    config_path = config_path.resolve()
    if config_path.parent != project_root or config_path.name != "config.json":
        raise SystemExit(
            f"install-service requires {project_root / 'config.json'}."
        )

    label = "com.opensecretary"
    plist_path = _service_plist_path(label)
    print(f"Writing launchd plist to {plist_path}")
    _write_launchd_plist(plist_path, project_root, label, "src.main", "openSecretary.log")
    _bootstrap_launchd(plist_path, label)
    print("launchd service installed.")


def uninstall_service() -> None:
    if sys.platform != "darwin":
        raise SystemExit("uninstall-service is only supported on macOS.")

    label = "com.opensecretary"
    plist_path = _service_plist_path(label)
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", target, str(plist_path)], check=False)
    if plist_path.exists():
        subprocess.run(["trash", str(plist_path)], check=True)
        print("launchd plist moved to Trash.")
    else:
        print("launchd plist not found.")


def service_status() -> None:
    if sys.platform != "darwin":
        raise SystemExit("status is only supported on macOS.")

    uid = os.getuid()
    label = "com.opensecretary"
    target = f"gui/{uid}/{label}"
    plist_path = _service_plist_path(label)
    result = subprocess.run(
        ["launchctl", "print", target],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        state = "not loaded"
    elif "state = running" in result.stdout:
        state = "running"
    else:
        state = "loaded"
    print(f"Service: {state}")
    print(f"Plist: {plist_path}")


def install_gateway(config_path: Path) -> None:
    if sys.platform != "darwin":
        raise SystemExit("install-gateway is only supported on macOS.")

    project_root = Path(__file__).resolve().parents[2]
    config_path = config_path.resolve()
    if config_path.parent != project_root or config_path.name != "config.json":
        raise SystemExit(
            f"install-gateway requires {project_root / 'config.json'}."
        )

    label = "com.opensecretary.gateway"
    plist_path = _service_plist_path(label)
    print(f"Writing launchd plist to {plist_path}")
    _write_launchd_plist(plist_path, project_root, label, "src.gateway.main", "openSecretary-gateway.log")
    _bootstrap_launchd(plist_path, label)
    print("launchd gateway installed.")


def uninstall_gateway() -> None:
    if sys.platform != "darwin":
        raise SystemExit("uninstall-gateway is only supported on macOS.")

    label = "com.opensecretary.gateway"
    plist_path = _service_plist_path(label)
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", target, str(plist_path)], check=False)
    if plist_path.exists():
        subprocess.run(["trash", str(plist_path)], check=True)
        print("launchd gateway plist moved to Trash.")
    else:
        print("launchd gateway plist not found.")


def gateway_status() -> None:
    if sys.platform != "darwin":
        raise SystemExit("gateway-status is only supported on macOS.")

    uid = os.getuid()
    label = "com.opensecretary.gateway"
    target = f"gui/{uid}/{label}"
    plist_path = _service_plist_path(label)
    result = subprocess.run(
        ["launchctl", "print", target],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        state = "not loaded"
    elif "state = running" in result.stdout:
        state = "running"
    else:
        state = "loaded"
    print(f"Gateway: {state}")
    print(f"Plist: {plist_path}")
