# app.py (Orders)
import os
from dotenv import load_dotenv

from flask import Flask
from flask_cors import CORS
from flask_restx import Api

from database.db import init_db   

from resources.health import ns as health_ns
from resources.orders import ns as orders_ns
from resources.order_items import ns as order_items_ns

load_dotenv() 


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["ERROR_404_HELP"] = False
    app.config["TESTING"] = testing

    api = Api(
        app,
        version="1.0",
        title="Orders API",
        description="CRUD de pedidos e itens; conversão de câmbio no backend.",
        doc="/docs",
        prefix="/api/v1",
    )

    # CORS totalmente aberto (ambiente local/dev)
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=False,
    )

    # Namespaces — sem path manual (herdam prefixo /api/v1)
    api.add_namespace(health_ns)       # → /api/v1/health
    api.add_namespace(orders_ns)       # → /api/v1/orders
    api.add_namespace(order_items_ns)  # → /api/v1/orders/{id}/items 

    # Inicialização de banco (apenas fora de testes)
    if not testing:
        init_db()

    return app


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5001))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)
