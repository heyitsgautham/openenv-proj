"""
Inference baseline for Data Cleaning OpenEnv environment.

Required environment variables:
- API_BASE_URL: LLM API endpoint (defaults to HF router)
- MODEL_NAME: model identifier for chat completions
- HF_TOKEN or API_KEY or OPENAI_API_KEY: API key (fallback order)
    If unset, uses local Hugging Face CLI login token when available.

Connection behavior:
- Try ENV_URL first (default http://localhost:8000)
- If unavailable, fall back to Docker image via from_docker_image
- Optional LOCAL_IMAGE_NAME when using from_docker_image
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import json
import os
from pathlib import Path
import sys
import textwrap
import time
import urllib.request
from typing import Any, Dict, List

try:
    from data_cleaning_env import DataCleanAction, DataCleanEnv
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from data_cleaning_env import DataCleanAction, DataCleanEnv


def _load_hf_cli_token() -> str | None:
    try:
        from huggingface_hub import HfFolder

        token = HfFolder.get_token()
        if token:
            return token.strip()
    except Exception:
        return None
    return None

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = (
    os.getenv("HF_TOKEN")
    or os.getenv("API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or _load_hf_cli_token()
)
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "data-cleaning-env:latest")

TASKS = ["easy", "medium", "hard"]
TASK_MAX_STEPS = {
    "easy": int(os.getenv("EASY_MAX_STEPS", "2")),
    "medium": int(os.getenv("MEDIUM_MAX_STEPS", "2")),
    "hard": int(os.getenv("HARD_MAX_STEPS", "3")),
}
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "45"))
ENV_STEP_TIMEOUT_S = float(os.getenv("ENV_STEP_TIMEOUT_S", "8"))
ENV_RESET_TIMEOUT_S = float(os.getenv("ENV_RESET_TIMEOUT_S", "12"))
ENV_CONNECT_TIMEOUT_S = float(os.getenv("ENV_CONNECT_TIMEOUT_S", "20"))
DOCKER_CONNECT_TIMEOUT_S = float(os.getenv("DOCKER_CONNECT_TIMEOUT_S", "40"))
TASK_TIME_BUDGET_S = float(os.getenv("TASK_TIME_BUDGET_S", "360"))
INFERENCE_TIME_BUDGET_S = float(os.getenv("INFERENCE_TIME_BUDGET_S", "1080"))
MAX_CONSECUTIVE_MODEL_FAILURES = int(os.getenv("MAX_CONSECUTIVE_MODEL_FAILURES", "2"))
MAX_NO_PROGRESS_STEPS = int(os.getenv("MAX_NO_PROGRESS_STEPS", "1"))
MAX_VALIDATION_ERRORS_IN_PROMPT = int(os.getenv("MAX_VALIDATION_ERRORS_IN_PROMPT", "12"))
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

    for task_id, steps in TASK_MAX_STEPS.items():
        if steps < 1:
            sys.exit(f"ERROR: {task_id} max steps must be >= 1.")

    if LLM_TIMEOUT_S <= 0:
        sys.exit("ERROR: LLM_TIMEOUT_S must be > 0.")
    if ENV_STEP_TIMEOUT_S <= 0:
        sys.exit("ERROR: ENV_STEP_TIMEOUT_S must be > 0.")
    if ENV_RESET_TIMEOUT_S <= 0:
        sys.exit("ERROR: ENV_RESET_TIMEOUT_S must be > 0.")
    if ENV_CONNECT_TIMEOUT_S <= 0:
        sys.exit("ERROR: ENV_CONNECT_TIMEOUT_S must be > 0.")
    if DOCKER_CONNECT_TIMEOUT_S <= 0:
        sys.exit("ERROR: DOCKER_CONNECT_TIMEOUT_S must be > 0.")
    if TASK_TIME_BUDGET_S <= 0:
        sys.exit("ERROR: TASK_TIME_BUDGET_S must be > 0.")
    if INFERENCE_TIME_BUDGET_S <= 0:
        sys.exit("ERROR: INFERENCE_TIME_BUDGET_S must be > 0.")


def _log_start(message: str) -> None:
    print(f"START: {message}")


def _log_step(message: str) -> None:
    print(f"STEP: {message}")


def _log_end(message: str) -> None:
    print(f"END: {message}")


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

    data_json = json.dumps(records, ensure_ascii=True, separators=(",", ":"))

    lines = [
        f"Step: {step}/{max_steps}",
        f"Task:\n{observation.task_description}",
        f"Target schema:\n{json.dumps(schema, ensure_ascii=True, separators=(',', ':'))}",
        f"Input data ({len(records)} records, full dataset):\n{data_json}",
    ]

    if errors:
        shown = errors[:MAX_VALIDATION_ERRORS_IN_PROMPT]
        lines.append(
            "Validation errors from previous attempt:\n"
            + "\n".join(f"- {item}" for item in shown)
        )
        lines.append(f"Current score: {observation.current_score:.3f}")

    lines.append("Respond with only a minified JSON array of cleaned records.")
    return "\n\n".join(lines)


def _server_is_reachable(url: str, timeout: float = 3.0) -> bool:
    health_url = f"{url.rstrip('/')}/health"
    try:
        urllib.request.urlopen(health_url, timeout=timeout)
        return True
    except Exception:
        return False


def _run_with_timeout(fn: Any, timeout_s: float, label: str) -> Any:
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout_s)
        except FuturesTimeoutError as exc:
            raise TimeoutError(f"{label} timed out after {timeout_s:.1f}s") from exc


def _connect_env() -> Any:
    if _server_is_reachable(ENV_URL):
        _log_step(f"Using running server at {ENV_URL}")
        try:
            return _run_with_timeout(
                lambda: DataCleanEnv(base_url=ENV_URL).sync(),
                timeout_s=ENV_CONNECT_TIMEOUT_S,
                label="env_sync",
            )
        except Exception as exc:
            _log_step(f"Failed to connect via ENV_URL ({exc}). Trying Docker fallback.")

    _log_step(f"ENV_URL unavailable: {ENV_URL}")
    _log_step(f"Falling back to Docker image: {LOCAL_IMAGE_NAME}")
    try:
        docker_env = asyncio.run(
            asyncio.wait_for(
                DataCleanEnv.from_docker_image(LOCAL_IMAGE_NAME),
                timeout=DOCKER_CONNECT_TIMEOUT_S,
            )
        )
        return _run_with_timeout(
            docker_env.sync,
            timeout_s=ENV_CONNECT_TIMEOUT_S,
            label="docker_env_sync",
        )
    except Exception as exc:
        sys.exit(f"ERROR: Unable to connect via ENV_URL or Docker fallback ({exc}).")


def _request_model_output(client: OpenAI, prompt: str, timeout_s: float) -> str:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        stream=False,
        timeout=timeout_s,
    )
    return _extract_response_text(completion.choices[0].message.content)


def run_task(
    env: Any,
    client: OpenAI,
    task_id: str,
    global_deadline: float,
) -> Dict[str, Any]:
    result = _run_with_timeout(
        lambda: env.reset(task_id=task_id),
        timeout_s=ENV_RESET_TIMEOUT_S,
        label=f"reset_{task_id}",
    )
    observation = result.observation
    max_steps = TASK_MAX_STEPS.get(task_id, 10)
    task_deadline = min(global_deadline, time.monotonic() + TASK_TIME_BUDGET_S)

    _log_start(f"task={task_id} max_steps={max_steps} input_records={len(observation.input_data)}")

    best_score = float(observation.current_score)
    previous_score = best_score
    no_progress_steps = 0
    consecutive_model_failures = 0

    for step in range(1, max_steps + 1):
        now = time.monotonic()
        if now >= task_deadline:
            _log_step(f"task={task_id} step={step} status=task_time_budget_exceeded")
            break
        if now >= global_deadline:
            _log_step(f"task={task_id} step={step} status=global_time_budget_exceeded")
            break

        if result.done:
            _log_step(f"task={task_id} step={step} status=done_before_next_step")
            break

        prompt = build_user_prompt(observation, step, max_steps)
        request_timeout_s = min(LLM_TIMEOUT_S, max(3.0, task_deadline - time.monotonic()))

        try:
            response_text = _request_model_output(client, prompt, timeout_s=request_timeout_s)
            cleaned_data = parse_response(response_text)
            if not cleaned_data:
                _log_step(
                    f"task={task_id} step={step} status=invalid_model_json fallback=empty_payload"
                )
            consecutive_model_failures = 0
        except Exception as exc:
            _log_step(f"task={task_id} step={step} status=model_request_failed error={exc}")
            cleaned_data = []
            consecutive_model_failures += 1
            if consecutive_model_failures >= MAX_CONSECUTIVE_MODEL_FAILURES:
                _log_step(
                    f"task={task_id} step={step} status=too_many_model_failures early_stop=true"
                )
                break

        action = DataCleanAction(data=cleaned_data)
        try:
            result = _run_with_timeout(
                lambda: env.step(action, timeout_s=ENV_STEP_TIMEOUT_S),
                timeout_s=ENV_STEP_TIMEOUT_S + 2.0,
                label=f"step_{task_id}_{step}",
            )
        except Exception as exc:
            _log_step(f"task={task_id} step={step} status=env_step_failed error={exc}")
            break
        observation = result.observation

        score = float(observation.current_score)
        best_score = max(best_score, score)
        reward = float(result.reward) if result.reward is not None else 0.0
        error_count = len(observation.validation_errors)

        if abs(score - previous_score) < 1e-6:
            no_progress_steps += 1
        else:
            no_progress_steps = 0
        previous_score = score

        _log_step(
            f"task={task_id} step={step}/{max_steps} score={score:.3f} "
            f"errors={error_count} reward={reward:.3f}"
        )

        if no_progress_steps >= MAX_NO_PROGRESS_STEPS:
            _log_step(
                f"task={task_id} step={step} status=no_progress_early_stop streak={no_progress_steps}"
            )
            break

        if score >= NEAR_PERFECT_SCORE:
            _log_step(f"task={task_id} step={step} status=near_perfect_early_stop")
            break

        if result.done:
            _log_step(f"task={task_id} step={step} status=environment_done")
            break

    _log_end(f"task={task_id} best_score={best_score:.3f}")
    return {"task_id": task_id, "best_score": best_score}


def main() -> None:
    _log_start("inference")
    _validate_required_env()

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        sys.exit("ERROR: Missing dependency 'openai'. Install it before running inference.py.")

    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
        max_retries=0,
        timeout=LLM_TIMEOUT_S,
    )
    env = _connect_env()
    global_deadline = time.monotonic() + INFERENCE_TIME_BUDGET_S

    try:
        results: List[Dict[str, Any]] = []
        for task_id in TASKS:
            if time.monotonic() >= global_deadline:
                _log_step(f"task={task_id} status=skipped_global_time_budget")
                results.append({"task_id": task_id, "best_score": 0.0})
                continue
            results.append(run_task(env, client, task_id, global_deadline=global_deadline))

        total = sum(item["best_score"] for item in results)
        average = total / len(results) if results else 0.0

        for item in results:
            _log_step(f"summary task={item['task_id']} best_score={item['best_score']:.3f}")
        _log_end(f"inference average={average:.3f}")
    finally:
        try:
            env.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
