"""
ETL — Projeto de Análise de Dados de E-commerce (Olist)

Extract  -> lê os CSVs brutos em data/raw/
Transform -> corrige tipos de data, remove duplicatas, trata nulos
Load     -> envia cada tabela para o MySQL (banco olist_ecommerce)

Como rodar:
    python src/etl.py

Pré-requisitos:
    - MySQL rodando localmente com o banco criado (rode sql/schema.sql antes)
    - Variáveis de conexão configuradas abaixo (ou via variáveis de ambiente)
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# --------------------------------------------------------------------------
# Configuração de conexão
# Troque MYSQL_PASSWORD pela sua senha real, ou exporte a variável de ambiente
# antes de rodar: export MYSQL_PASSWORD="sua_senha"
# --------------------------------------------------------------------------
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "SUA_SENHA")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "olist_ecommerce")

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw") + os.sep


def extract():
    """Lê os 7 CSVs originais do dataset Olist."""
    print("[1/3] Extract — lendo os CSVs...")
    customers = pd.read_csv(RAW_PATH + "olist_customers_dataset.csv")
    orders = pd.read_csv(RAW_PATH + "olist_orders_dataset.csv")
    items = pd.read_csv(RAW_PATH + "olist_order_items_dataset.csv")
    payments = pd.read_csv(RAW_PATH + "olist_order_payments_dataset.csv")
    reviews = pd.read_csv(RAW_PATH + "olist_order_reviews_dataset.csv")
    products = pd.read_csv(RAW_PATH + "olist_products_dataset.csv")
    sellers = pd.read_csv(RAW_PATH + "olist_sellers_dataset.csv")
    print(f"   customers={len(customers)}  orders={len(orders)}  items={len(items)}  "
          f"payments={len(payments)}  reviews={len(reviews)}  products={len(products)}  "
          f"sellers={len(sellers)}")
    return customers, orders, items, payments, reviews, products, sellers


def transform(customers, orders, items, payments, reviews, products, sellers):
    """Corrige tipos, remove duplicatas e trata valores nulos."""
    print("[2/3] Transform — limpando os dados...")

    # --- datas: de texto (object) para datetime de verdade ---
    colunas_de_data = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for coluna in colunas_de_data:
        orders[coluna] = pd.to_datetime(orders[coluna], errors="coerce")

    reviews["review_creation_date"] = pd.to_datetime(
        reviews["review_creation_date"], errors="coerce"
    )

    # --- duplicatas ---
    customers = customers.drop_duplicates(subset="customer_id")
    products = products.drop_duplicates(subset="product_id")
    sellers = sellers.drop_duplicates(subset="seller_id")
    reviews = reviews.drop_duplicates(subset="review_id")
    orders = orders.drop_duplicates(subset="order_id")

    # --- nulos ---
    products["product_category_name"] = products["product_category_name"].fillna(
        "nao_informado"
    )

    # --- mantendo só as colunas que interessam (bate com o schema.sql) ---
    products = products[[
        "product_id", "product_category_name", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm",
    ]]
    reviews = reviews[[
        "review_id", "order_id", "review_score",
        "review_comment_title", "review_comment_message", "review_creation_date",
    ]]

    # --- integridade referencial: garante que só entram linhas cujas FKs existem ---
    valid_customers = set(customers["customer_id"])
    orders = orders[orders["customer_id"].isin(valid_customers)]

    valid_orders = set(orders["order_id"])
    items = items[items["order_id"].isin(valid_orders)]
    payments = payments[payments["order_id"].isin(valid_orders)]
    reviews = reviews[reviews["order_id"].isin(valid_orders)]

    valid_products = set(products["product_id"])
    valid_sellers = set(sellers["seller_id"])
    items = items[items["product_id"].isin(valid_products) & items["seller_id"].isin(valid_sellers)]

    print(f"   após limpeza: customers={len(customers)}  orders={len(orders)}  "
          f"items={len(items)}  payments={len(payments)}  reviews={len(reviews)}  "
          f"products={len(products)}  sellers={len(sellers)}")

    return customers, orders, items, payments, reviews, products, sellers


def load(customers, orders, items, payments, reviews, products, sellers):
    """Envia cada tabela para o MySQL, respeitando a ordem das foreign keys."""
    print("[3/3] Load — enviando para o MySQL...")
    conn_str = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    engine = create_engine(conn_str)

    # 1º as tabelas "independentes"
    customers.to_sql("customers", engine, if_exists="append", index=False)
    sellers.to_sql("sellers", engine, if_exists="append", index=False)
    products.to_sql("products", engine, if_exists="append", index=False)

    # 2º orders (depende de customers já existir)
    orders.to_sql("orders", engine, if_exists="append", index=False)

    # 3º as que dependem de orders
    items.to_sql("order_items", engine, if_exists="append", index=False)
    payments.to_sql("order_payments", engine, if_exists="append", index=False)
    reviews.to_sql("order_reviews", engine, if_exists="append", index=False)

    print("ETL concluído com sucesso!")


if __name__ == "__main__":
    dados = extract()
    dados_limpos = transform(*dados)
    load(*dados_limpos)
