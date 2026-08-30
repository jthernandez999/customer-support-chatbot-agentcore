"""Load non-empty KEY=VALUE pairs from a nearby .env file."""
import os
import pathlib


def load_repo_env():
    here = pathlib.Path(__file__).resolve().parent
    env_path = None
    for folder in [here, *here.parents]:
        candidate = folder / ".env"
        if candidate.is_file():
            env_path = candidate
            break
    if env_path is None:
        sibling = (
            here.parents[2]
            / "aws-c1-prompting-llm-reasoning-nd905-cd14762-exercises"
            / ".env"
        )
        if sibling.is_file():
            env_path = sibling
    if env_path is None:
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value:
            os.environ[key] = value
    if not os.environ.get("AWS_PROFILE"):
        os.environ.pop("AWS_PROFILE", None)
