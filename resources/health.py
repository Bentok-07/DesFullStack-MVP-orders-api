# resources/health.py
from flask_restx import Namespace, Resource
from services.rates import get_usd_brl_rate

ns = Namespace("health", description="Diagnostics")

@ns.route("/rate")
class Rate(Resource):
    def get(self):
        rate = get_usd_brl_rate()
        return {"rate": float(rate)}, 200
