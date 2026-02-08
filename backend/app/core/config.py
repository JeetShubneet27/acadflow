from pydantic import BaseSettings


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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
