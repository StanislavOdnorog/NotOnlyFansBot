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
    USER_AGENT_HEADER: str
    NO_MATERIAL_URL: str

    PLAYER_REF: str
    PLAYER_PARAMS: str

    SUBSCRIPTION_COST: int
    PAYMENT_URL: str
    CHECK_PAYMENT_URL: str
    SHOP_ID: str
    SHOP_TOKEN: str

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", case_sensitive=True
    )


config = Config()
