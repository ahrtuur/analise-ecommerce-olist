"""
Gera um dataset SINTÉTICO com a mesma estrutura (colunas e tipos) do
Brazilian E-Commerce Public Dataset by Olist (Kaggle).

Por que isso existe:
Este ambiente não tem acesso ao Kaggle para baixar o dataset real.
Para entregar o projeto FUNCIONANDO de ponta a ponta (ETL -> MySQL -> SQL -> BI),
geramos aqui um dataset artificial, mas realista, com o MESMO formato de colunas,
os mesmos tipos de sujeira de dados (nulos, datas como texto, duplicatas) e
os mesmos padrões de negócio (sazonalidade, atraso de entrega afetando avaliação etc).

Quando você quiser usar o dataset REAL:
1. Baixe em https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Substitua os arquivos em data/raw/ pelos CSVs baixados
3. Rode o ETL (src/etl.py) normalmente -- nada mais muda, porque as colunas
   têm exatamente os mesmos nomes do dataset real.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N_CUSTOMERS = 3000
N_SELLERS = 300
N_PRODUCTS = 600
N_ORDERS = 5200

OUT_DIR = "raw/"

# ---------------------------------------------------------------------------
# Referência geográfica (estados reais do Brasil, com peso proporcional
# parecido com a distribuição real da Olist -- SP concentra a maior fatia)
# ---------------------------------------------------------------------------
STATES = {
    "SP": ("São Paulo", 0.42), "RJ": ("Rio de Janeiro", 0.13),
    "MG": ("Belo Horizonte", 0.11), "RS": ("Porto Alegre", 0.055),
    "PR": ("Curitiba", 0.05), "SC": ("Florianópolis", 0.035),
    "BA": ("Salvador", 0.035), "DF": ("Brasília", 0.02),
    "GO": ("Goiânia", 0.02), "ES": ("Vitória", 0.02),
    "PE": ("Recife", 0.02), "CE": ("Fortaleza", 0.018),
    "PA": ("Belém", 0.012), "MT": ("Cuiabá", 0.01),
    "MA": ("São Luís", 0.008), "MS": ("Campo Grande", 0.008),
    "PB": ("João Pessoa", 0.007), "PI": ("Teresina", 0.006),
    "RN": ("Natal", 0.006), "AL": ("Maceió", 0.005),
    "SE": ("Aracaju", 0.004), "AM": ("Manaus", 0.006),
    "RO": ("Porto Velho", 0.003), "TO": ("Palmas", 0.003),
    "AC": ("Rio Branco", 0.002), "AP": ("Macapá", 0.002),
    "RR": ("Boa Vista", 0.001),
}
state_codes = list(STATES.keys())
state_weights = np.array([v[1] for v in STATES.values()])
state_weights = state_weights / state_weights.sum()

CATEGORIES = [
    "cama_mesa_banho", "beleza_saude", "esporte_lazer", "moveis_decoracao",
    "informatica_acessorios", "utilidades_domesticas", "relogios_presentes",
    "telefonia", "automotivo", "brinquedos", "cool_stuff",
    "ferramentas_jardim", "perfumaria", "bebes", "eletronicos",
    "papelaria", "fashion_bolsas_acessorios", "pet_shop",
    "moveis_escritorio", "construcao_ferramentas", "livros", "market_place",
]

PAYMENT_TYPES = ["credit_card", "boleto", "voucher", "debit_card"]
PAYMENT_WEIGHTS = [0.73, 0.19, 0.05, 0.03]

# ---------------------------------------------------------------------------
# customers
# ---------------------------------------------------------------------------
def make_ids(n, prefix):
    return [f"{prefix}{i:07d}{random.randint(1000,9999)}" for i in range(n)]

customer_ids = make_ids(N_CUSTOMERS, "cust_")
customer_unique_ids = make_ids(N_CUSTOMERS, "uniq_")
cust_state_choice = np.random.choice(state_codes, size=N_CUSTOMERS, p=state_weights)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "customer_unique_id": customer_unique_ids,
    "customer_zip_code_prefix": np.random.randint(1000, 99999, size=N_CUSTOMERS),
    "customer_city": [STATES[s][0] for s in cust_state_choice],
    "customer_state": cust_state_choice,
})
# sujeira proposital: alguns zip codes nulos, algumas duplicatas de customer_id
customers.loc[customers.sample(frac=0.01, random_state=1).index, "customer_zip_code_prefix"] = np.nan
dup_rows = customers.sample(frac=0.005, random_state=2)
customers = pd.concat([customers, dup_rows], ignore_index=True)

# ---------------------------------------------------------------------------
# sellers
# ---------------------------------------------------------------------------
seller_ids = make_ids(N_SELLERS, "sell_")
seller_state_choice = np.random.choice(state_codes, size=N_SELLERS, p=state_weights)
sellers = pd.DataFrame({
    "seller_id": seller_ids,
    "seller_zip_code_prefix": np.random.randint(1000, 99999, size=N_SELLERS),
    "seller_city": [STATES[s][0] for s in seller_state_choice],
    "seller_state": seller_state_choice,
})

# ---------------------------------------------------------------------------
# products
# ---------------------------------------------------------------------------
product_ids = make_ids(N_PRODUCTS, "prod_")
prod_categories = np.random.choice(CATEGORIES, size=N_PRODUCTS)
products = pd.DataFrame({
    "product_id": product_ids,
    "product_category_name": prod_categories,
    "product_weight_g": np.round(np.random.gamma(3, 400, size=N_PRODUCTS), 0),
    "product_length_cm": np.round(np.random.uniform(5, 100, size=N_PRODUCTS), 1),
    "product_height_cm": np.round(np.random.uniform(2, 60, size=N_PRODUCTS), 1),
    "product_width_cm": np.round(np.random.uniform(5, 80, size=N_PRODUCTS), 1),
})
# sujeira: 3% das categorias vazias (comum no dataset real)
products.loc[products.sample(frac=0.03, random_state=3).index, "product_category_name"] = np.nan
dup_products = products.sample(frac=0.004, random_state=4)
products = pd.concat([products, dup_products], ignore_index=True)

# ---------------------------------------------------------------------------
# orders (+ sazonalidade: pico em nov/dez, crescimento ao longo do tempo)
# ---------------------------------------------------------------------------
start_date = datetime(2016, 9, 1)
end_date = datetime(2018, 8, 31)
total_days = (end_date - start_date).days

# distribuição de compras: tendência de crescimento + pico sazonal novembro
day_offsets = []
weights = []
for d in range(total_days):
    date = start_date + timedelta(days=d)
    growth = 1 + (d / total_days) * 2.2          # cresce ao longo do tempo
    seasonal = 2.6 if date.month == 11 else (1.6 if date.month == 12 else 1.0)
    weekday_boost = 1.15 if date.weekday() < 5 else 0.8
    weights.append(growth * seasonal * weekday_boost)
    day_offsets.append(d)
weights = np.array(weights) / np.sum(weights)

order_ids = make_ids(N_ORDERS, "ord_")
chosen_days = np.random.choice(day_offsets, size=N_ORDERS, p=weights)
purchase_ts = [start_date + timedelta(days=int(d), hours=random.randint(0, 23),
                                       minutes=random.randint(0, 59)) for d in chosen_days]

order_customer_ids = np.random.choice(customer_ids, size=N_ORDERS, replace=True)

statuses = np.random.choice(
    ["delivered", "shipped", "canceled", "processing", "unavailable"],
    size=N_ORDERS, p=[0.94, 0.03, 0.015, 0.01, 0.005]
)

approved_at, carrier_date, delivered_date, estimated_date = [], [], [], []
# estado do cliente por pedido, para simular atraso maior em estados distantes
cust_state_map = dict(zip(customers["customer_id"], customers["customer_state"]))
order_cust_state = np.array([cust_state_map.get(cid, "SP") for cid in order_customer_ids])
FAR_STATES = {"AM", "RR", "AP", "AC", "RO", "PA", "MA", "PI", "TO", "MT", "MS"}

for i in range(N_ORDERS):
    p = purchase_ts[i]
    appr = p + timedelta(hours=random.randint(1, 48))
    approved_at.append(appr)

    far = order_cust_state[i] in FAR_STATES
    handling = random.randint(1, 3)
    carrier = appr + timedelta(days=handling)
    carrier_date.append(carrier)

    base_transit = random.randint(9, 15) if far else random.randint(3, 9)
    # 22% das entregas atrasam de propósito (pra dar sinal de negócio real no BI)
    delay_extra = random.randint(4, 12) if random.random() < 0.22 else 0
    delivered = carrier + timedelta(days=base_transit + delay_extra)

    est = p + timedelta(days=random.randint(12, 20) if far else random.randint(7, 14))

    if statuses[i] != "delivered":
        delivered_date.append(pd.NaT)
    else:
        delivered_date.append(delivered)
    estimated_date.append(est)

orders = pd.DataFrame({
    "order_id": order_ids,
    "customer_id": order_customer_ids,
    "order_status": statuses,
    "order_purchase_timestamp": purchase_ts,
    "order_approved_at": approved_at,
    "order_delivered_carrier_date": carrier_date,
    "order_delivered_customer_date": delivered_date,
    "order_estimated_delivery_date": estimated_date,
})
# sujeira: datas como texto (object) propositalmente formatadas de forma "suja"
for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
            "order_estimated_delivery_date"]:
    orders[col] = orders[col].astype(str)
orders["order_delivered_customer_date"] = orders["order_delivered_customer_date"].apply(
    lambda x: str(x) if pd.notna(x) else ""
)
# alguns approved_at nulos (comum no dataset real)
null_idx = orders.sample(frac=0.008, random_state=5).index
orders.loc[null_idx, "order_approved_at"] = ""

# ---------------------------------------------------------------------------
# order_items (1 a 3 itens por pedido)
# ---------------------------------------------------------------------------
items_rows = []
category_price = {c: round(np.random.uniform(25, 320), 2) for c in CATEGORIES}
for oid in order_ids:
    n_items = np.random.choice([1, 1, 1, 2, 2, 3], 1)[0]
    for item_num in range(1, n_items + 1):
        prod = random.choice(product_ids)
        # nem todo product_id sujo tem categoria válida -- ok, fica realista
        cat_row = products.loc[products["product_id"] == prod, "product_category_name"]
        cat = cat_row.values[0] if len(cat_row) else random.choice(CATEGORIES)
        base_price = category_price.get(cat, 90.0) if pd.notna(cat) else 90.0
        price = round(max(9.9, np.random.normal(base_price, base_price * 0.35)), 2)
        freight = round(max(6.5, np.random.normal(18, 7)), 2)
        seller = random.choice(seller_ids)
        items_rows.append((oid, item_num, prod, seller, price, freight))

items = pd.DataFrame(items_rows, columns=[
    "order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"
])

# ---------------------------------------------------------------------------
# order_payments
# ---------------------------------------------------------------------------
pay_rows = []
order_total = items.groupby("order_id")["price"].sum().to_dict()
order_freight_total = items.groupby("order_id")["freight_value"].sum().to_dict()
for oid in order_ids:
    total = round(order_total.get(oid, 0) + order_freight_total.get(oid, 0), 2)
    if total <= 0:
        continue
    ptype = np.random.choice(PAYMENT_TYPES, p=PAYMENT_WEIGHTS)
    installments = 1
    if ptype == "credit_card":
        installments = int(np.random.choice(range(1, 13), p=[0.28,0.15,0.13,0.11,0.09,0.07,0.05,0.04,0.03,0.02,0.02,0.01]))
    pay_rows.append((oid, 1, ptype, installments, total))

payments = pd.DataFrame(pay_rows, columns=[
    "order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"
])

# ---------------------------------------------------------------------------
# order_reviews (nota correlacionada com atraso de entrega)
# ---------------------------------------------------------------------------
orders_idx = orders.set_index("order_id")
review_rows = []
for oid in order_ids:
    row = orders_idx.loc[oid]
    if row["order_status"] != "delivered" or row["order_delivered_customer_date"] == "":
        # ainda pode existir review em pedido não entregue (raro), mas vamos pular a maioria
        if random.random() > 0.05:
            continue
        score = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
    else:
        try:
            delivered = pd.to_datetime(row["order_delivered_customer_date"])
            estimated = pd.to_datetime(row["order_estimated_delivery_date"])
            late = delivered > estimated
        except Exception:
            late = False
        if late:
            score = np.random.choice([1, 2, 3, 4, 5], p=[0.38, 0.27, 0.18, 0.11, 0.06])
        else:
            score = np.random.choice([1, 2, 3, 4, 5], p=[0.03, 0.05, 0.12, 0.28, 0.52])

    rid = f"rev_{random.randint(100000,999999)}{random.randint(100,999)}"
    title = "" if random.random() < 0.7 else random.choice(
        ["Bom", "Recomendo", "Não gostei", "Chegou atrasado", "Produto ok", "Excelente"])
    msg = "" if random.random() < 0.55 else random.choice([
        "Produto chegou dentro do prazo, tudo certo.",
        "Entrega atrasou bastante, mas o produto é bom.",
        "Nao recomendo, qualidade abaixo do esperado.",
        "Superou expectativas, voltarei a comprar.",
        "Embalagem veio danificada.",
        "",
    ])
    creation = pd.to_datetime(row["order_purchase_timestamp"]) + timedelta(days=random.randint(3, 25))
    review_rows.append((rid, oid, score, title, msg, str(creation)))

reviews = pd.DataFrame(review_rows, columns=[
    "review_id", "order_id", "review_score", "review_comment_title",
    "review_comment_message", "review_creation_date"
])
dup_reviews = reviews.sample(frac=0.003, random_state=6) if len(reviews) > 0 else reviews
reviews = pd.concat([reviews, dup_reviews], ignore_index=True)

# ---------------------------------------------------------------------------
# product_category_name_translation
# ---------------------------------------------------------------------------
translation_map = {
    "cama_mesa_banho": "bed_bath_table", "beleza_saude": "health_beauty",
    "esporte_lazer": "sports_leisure", "moveis_decoracao": "furniture_decor",
    "informatica_acessorios": "computers_accessories",
    "utilidades_domesticas": "housewares", "relogios_presentes": "watches_gifts",
    "telefonia": "telephony", "automotivo": "auto", "brinquedos": "toys",
    "cool_stuff": "cool_stuff", "ferramentas_jardim": "garden_tools",
    "perfumaria": "perfumery", "bebes": "baby", "eletronicos": "electronics",
    "papelaria": "stationery", "fashion_bolsas_acessorios": "fashion_bags_accessories",
    "pet_shop": "pet_shop", "moveis_escritorio": "office_furniture",
    "construcao_ferramentas": "construction_tools", "livros": "books",
    "market_place": "market_place",
}
translation = pd.DataFrame(
    list(translation_map.items()),
    columns=["product_category_name", "product_category_name_english"]
)

# ---------------------------------------------------------------------------
# geolocation (amostra simplificada)
# ---------------------------------------------------------------------------
geo_rows = []
for s, (city, _) in STATES.items():
    for _ in range(15):
        geo_rows.append((
            np.random.randint(1000, 99999), np.random.uniform(-33, 5),
            np.random.uniform(-73, -35), city, s
        ))
geolocation = pd.DataFrame(geo_rows, columns=[
    "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
    "geolocation_city", "geolocation_state"
])

# ---------------------------------------------------------------------------
# salvar tudo
# ---------------------------------------------------------------------------
customers.to_csv(OUT_DIR + "olist_customers_dataset.csv", index=False)
sellers.to_csv(OUT_DIR + "olist_sellers_dataset.csv", index=False)
products.to_csv(OUT_DIR + "olist_products_dataset.csv", index=False)
orders.to_csv(OUT_DIR + "olist_orders_dataset.csv", index=False)
items.to_csv(OUT_DIR + "olist_order_items_dataset.csv", index=False)
payments.to_csv(OUT_DIR + "olist_order_payments_dataset.csv", index=False)
reviews.to_csv(OUT_DIR + "olist_order_reviews_dataset.csv", index=False)
translation.to_csv(OUT_DIR + "product_category_name_translation.csv", index=False)
geolocation.to_csv(OUT_DIR + "olist_geolocation_dataset.csv", index=False)

print("Dataset sintético gerado em data/raw/:")
print(f"  customers: {len(customers)}")
print(f"  sellers:   {len(sellers)}")
print(f"  products:  {len(products)}")
print(f"  orders:    {len(orders)}")
print(f"  items:     {len(items)}")
print(f"  payments:  {len(payments)}")
print(f"  reviews:   {len(reviews)}")
