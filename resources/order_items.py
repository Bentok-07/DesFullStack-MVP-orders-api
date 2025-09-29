# resources/order_items.py
from flask_restx import Namespace, Resource, fields
from flask import request
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.models import Order, OrderItem
from services.rates import get_usd_brl_rate

ns = Namespace("order_items", description="Order Items CRUD")

# ====== Models (Swagger) ======
item_in = ns.model("OrderItemIn", {
    "sku": fields.String(required=True, example="SKU-ABC-001"),
    "description": fields.String(required=True, example="Notebook 15''"),
    "qty": fields.Integer(required=True, min=1, example=2),
    "unit_price_usd": fields.Float(required=True, min=0, example=750.0),
})

item_upd = ns.model("OrderItemUpdate", {
    "sku": fields.String(required=False, example="SKU-ABC-002"),
    "description": fields.String(required=False, example="Notebook 17''"),
    "qty": fields.Integer(required=False, min=1, example=1),
    "unit_price_usd": fields.Float(required=False, min=0, example=700.0),
})

item_out = ns.model("OrderItemOut", {
    "id": fields.Integer(example=1),
    "order_id": fields.Integer(example=123),
    "sku": fields.String(example="SKU-ABC-001"),
    "description": fields.String(example="Notebook 15''"),
    "qty": fields.Integer(example=2),
    "unit_price_usd": fields.Float(example=750.0),
    "line_total_usd": fields.Float(example=1500.0),
})

order_totals = ns.model("OrderTotals", {
    "total_usd": fields.Float(example=1500.0),
    "total_brl": fields.Float(example=8250.0),
})

resp_item_and_totals = ns.model("RespItemAndTotals", {
    "message": fields.String(example="Item added"),
    "item": fields.Nested(item_out),
    "order_totals": fields.Nested(order_totals),
})

resp_msg_and_totals = ns.model("RespMsgAndTotals", {
    "message": fields.String(example="Item updated"),
    "order_totals": fields.Nested(order_totals),
})

# ====== Helpers ======
def recalc_order(order: Order, rate: float):
    """Recalcula totais do pedido sem dar commit."""
    order.total_usd = round(sum(i.line_total_usd for i in order.items), 2)
    order.total_brl = round(order.total_usd * rate, 2)

def serialize_item(item: OrderItem):
    return {
        "id": item.id,
        "order_id": item.order_id,
        "sku": item.sku,
        "description": item.description,
        "qty": item.qty,
        "unit_price_usd": item.unit_price_usd,
        "line_total_usd": item.line_total_usd,
    }

def serialize_totals(order: Order):
    return {"total_usd": order.total_usd, "total_brl": order.total_brl}

# ====== Endpoints ======
@ns.route("/<int:order_id>/items")
class ItemList(Resource):
    @ns.expect(item_in, validate=True)
    @ns.marshal_with(resp_item_and_totals, code=201)
    def post(self, order_id):
        """Adiciona um item ao pedido e recalcula totais."""
        session: Session = SessionLocal()
        rate = get_usd_brl_rate()
        try:
            order = session.get(Order, order_id)
            if not order:
                ns.abort(404, "Order not found")

            data = request.json
            if data["qty"] < 1 or data["unit_price_usd"] < 0:
                ns.abort(400, "Invalid item values")

            item = OrderItem(
                order_id=order_id,
                sku=data["sku"],
                description=data["description"],
                qty=data["qty"],
                unit_price_usd=data["unit_price_usd"],
                line_total_usd=data["qty"] * data["unit_price_usd"],
            )
            session.add(item)

            # recálculo antes do commit
            recalc_order(order, rate)
            session.commit()
            session.refresh(item)  # garante ID

            return {
                "message": "Item added",
                "item": serialize_item(item),
                "order_totals": serialize_totals(order),
            }, 201, {
                "Location": f"/api/v1/order_items/{order_id}/items/{item.id}"
            }
        finally:
            session.close()


@ns.route("/<int:order_id>/items/<int:item_id>")
class ItemDetail(Resource):
    @ns.expect(item_upd, validate=True)
    @ns.marshal_with(resp_msg_and_totals)
    def put(self, order_id, item_id):
        """Atualiza parcialmente um item e recalcula totais (PUT comportando-se como PATCH)."""
        session: Session = SessionLocal()
        rate = get_usd_brl_rate()
        try:
            order = session.get(Order, order_id)
            if not order:
                ns.abort(404, "Order not found")

            item = session.get(OrderItem, item_id)
            if not item or item.order_id != order_id:
                ns.abort(404, "Item not found for this order")

            data = request.json or {}
            for f in ("sku", "description", "qty", "unit_price_usd"):
                if f in data:
                    if f == "qty" and data[f] is not None and data[f] < 1:
                        ns.abort(400, "qty must be >= 1")
                    if f == "unit_price_usd" and data[f] is not None and data[f] < 0:
                        ns.abort(400, "unit_price_usd must be >= 0")
                    setattr(item, f, data[f])

            # rederiva o total da linha
            item.line_total_usd = item.qty * item.unit_price_usd

            recalc_order(order, rate)
            session.commit()

            return {
                "message": "Item updated",
                "order_totals": serialize_totals(order),
            }
        finally:
            session.close()

    @ns.marshal_with(resp_msg_and_totals)
    def delete(self, order_id, item_id):
        """Remove um item do pedido e recalcula totais."""
        session: Session = SessionLocal()
        rate = get_usd_brl_rate()
        try:
            order = session.get(Order, order_id)
            if not order:
                ns.abort(404, "Order not found")

            item = session.get(OrderItem, item_id)
            if not item or item.order_id != order_id:
                ns.abort(404, "Item not found for this order")

            session.delete(item)

            recalc_order(order, rate)
            session.commit()

            return {
                "message": "Item deleted",
                "order_totals": serialize_totals(order),
            }
        finally:
            session.close()
