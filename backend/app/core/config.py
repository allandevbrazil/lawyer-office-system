from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    local_database_url: str | None = Field(
        default="postgresql+asyncpg://lawfirm:change-me@localhost:5433/lawfirm",
        alias="LOCAL_DATABASE_URL",
    )
    neon_database_url: str | None = Field(default=None, alias="NEON_DATABASE_URL")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    frontend_base_url: str = Field(default="http://localhost:5173", alias="FRONTEND_BASE_URL")
    render_external_url: str | None = Field(default=None, alias="RENDER_EXTERNAL_URL")
    jwt_secret_key: str = Field(
        default="dev-only-change-me-with-at-least-32-bytes", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=4320, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=3, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    refresh_cookie_name: str = Field(default="lawfirm_refresh", alias="REFRESH_COOKIE_NAME")
    initial_master_email: str | None = Field(default=None, alias="INITIAL_MASTER_EMAIL")
    initial_master_password: str | None = Field(default=None, alias="INITIAL_MASTER_PASSWORD")
    initial_firm_name: str = Field(default="LawFirm Demo", alias="INITIAL_FIRM_NAME")
    initial_employee_email: str = Field(
        default="ana.silva@example.com", alias="INITIAL_EMPLOYEE_EMAIL"
    )
    initial_employee_password: str = Field(
        default="Demo@123456", alias="INITIAL_EMPLOYEE_PASSWORD"
    )
    initial_client_email: str = Field(
        default="mariana.costa@example.com", alias="INITIAL_CLIENT_EMAIL"
    )
    initial_client_password: str = Field(
        default="Client@123456", alias="INITIAL_CLIENT_PASSWORD"
    )
    resend_api_key: str | None = Field(default=None, alias="RESEND_API_KEY")
    resend_from_email: str | None = Field(default=None, alias="RESEND_FROM_EMAIL")
    local_storage_path: str = Field(default=".local-storage", alias="LOCAL_STORAGE_PATH")
    max_upload_size_bytes: int = Field(default=10_485_760, alias="MAX_UPLOAD_SIZE_BYTES")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        is_production = self.app_env.lower() in {"production", "prod"}
        configured_url = (
            self.neon_database_url if is_production else self.local_database_url
        ) or self.database_url
        if not configured_url:
            target = "NEON_DATABASE_URL" if is_production else "LOCAL_DATABASE_URL"
            raise RuntimeError(f"{target} não está configurada para APP_ENV={self.app_env}.")
        if configured_url.startswith("postgres://") or configured_url.startswith("postgresql://"):
            configured_url = configured_url.replace("postgres://", "postgresql+asyncpg://", 1).replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        parsed = urlsplit(configured_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        ssl_mode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if ssl_mode:
            query["ssl"] = "require" if ssl_mode in {"require", "verify-ca", "verify-full"} else "disable"
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


@lru_cache
def get_settings() -> Settings:
    return Settings()
