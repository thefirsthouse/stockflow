import datetime

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, ChoiceType


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[int] = mapped_column(String, index=True, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=True)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    location: Mapped[str] = mapped_column(String)


class StockMovement(Base):
    __tablename__ = "stock-movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'))
    warehouse: Mapped[int] = mapped_column(Integer, ForeignKey('warehouses.id'))
    movement_type: Mapped[str] = mapped_column(String, ChoiceType({"in": "IN", "out": "OUT"}), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    comment: Mapped[str] = mapped_column(String)

