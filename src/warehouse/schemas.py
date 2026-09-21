from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MovementType(str, Enum):
    in_ = "IN"
    out = "OUT"


class ProductBaseSchema(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=255)


class ProductCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(default=None, min_length=1, max_length=255)
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(default=None, min_length=1, max_length=100)


class ProductUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, min_length=1, max_length=100)


class ProductReadSchema(ProductBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class WarehouseBaseSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=255)


class WarehouseCreateSchema(WarehouseBaseSchema):
    pass


class WarehouseUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=255)


class WarehouseReadSchema(WarehouseBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class StockMovementBaseSchema(BaseModel):
    product: int = Field(..., gt=0)
    warehouse: int = Field(..., gt=0)
    movement_type: MovementType
    quantity: int = Field(..., gt=0)
    comment: str = ""


class StockMovementCreateSchema(StockMovementBaseSchema):
    pass


class StockMovementUpdateSchema(BaseModel):
    product: int | None = Field(default=None, gt=0)
    warehouse: int | None = Field(default=None, gt=0)
    movement_type: MovementType | None = None
    quantity: int | None = Field(default=None, gt=0)
    comment: str | None = None


class StockMovementReadSchema(StockMovementBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class StockItemBaseSchema(BaseModel):
    product: int = Field(..., gt=0)
    warehouse: int = Field(..., gt=0)
    quantity: int = Field(..., ge=0)


class StockItemCreateSchema(StockItemBaseSchema):
    pass


class StockItemUpdateSchema(BaseModel):
    product: int | None = Field(default=None, gt=0)
    warehouse: int | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=0)


class StockItemReadSchema(StockItemBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
