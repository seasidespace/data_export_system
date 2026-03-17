from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Alpha Vantage
    alpha_vantage_api_key: str = "demo"
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"

    # Rate limiting (free tier: 5 calls per 60 seconds)
    rate_limit_calls: int = 5
    rate_limit_period: int = 60

    # Snowflake
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_database: str = "MARKET_ANALYTICS"
    snowflake_schema: str = "RAW"
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_role: str = "SYSADMIN"


settings = Settings()
