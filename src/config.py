import pydantic_settings


class Config(pydantic_settings.BaseSettings):
    BOT_API_KEY: str
    DATABASE: str
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    PAGE_URL: str
    MAIN_URL: str
    MODELS_URL: str

    model_config = pydantic_settings.SettingsConfigDict(
        env_file="../.env", case_sensitive=True
    )


config = Config()
