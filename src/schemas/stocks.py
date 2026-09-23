from pydantic import BaseModel, Field, field_validator


def normalize_symbol(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Symbol must be a string")
    return value.strip().upper()


class SymbolRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, pattern=r"^[A-Z0-9]+$")
    normalize = field_validator("symbol", mode="before")(normalize_symbol)


class SymbolValidation(BaseModel):
    symbol: str
    valid: bool | None = None
    status: str = "not_implemented"
    message: str = "Provider validation is not implemented in Day 0."
