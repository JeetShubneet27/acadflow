from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AcadFlow API"
    environment: str = "development"
    database_url: str = "sqlite:///./acadflow.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    storage_dir: str = "./storage"
    cors_origins: str = "http://localhost:3000"
    plagiarism_base_fee_cents: int = 2500
    plagiarism_currency: str = "INR"
    payment_upi_vpa: str = "acadflow@upi"
    payment_upi_payee_name: str = "AcadFlow"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    faculty_blocked_domains: str = (
        "gmail.com,googlemail.com,yahoo.com,ymail.com,outlook.com,hotmail.com,live.com,aol.com,icloud.com"
    )
    invite_expiry_hours: int = 168
    draft_lock_minutes: int = 60
    otp_secret: str = "change-me"
    otp_expiry_minutes: int = 10
    otp_max_attempts: int = 5
    otp_cooldown_seconds: int = 60
    otp_test_mode: bool = False
    otp_test_code: str = "123456"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@acadflow.com"
    smtp_use_tls: bool = True
    smtp_suppress_send: bool = False
    smtp_timeout_seconds: int = 15
    public_plagiarism_enabled: bool = False
    latex_preview_provider: str = "none"
    latex_preview_timeout_seconds: int = 30
    word_preview_provider: str = "none"
    word_preview_timeout_seconds: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
