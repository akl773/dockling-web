from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TableMode = Literal["off", "fast", "accurate"]
ImageHandling = Literal["none", "referenced", "embedded"]


class ConversionSettings(BaseModel):
    ocr_enabled: bool = True
    table_mode: TableMode = "fast"
    image_handling: ImageHandling = "none"


class PartialConversionSettings(BaseModel):
    ocr_enabled: bool | None = None
    table_mode: TableMode | None = None
    image_handling: ImageHandling | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: str
    original_filename: str
    stored_pdf_path: str
    markdown_path: str
    assets_dir_path: str
    zip_entry_name: str
    status: str
    progress: int = Field(ge=0, le=100)
    settings_json: dict
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class BatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    default_settings_json: dict
    status: str
    file_count: int
    jobs: list[JobRead]


class HealthRead(BaseModel):
    status: str
