"""Meeting commands for the current running demo instance."""
import argparse
import json
import subprocess

from start import RUNTIME, chassis, portal_environment

TASK = "task-cedar-launch-2"
CHANGES = {"status": "done", "next_step": "Homer confirmed the fictional Cedar launch review."}


def chief_write(vault):
    env = portal_environment()
    # Rotate the disposable chief token inside the trusted shell. Keep it out of argv and files.
    token = chassis("agent-token", "create", "chief-of-staff", "--vault", vault, env=env).strip()
    env.update(CHASSIS_AGENT_ID="chief-of-staff", CHASSIS_AGENT_TOKEN=token,
               CHASSIS_AGENT_NAME="chief-of-staff", CHASSIS_AGENT_EMAIL="chief-of-staff@chassis.local")
    record = json.loads(chassis("get", TASK, "--vault", vault, env=env))
    if all(record[key] == value for key, value in CHANGES.items()):
        print("Homer's update is already present.")
        return
    result = json.loads(chassis("update", TASK, "--vault", vault, "--expected-version",
                                str(record["version"]), "--changes", json.dumps(CHANGES), env=env))
    print(f'{TASK}  v{result["record"]["version"]}  {result["commit"]}')


def history(vault):
    return subprocess.check_output(["git", "-C", vault, "log", "-3",
                                    "--format=%h  %an <%ae>  %s", "--name-only"], text=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["chief-write", "history"])
    args = parser.parse_args()
    active = (RUNTIME / "current").resolve(strict=True)
    if args.command == "chief-write":
        chief_write(active)
    else:
        print(history(active), end="")
