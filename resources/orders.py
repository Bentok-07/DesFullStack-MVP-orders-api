from flask_restx import Namespace, Resource, fields
from flask import request
from database.db import SessionLocal
from models.models import Order, OrderItem
from services.rates import get_usd_brl_rate


ns = Namespace("orders", description="Orders CRUD")

# ====== Modelos Swagger (entrada) ======
order_item_model = ns.model("OrderItem", {
    "sku": fields.String(required=True, example="SKU-ABC-001"),
    "description": fields.String(required=True, example="Notebook 15''"),
    "qty": fields.Integer(required=True, min=1, example=2),
    "unit_price_usd": fields.Float(required=True, min=0, example=750.0),
})

order_model = ns.model("Order", {
    "customer_id": fields.String(required=True, example="CUST-001"),
    "items": fields.List(fields.Nested(order_item_model), required=True,
                         description="Lista inicial de itens"),
})

order_update_model = ns.model("OrderUpdate", {
    "customer_id": fields.String(required=False, example="CUST-002"),
})

# ====== Modelos Swagger (saída) ======
order_item_out = ns.model("OrderItemOut", {
    "id": fields.Integer(example=1),
    "sku": fields.String(example="SKU-ABC-001"),
    "description": fields.String(example="Notebook 15''"),
    "qty": fields.Integer(example=2),
    "unit_price_usd": fields.Float(example=750.0),
    "line_total_usd": fields.Float(example=1500.0),
})

order_summary = ns.model("OrderSummary", {
    "id": fields.Integer(example=1),
    "customer_id": fields.String(example="CUST-001"),
    "total_usd": fields.Float(example=1550.0),
    "status": fields.String(example="PENDING"),
})

order_out = ns.model("OrderOut", {
    "id": fields.Integer(example=1),
    "customer_id": fields.String(example="CUST-001"),
    "total_usd": fields.Float(example=1550.0),
    "total_brl": fields.Float(example=0.0),
    "created_at": fields.String(example="2025-09-03T12:34:56"),
    "items": fields.List(fields.Nested(order_item_out)),
    'status': fields.String,
})

# ====== Helpers ======
def calc_totals(order: Order):
    order.total_usd = round(sum(item.line_total_usd for item in order.items), 2)
    rate = get_usd_brl_rate()
    order.total_brl = round(order.total_usd * rate, 2)
    print(f"[calc_totals] USD={order.total_usd} rate={rate} BRL={order.total_brl}")
    return order


def serialize_order(order: Order):
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "total_usd": order.total_usd,
        "total_brl": order.total_brl,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "status": order.status,
        "items": [
            {
                "id": i.id,
                "sku": i.sku,
                "description": i.description,
                "qty": i.qty,
                "unit_price_usd": i.unit_price_usd,
                "line_total_usd": i.line_total_usd,
            } for i in order.items
        ],
    }

# ====== Endpoints ======
@ns.route("")
class OrderList(Resource):
    @ns.expect(order_model, validate=True)
    @ns.marshal_with(order_out, code=201)
    def post(self):
        data = request.json
        if not data.get("items"):
            return {"error": "At least one item is required"}, 400

        session = SessionLocal()
        order = Order(customer_id=data["customer_id"], status="PENDING")

        for item in data["items"]:
            if item["qty"] < 1 or item["unit_price_usd"] < 0:
                return {"error": "Invalid item values"}, 400
            line_total = item["qty"] * item["unit_price_usd"]
            order.items.append(OrderItem(
                sku=item["sku"],
                description=item["description"],
                qty=item["qty"],
                unit_price_usd=item["unit_price_usd"],
                line_total_usd=line_total
            ))

        calc_totals(order)
        session.add(order)
        session.commit()
        session.refresh(order)
        return serialize_order(order), 201

    @ns.marshal_list_with(order_summary)
    def get(self):
        session = SessionLocal()  
        try:
            customer_id = request.args.get("customer_id")

            q = session.query(Order)
            if customer_id:
                q = q.filter(Order.customer_id == customer_id)

            orders = q.order_by(Order.id.asc()).all()
            return [
                {
                    "id": o.id,
                    "customer_id": o.customer_id,
                    "total_usd": o.total_usd,
                    "status": o.status,
                }
                for o in orders
            ], 200
        finally:
            session.close()


@ns.route("/<int:order_id>")
class OrderDetail(Resource):
    @ns.marshal_with(order_out)
    def get(self, order_id):
        session = SessionLocal()
        order = session.get(Order, order_id)
        if not order:
            ns.abort(404, "Order not found")
        return serialize_order(order)

    @ns.expect(order_update_model, validate=True)
    @ns.marshal_with(order_out)
    def put(self, order_id):
        data = request.json or {}
        session = SessionLocal()
        order = session.get(Order, order_id)
        if not order:
            ns.abort(404, "Order not found")

        if "customer_id" in data:
            order.customer_id = data["customer_id"]

        session.commit()
        session.refresh(order)
        return serialize_order(order)

    @ns.doc(responses={200: "Order deleted", 404: "Order not found"})
    def delete(self, order_id):
        session = SessionLocal()
        order = session.get(Order, order_id)
        if not order:
            return {"error": "Order not found"}, 404
        if getattr(order, "status", None) != "PENDING":
            return {"error": "Only PENDING orders can be deleted"}, 409
        session.delete(order)
        session.commit()
        return {"message": "Order deleted"}, 200
