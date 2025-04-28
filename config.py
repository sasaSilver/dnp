from pydantic_settings import BaseSettings

class Settings(BaseSettings(_env_file='.env')):
    db_uri: str