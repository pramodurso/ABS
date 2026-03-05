from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  secret_key:str
  algorithm:str
  database_username:str
  database_password:str
  database_name:str
  database_hostname:str
  database_port:str

  class Config:
    env_file=".env"


settings=Settings()