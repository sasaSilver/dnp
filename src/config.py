from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", enable_decoding=False)
    db_uri: str
    server_addr: str
    testing: bool
    
settings = Settings()