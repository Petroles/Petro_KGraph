from pathlib import Path

from pydantic import BaseSettings, Field

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    MERGED_COLLECTION_FILENAME: str = Field(default="MERGED_COLLECTIONS.json")
    SKOS_FILENAME: str = Field(default="SKOS_Tulsa.nt")
    OIL_WELL_FILENAME: str = Field(default="06_Termos_TabelaPocosANP2019.csv")
    DATA_DIR: str = Field(default=f"{BASE_DIR}/bases")
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/")
    MONGODB_DATABASE_NAME: str = Field(default="fy3a")
    MONGODB_COLLECTION_NAME: str = Field(default="termsBase")

    class Config:
        env_file = f"{BASE_DIR}/.env"


settings = Settings()
