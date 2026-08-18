"""
Roda as consultas de negócio (sql/queries.sql) direto no MySQL e salva
cada resultado como um .tsv em analysis/ — esses arquivos alimentam o
analysis/build_dashboard_images.py.

Como rodar (depois do ETL já ter sido executado):
    export MYSQL_PASSWORD="sua_senha"
    python analysis/run_queries.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "SUA_SENHA")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "olist_ecommerce")

OUT_DIR = os.path.dirname(__file__) or "."

QUERIES = {
    "q1_receita_mensal.tsv": """
        SELECT DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS mes,
               ROUND(SUM(oi.price), 2) AS receita
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY mes ORDER BY mes;
    """,
    "q2_top_categorias.tsv": """
        SELECT p.product_category_name AS categoria,
               ROUND(SUM(oi.price), 2) AS receita,
               COUNT(*) AS qtd
        FROM order_items oi JOIN products p ON oi.product_id = p.product_id
        GROUP BY categoria ORDER BY receita DESC LIMIT 10;
    """,
    "q3_tempo_entrega_estado.tsv": """
        SELECT c.customer_state AS estado,
               ROUND(AVG(DATEDIFF(o.order_delivered_customer_date, o.order_purchase_timestamp)), 1) AS dias
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY estado ORDER BY dias DESC;
    """,
    "q4_atraso_vs_nota.tsv": """
        SELECT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                    THEN 'Atrasado' ELSE 'No prazo' END AS status_entrega,
               ROUND(AVG(r.review_score), 2) AS nota_media,
               COUNT(*) AS qtd
        FROM orders o JOIN order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY status_entrega;
    """,
    "q5_metodos_pagamento.tsv": """
        SELECT payment_type AS metodo, COUNT(*) AS qtd,
               ROUND(SUM(payment_value), 2) AS valor_total
        FROM order_payments GROUP BY metodo ORDER BY qtd DESC;
    """,
    "q6_pedidos_por_estado.tsv": """
        SELECT c.customer_state AS estado,
               COUNT(DISTINCT o.order_id) AS qtd_pedidos,
               ROUND(SUM(oi.price), 2) AS receita
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY estado ORDER BY receita DESC;
    """,
    "q7_kpis.tsv": """
        SELECT COUNT(DISTINCT o.order_id) AS total_pedidos,
               ROUND(SUM(oi.price), 2) AS receita_total,
               ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS ticket_medio,
               ROUND(AVG(r.review_score), 2) AS nota_media
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered';
    """,
}


def main():
    conn_str = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    engine = create_engine(conn_str)

    with engine.connect() as conn:
        for filename, query in QUERIES.items():
            df = pd.read_sql(text(query), conn)
            out_path = os.path.join(OUT_DIR, filename)
            df.to_csv(out_path, sep="\t", index=False)
            print(f"  {filename:<32} -> {len(df)} linhas")

    print("\nTodas as queries rodaram e foram exportadas para analysis/*.tsv")
    print("Agora rode: python analysis/build_dashboard_images.py")


if __name__ == "__main__":
    main()
