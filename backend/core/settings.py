from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AgentForge"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    llm_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "NULL"
    llm_model: str = "local-model"
    llm_temperature: float = 0.1
    llm_timeout: int = 600

    database_url: str = "sqlite:///./agentforge.db"
    workspace_dir: str = "./backend/workspace"

    model_config = {"env_file": ".env"}


settings = Settings()
