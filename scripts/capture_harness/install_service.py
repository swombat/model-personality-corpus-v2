#!/usr/bin/env python3
"""Generate portable service definitions; installation is explicit, not a side effect."""

import argparse, json, plistlib, shlex, sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("spec", type=Path)
p.add_argument("--state", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--platform", choices=["macos", "linux"], required=True)
p.add_argument("--credential-loader", type=Path, required=True)
p.add_argument("--name", default="mira-model-capture")
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
a.state.mkdir(parents=True, exist_ok=True)
wrapper = a.output / "start.sh"
wrapper.write_text(
    "#!/usr/bin/env bash\nset -euo pipefail\nsource "
    + shlex.quote(str(a.credential_loader.resolve()))
    + "\nexec "
    + shlex.join(
        [
            sys.executable,
            str(Path(__file__).with_name("service.py").resolve()),
            str(a.spec.resolve()),
            "--state",
            str(a.state.resolve()),
        ]
    )
    + "\n"
)
wrapper.chmod(0o700)
if a.platform == "macos":
    d = {
        "Label": "com.mira." + a.name,
        "ProgramArguments": [
            "/usr/bin/caffeinate",
            "-i",
            "/bin/bash",
            str(wrapper.resolve()),
        ],
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 60,
        "ProcessType": "Standard",
        "StandardOutPath": str(a.state.resolve() / "service.log"),
        "StandardErrorPath": str(a.state.resolve() / "service.err"),
        "EnvironmentVariables": {
            "PATH": str(Path.home() / ".cargo/bin")
            + ":/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
            "SOPS_AGE_KEY_FILE": str(Path.home() / ".config/sops/age/keys.txt"),
        },
    }
    dest = a.output / (d["Label"] + ".plist")
    dest.write_bytes(plistlib.dumps(d))
    print(dest)
else:
    dest = a.output / (a.name + ".service")
    dest.write_text(
        "[Unit]\nDescription=Verified streaming model capture\nAfter=network-online.target\nWants=network-online.target\nStartLimitIntervalSec=600\nStartLimitBurst=5\n\n[Service]\nType=simple\nExecStart=/bin/bash "
        + json.dumps(str(wrapper.resolve()))
        + "\nRestart=on-failure\nRestartSec=60\nKillMode=control-group\nTimeoutStopSec=45\nUMask=0077\n\n[Install]\nWantedBy=default.target\n"
    )
    print(dest)
