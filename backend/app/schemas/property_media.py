from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, HttpUrl


class PropertyMediaCreate(BaseModel):
    property_id: UUID
    url: HttpUrl
    media_type: Literal["image", "video", "floor_plan", "virtual_tour"]


class PropertyMediaResponse(BaseModel):
    id: UUID
    property_id: UUID
    url: HttpUrl
    media_type: Literal["image", "video", "floor_plan", "virtual_tour"]
    created_at: datetime

    model_config = {"from_attributes": True}
