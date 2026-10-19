from pydantic import BaseModel, Field,field_validator
from typing import Literal
import re

class LeadRequest(BaseModel):
    name: str
    phone: str
    interest: Literal["subscription", "one_off", "question"]
    comment: str | None
    utm_source: str | None = Field(default=None, max_length=200)
    utm_campaign: str | None = Field(default=None, max_length=200)
    utm_content: str | None = Field(default=None, max_length=200)
    landing_page: str | None = Field(default=None, max_length=500)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(r"\+375\d{9}", value):
            raise ValueError("Неккоректный номер(doesn't from Belarus. PS: +375XXXXXXXXX)")
        return value

