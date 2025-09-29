import os, requests

def get_usd_brl_rate() -> float:
    url = os.getenv("EXTERNAL_RATE_URL", "https://economia.awesomeapi.com.br/json/last/USD-BRL")
    fallback = float(os.getenv("FALLBACK_USD_BRL", "1.00"))
    try:
        resp = requests.get(url, timeout=3)
        resp.raise_for_status()
        data = resp.json()

        bid = None
        # Formato comum da AwesomeAPI: {"USDBRL":{"bid":"5.1234", ...}}
        if isinstance(data, dict):
            if "USDBRL" in data and isinstance(data["USDBRL"], dict) and "bid" in data["USDBRL"]:
                bid = data["USDBRL"]["bid"]
            else:
                # tenta achar o primeiro dict com "bid"
                for v in data.values():
                    if isinstance(v, dict) and "bid" in v:
                        bid = v["bid"]
                        break
        # Alguns provedores retornam lista [{"bid": "..."}]
        if bid is None and isinstance(data, list) and data and isinstance(data[0], dict) and "bid" in data[0]:
            bid = data[0]["bid"]

        rate = float(str(bid).replace(",", ".")) if bid is not None else None
        if not rate or rate <= 0:
            return fallback
        return rate
    except Exception:
        return fallback
