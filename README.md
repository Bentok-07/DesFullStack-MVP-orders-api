
# `orders-api/README.md`

# Orders API

API REST em Flask-RESTX para **pedidos** e **itens de pedido**. Integra com **API pública de câmbio USD→BRL** e possui **fallback** configurável por variável de ambiente.

## Como executar com Docker

mkdir .data -Force
docker build -t orders-api .
docker run --name orders-api --rm -p 5001:5001 -e ORDERS_DB_PATH=/data/orders.db -v "${PWD}/.data:/data" orders-api
