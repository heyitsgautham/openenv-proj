"""FastAPI application scaffold for the Data Cleaning environment."""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv is required. Install dependencies with 'uv sync'.") from e

try:
    from ..models import DataCleanAction, DataCleanObservation, DataCleanState
except ModuleNotFoundError:
    from models import DataCleanAction, DataCleanObservation, DataCleanState


class DataCleanEnvironment:
    """Session 1 placeholder environment implementation."""

    def __init__(self) -> None:
        self._state = DataCleanState(episode_id="", step_count=0)

    def reset(self, *args, **kwargs) -> DataCleanObservation:
        self._state = DataCleanState(episode_id=self._state.episode_id, step_count=0)
        return DataCleanObservation(
            task_description="Session 1 scaffold placeholder",
            input_data=[],
            target_schema={},
            validation_errors=[],
            current_score=0.0,
            done=False,
            reward=0.0,
            metadata={"status": "scaffold"},
        )

    def step(self, action: DataCleanAction, *args, **kwargs) -> DataCleanObservation:
        self._state.step_count += 1
        return DataCleanObservation(
            task_description="Session 1 scaffold placeholder",
            input_data=action.data,
            target_schema={},
            validation_errors=["Environment logic is implemented in Session 2."],
            current_score=0.0,
            done=True,
            reward=0.0,
            metadata={"status": "scaffold", "step": self._state.step_count},
        )

    @property
    def state(self) -> DataCleanState:
        return self._state


app = create_app(
    DataCleanEnvironment,
    DataCleanAction,
    DataCleanObservation,
    env_name="data_cleaning_env",
    max_concurrent_envs=1,
)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Entrypoint used by the `server` script in pyproject.toml."""

    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
