from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database.db import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(64), nullable=False)
    total_usd = Column(Float, default=0.0, nullable=False)
    total_brl = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(64), nullable=False)
    description = Column(String(255), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    line_total_usd = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
