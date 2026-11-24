from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_api_keys: str = ""
    llm_model: str = "gemini/gemini-2.0-flash"
    database_url: str = "sqlite:///./app.db"
    allowed_origins: str = "http://localhost:3000"
    enable_failure_simulation: bool = False

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.llm_api_keys.split(",") if k.strip()]

    @property
    def allowed_origin_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
