"""
Inference baseline for Data Cleaning OpenEnv environment.

Required environment variables:
- API_BASE_URL: LLM API endpoint (defaults to HF router)
- MODEL_NAME: model identifier for chat completions
- HF_TOKEN or API_KEY or OPENAI_API_KEY: API key (fallback order)

Connection behavior:
- Try ENV_URL first (default http://localhost:8000)
- If unavailable, fall back to Docker image via from_docker_image
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sys
import textwrap
import urllib.request
from typing import Any, Dict, List

try:
    from data_cleaning_env import DataCleanAction, DataCleanEnv
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from data_cleaning_env import DataCleanAction, DataCleanEnv

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "data-cleaning-env:latest")

TASKS = ["easy", "medium", "hard"]
TASK_MAX_STEPS = {"easy": 10, "medium": 15, "hard": 20}
TEMPERATURE = 0.2
MAX_TOKENS = 4096
NEAR_PERFECT_SCORE = 0.99

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a data cleaning agent. You receive task instructions, a target schema,
    and raw records. Return only a JSON array containing all cleaned records.

    Rules:
    - Output must be valid JSON and contain no markdown.
    - Keep all records; do not drop rows unless exact duplicates must be removed.
    - Follow task-specific business rules from the prompt.
    - Match the target schema exactly.
    """
).strip()


def _validate_required_env() -> None:
    if not API_KEY:
        sys.exit("ERROR: Missing API key. Set HF_TOKEN, API_KEY, or OPENAI_API_KEY.")
    if not MODEL_NAME:
        sys.exit("ERROR: Missing MODEL_NAME.")


def _extract_response_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip().startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return "\n".join(lines[1:]).strip()


def parse_response(text: str) -> List[Dict[str, Any]]:
    cleaned = _strip_markdown_fences(text)
    if not cleaned:
        return []

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []
    if not all(isinstance(row, dict) for row in payload):
        return []
    return payload


def build_user_prompt(observation: Any, step: int, max_steps: int) -> str:
    records = observation.input_data or []
    schema = observation.target_schema or {}
    errors = observation.validation_errors or []

    data_json = json.dumps(records, ensure_ascii=True, indent=2)
    if len(data_json) > 80_000:
        data_json = json.dumps(records, ensure_ascii=True, separators=(",", ":"))

    lines = [
        f"Step: {step}/{max_steps}",
        f"Task:\n{observation.task_description}",
        f"Target schema:\n{json.dumps(schema, ensure_ascii=True, indent=2)}",
        f"Input data ({len(records)} records, full dataset):\n{data_json}",
    ]

    if errors:
        shown = errors[:30]
        lines.append(
            "Validation errors from previous attempt:\n"
            + "\n".join(f"- {item}" for item in shown)
        )
        lines.append(f"Current score: {observation.current_score:.3f}")

    lines.append("Respond with only a JSON array of cleaned records.")
    return "\n\n".join(lines)


def _server_is_reachable(url: str, timeout: float = 3.0) -> bool:
    health_url = f"{url.rstrip('/')}/health"
    try:
        urllib.request.urlopen(health_url, timeout=timeout)
        return True
    except Exception:
        return False


def _connect_env() -> Any:
    if _server_is_reachable(ENV_URL):
        print(f"[connect] Using running server at {ENV_URL}")
        try:
            return DataCleanEnv(base_url=ENV_URL).sync()
        except Exception as exc:
            print(f"[connect] Failed to connect via ENV_URL ({exc}). Trying Docker fallback.")

    print(f"[connect] ENV_URL unavailable: {ENV_URL}")
    print(f"[connect] Falling back to Docker image: {DOCKER_IMAGE}")
    try:
        docker_env = asyncio.run(DataCleanEnv.from_docker_image(DOCKER_IMAGE))
        return docker_env.sync()
    except Exception as exc:
        sys.exit(f"ERROR: Unable to connect via ENV_URL or Docker fallback ({exc}).")


def _request_model_output(client: OpenAI, prompt: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        stream=False,
    )
    return _extract_response_text(completion.choices[0].message.content)


def run_task(env: Any, client: OpenAI, task_id: str) -> Dict[str, Any]:
    result = env.reset(task_id=task_id)
    observation = result.observation
    max_steps = TASK_MAX_STEPS.get(task_id, 10)

    print("=" * 60)
    print(f"Task: {task_id} | max_steps={max_steps}")
    print(f"Input records: {len(observation.input_data)}")

    best_score = float(observation.current_score)

    for step in range(1, max_steps + 1):
        if result.done:
            print("  Environment marked done before next step.")
            break

        prompt = build_user_prompt(observation, step, max_steps)

        try:
            response_text = _request_model_output(client, prompt)
            cleaned_data = parse_response(response_text)
            if not cleaned_data:
                print("  Model output was not valid JSON list[dict]. Using empty payload fallback.")
        except Exception as exc:
            print(f"  Model request failed ({exc}). Using empty payload fallback.")
            cleaned_data = []

        action = DataCleanAction(data=cleaned_data)
        result = env.step(action)
        observation = result.observation

        score = float(observation.current_score)
        best_score = max(best_score, score)
        reward = float(result.reward) if result.reward is not None else 0.0
        error_count = len(observation.validation_errors)

        print(
            f"  Step {step}/{max_steps}: score={score:.3f} | "
            f"errors={error_count} | reward={reward:.3f}"
        )

        if score >= NEAR_PERFECT_SCORE:
            print("  Near-perfect score reached. Early stopping this task.")
            break

        if result.done:
            print("  Environment signalled done.")
            break

    print(f"  Best score ({task_id}): {best_score:.3f}")
    return {"task_id": task_id, "best_score": best_score}


def main() -> None:
    _validate_required_env()

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        sys.exit("ERROR: Missing dependency 'openai'. Install it before running inference.py.")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = _connect_env()

    try:
        results: List[Dict[str, Any]] = []
        for task_id in TASKS:
            results.append(run_task(env, client, task_id))

        total = sum(item["best_score"] for item in results)
        average = total / len(results) if results else 0.0

        print("=" * 60)
        print("Baseline scores")
        for item in results:
            print(f"  {item['task_id']}: {item['best_score']:.3f}")
        print(f"  average: {average:.3f}")
        print("=" * 60)
    finally:
        try:
            env.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
