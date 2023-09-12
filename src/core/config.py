import pydantic_settings


class Config(pydantic_settings.BaseSettings):
    BOT_API_KEY: str
    SUP_BOT_API_KEY: str
    SUP_CHAT_ID: str
    DATABASE: str
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    PAGE_URL: str
    MAIN_URL: str
    MODELS_URL: str
    NO_MATERIAL_URL: str
    PLAYER_REF: str
    USER_AGENT_HEADER: str

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", case_sensitive=True
    )


config = Config()
