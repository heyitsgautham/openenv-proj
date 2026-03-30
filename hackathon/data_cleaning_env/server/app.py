"""FastAPI application scaffold for the Data Cleaning environment."""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv is required. Install dependencies with 'uv sync'.") from e

try:
    from ..models import DataCleanAction, DataCleanObservation
    from .data_cleaning_environment import DataCleanEnvironment
except (ModuleNotFoundError, ImportError):
    from models import DataCleanAction, DataCleanObservation
    from server.data_cleaning_environment import DataCleanEnvironment


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
    if args.port == 8000:
        main()
    else:
        main(port=args.port)
