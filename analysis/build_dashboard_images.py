"""
Gera as imagens do dashboard de BI a partir dos resultados reais das
queries SQL (rodadas contra o MySQL depois do ETL).

Isso simula visualmente o que um dashboard Power BI mostraria — os
números vêm do banco de dados de verdade, criado e populado pelo
pipeline deste projeto (schema.sql + etl.py + queries.sql).
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------
# Paleta / estilo (consistente com identidade "BI corporativo")
# ---------------------------------------------------------------------
NAVY = "#0B2545"
BLUE = "#1D5BBF"
TEAL = "#12A594"
ORANGE = "#F2994A"
RED = "#E5484D"
GREY = "#6B7280"
LIGHT_BG = "#F7F8FA"
CARD_BG = "#FFFFFF"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#E5E7EB",
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "axes.titleweight": "bold",
    "figure.facecolor": LIGHT_BG,
    "axes.facecolor": CARD_BG,
})

OUT = "../images/"

# ---------------------------------------------------------------------
# Carregar os resultados reais das queries
# ---------------------------------------------------------------------
receita_mensal = pd.read_csv("q1_receita_mensal.tsv", sep="\t")
top_categorias = pd.read_csv("q2_top_categorias.tsv", sep="\t")
tempo_entrega = pd.read_csv("q3_tempo_entrega_estado.tsv", sep="\t")
atraso_nota = pd.read_csv("q4_atraso_vs_nota.tsv", sep="\t")
metodos_pag = pd.read_csv("q5_metodos_pagamento.tsv", sep="\t")
receita_estado = pd.read_csv("q6_pedidos_por_estado.tsv", sep="\t")
kpis = pd.read_csv("q7_kpis.tsv", sep="\t").iloc[0]

CAT_LABELS = {
    "beleza_saude": "Beleza & Saúde", "informatica_acessorios": "Informática",
    "eletronicos": "Eletrônicos", "relogios_presentes": "Relógios/Presentes",
    "cama_mesa_banho": "Cama, Mesa e Banho", "esporte_lazer": "Esporte e Lazer",
    "moveis_decoracao": "Móveis e Decoração", "utilidades_domesticas": "Utilidades Dom.",
    "telefonia": "Telefonia", "automotivo": "Automotivo", "brinquedos": "Brinquedos",
    "cool_stuff": "Cool Stuff", "ferramentas_jardim": "Ferramentas/Jardim",
    "perfumaria": "Perfumaria", "bebes": "Bebês", "papelaria": "Papelaria",
    "fashion_bolsas_acessorios": "Fashion", "pet_shop": "Pet Shop",
    "moveis_escritorio": "Móveis Escritório", "construcao_ferramentas": "Construção",
    "livros": "Livros", "market_place": "Marketplace", "nao_informado": "Não informado",
}
PAY_LABELS = {"credit_card": "Cartão de Crédito", "boleto": "Boleto",
              "voucher": "Voucher", "debit_card": "Cartão de Débito"}

# =======================================================================
# 1) Receita mensal — linha
# =======================================================================
fig, ax = plt.subplots(figsize=(11, 4.5), dpi=150)
x = receita_mensal["mes"]
y = receita_mensal["receita"]
ax.plot(x, y, color=BLUE, linewidth=2.5, marker="o", markersize=4, markerfacecolor=BLUE)
ax.fill_between(range(len(x)), y, color=BLUE, alpha=0.08)
ax.set_title("Receita Mensal", fontsize=15, loc="left", pad=14)
ax.set_ylabel("Receita (R$)")
ax.set_xticks(range(0, len(x), 2))
ax.set_xticklabels(x[::2], rotation=45, ha="right", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EDEFF2", linewidth=0.8)
ax.yaxis.set_major_formatter(lambda v, p: f"R$ {v/1000:.0f}k")
fig.tight_layout()
fig.savefig(OUT + "01_receita_mensal.png", facecolor=LIGHT_BG)
plt.close(fig)

# =======================================================================
# 2) Top 10 categorias — barras horizontais
# =======================================================================
fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
cats = top_categorias.sort_values("receita")
labels = [CAT_LABELS.get(c, c) for c in cats["categoria"]]
colors = [TEAL if i == len(cats) - 1 else BLUE for i in range(len(cats))]
bars = ax.barh(labels, cats["receita"], color=colors, height=0.62)
ax.set_title("Top 10 Categorias por Receita", fontsize=15, loc="left", pad=14)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(left=False)
ax.set_xticks([])
for bar, val in zip(bars, cats["receita"]):
    ax.text(bar.get_width() + max(cats["receita"]) * 0.01, bar.get_y() + bar.get_height()/2,
            f"R$ {val:,.0f}".replace(",", "."), va="center", fontsize=9, color=NAVY)
fig.tight_layout()
fig.savefig(OUT + "02_top_categorias.png", facecolor=LIGHT_BG)
plt.close(fig)

# =======================================================================
# 3) Tempo médio de entrega por estado — barras (top 12 mais lentos)
# =======================================================================
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
te = tempo_entrega.sort_values("dias", ascending=False).head(12)
colors = [RED if d > 15 else (ORANGE if d > 10 else TEAL) for d in te["dias"]]
bars = ax.bar(te["estado"], te["dias"], color=colors, width=0.62)
ax.set_title("Tempo Médio de Entrega por Estado (dias) — 12 mais lentos", fontsize=14, loc="left", pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EDEFF2", linewidth=0.8)
for bar, val in zip(bars, te["dias"]):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.3, f"{val:.0f}", ha="center", fontsize=9, color=NAVY)
fig.tight_layout()
fig.savefig(OUT + "03_tempo_entrega_estado.png", facecolor=LIGHT_BG)
plt.close(fig)

# =======================================================================
# 4) Atraso vs nota média — barras comparativas (o insight principal)
# =======================================================================
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
order = ["No prazo", "Atrasado"]
vals = [atraso_nota.set_index("status_entrega").loc[s, "nota_media"] for s in order]
colors = [TEAL, RED]
bars = ax.bar(order, vals, color=colors, width=0.5)
ax.set_ylim(0, 5.5)
ax.set_title("Nota Média x Status de Entrega", fontsize=15, loc="left", pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EDEFF2", linewidth=0.8)
for bar, val in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.15, f"{val:.2f} ★", ha="center", fontsize=13,
             fontweight="bold", color=NAVY)
fig.tight_layout()
fig.savefig(OUT + "04_atraso_vs_nota.png", facecolor=LIGHT_BG)
plt.close(fig)

# =======================================================================
# 5) Métodos de pagamento — pizza/donut
# =======================================================================
fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=150)
labels = [PAY_LABELS.get(m, m) for m in metodos_pag["metodo"]]
colors_pie = [BLUE, TEAL, ORANGE, GREY]
wedges, texts, autotexts = ax.pie(
    metodos_pag["qtd"], labels=labels, autopct="%1.0f%%", startangle=90,
    colors=colors_pie[:len(metodos_pag)], pctdistance=0.78,
    wedgeprops=dict(width=0.42, edgecolor=LIGHT_BG, linewidth=2),
    textprops=dict(color=NAVY, fontsize=10),
)
for t in autotexts:
    t.set_color("white"); t.set_fontweight("bold"); t.set_fontsize(9)
ax.set_title("Métodos de Pagamento", fontsize=15, loc="left", pad=14)
fig.tight_layout()
fig.savefig(OUT + "05_metodos_pagamento.png", facecolor=LIGHT_BG)
plt.close(fig)

# =======================================================================
# 6) Receita por estado — barras horizontais (top 10)
# =======================================================================
fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
re_ = receita_estado.sort_values("receita", ascending=False).head(10).sort_values("receita")
bars = ax.barh(re_["estado"], re_["receita"], color=BLUE, height=0.6)
bars[-1].set_color(TEAL)
ax.set_title("Receita por Estado (Top 10)", fontsize=15, loc="left", pad=14)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_xticks([])
for bar, val in zip(bars, re_["receita"]):
    ax.text(bar.get_width() + max(re_["receita"]) * 0.01, bar.get_y() + bar.get_height()/2,
            f"R$ {val:,.0f}".replace(",", "."), va="center", fontsize=9, color=NAVY)
fig.tight_layout()
fig.savefig(OUT + "06_receita_por_estado.png", facecolor=LIGHT_BG)
plt.close(fig)

# =======================================================================
# 7) DASHBOARD COMPLETO — imagem única estilo Power BI (hero image do README)
# =======================================================================
fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=LIGHT_BG)
gs = fig.add_gridspec(3, 4, hspace=0.55, wspace=0.35,
                       left=0.04, right=0.97, top=0.90, bottom=0.05)

# título do dashboard
fig.text(0.04, 0.965, "Olist E-commerce — Dashboard de Vendas", fontsize=20,
          fontweight="bold", color=NAVY)
fig.text(0.04, 0.935, "Python (ETL) → MySQL → Análise SQL  |  dados: ago/2016 – ago/2018",
          fontsize=10.5, color=GREY)

# --- KPI cards (linha 1) ---
kpi_data = [
    ("Receita Total", f"R$ {kpis['receita_total']/1e6:.2f}M", BLUE),
    ("Pedidos Entregues", f"{int(kpis['total_pedidos']):,}".replace(",", "."), TEAL),
    ("Ticket Médio", f"R$ {kpis['ticket_medio']:.2f}", ORANGE),
    ("Nota Média", f"{kpis['nota_media']:.2f} ★", NAVY),
]
for i, (label, value, color) in enumerate(kpi_data):
    ax = fig.add_subplot(gs[0, i])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    card = FancyBboxPatch((0.02, 0.08), 0.96, 0.86, boxstyle="round,pad=0,rounding_size=0.06",
                           linewidth=0, facecolor="white")
    ax.add_patch(card)
    ax.add_patch(FancyBboxPatch((0.02, 0.08), 0.05, 0.86, boxstyle="round,pad=0,rounding_size=0.02",
                                 linewidth=0, facecolor=color))
    ax.text(0.14, 0.60, value, fontsize=19, fontweight="bold", color=NAVY, va="center")
    ax.text(0.14, 0.28, label, fontsize=10.5, color=GREY, va="center")

# --- Receita mensal (linha 2, ocupa 2 colunas) ---
ax = fig.add_subplot(gs[1, 0:2])
x = receita_mensal["mes"]; y = receita_mensal["receita"]
ax.plot(x, y, color=BLUE, linewidth=2, marker="o", markersize=3)
ax.fill_between(range(len(x)), y, color=BLUE, alpha=0.08)
ax.set_title("Receita Mensal", fontsize=11.5, loc="left", fontweight="bold")
ax.set_xticks(range(0, len(x), 4)); ax.set_xticklabels(x[::4], rotation=0, fontsize=7)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EDEFF2", linewidth=0.7)
ax.yaxis.set_major_formatter(lambda v, p: f"{v/1000:.0f}k")
ax.tick_params(labelsize=7.5)

# --- Top categorias (linha 2, 2 colunas) ---
ax = fig.add_subplot(gs[1, 2:4])
cats = top_categorias.sort_values("receita").tail(6)
labels = [CAT_LABELS.get(c, c) for c in cats["categoria"]]
bars = ax.barh(labels, cats["receita"], color=BLUE, height=0.6)
bars[-1].set_color(TEAL)
ax.set_title("Top Categorias por Receita", fontsize=11.5, loc="left", fontweight="bold")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_xticks([]); ax.tick_params(labelsize=8)

# --- Atraso x nota (linha 3, 1 coluna) ---
ax = fig.add_subplot(gs[2, 0])
order = ["No prazo", "Atrasado"]
vals = [atraso_nota.set_index("status_entrega").loc[s, "nota_media"] for s in order]
bars = ax.bar(order, vals, color=[TEAL, RED], width=0.55)
ax.set_ylim(0, 5.5)
ax.set_title("Nota x Entrega", fontsize=11.5, loc="left", fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#EDEFF2", linewidth=0.7)
ax.tick_params(labelsize=8)
for bar, val in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.15, f"{val:.1f}", ha="center", fontsize=9, fontweight="bold")

# --- Métodos de pagamento (linha 3, 1 coluna) ---
ax = fig.add_subplot(gs[2, 1])
labels = [PAY_LABELS.get(m, m) for m in metodos_pag["metodo"]]
wedges, texts, autotexts = ax.pie(
    metodos_pag["qtd"], autopct="%1.0f%%", startangle=90,
    colors=[BLUE, TEAL, ORANGE, GREY][:len(metodos_pag)], pctdistance=0.75,
    wedgeprops=dict(width=0.42, edgecolor=LIGHT_BG, linewidth=1.5),
    textprops=dict(fontsize=7.5, color="white", fontweight="bold"),
)
ax.set_title("Pagamento", fontsize=11.5, loc="left", fontweight="bold")
ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.35), fontsize=6.5, ncol=2, frameon=False)

# --- Receita por estado (linha 3, 2 colunas) ---
ax = fig.add_subplot(gs[2, 2:4])
re_ = receita_estado.sort_values("receita", ascending=False).head(8).sort_values("receita")
bars = ax.barh(re_["estado"], re_["receita"], color=BLUE, height=0.6)
bars[-1].set_color(TEAL)
ax.set_title("Receita por Estado (Top 8)", fontsize=11.5, loc="left", fontweight="bold")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_xticks([]); ax.tick_params(labelsize=8)

fig.savefig(OUT + "00_dashboard_overview.png", facecolor=LIGHT_BG, bbox_inches="tight")
plt.close(fig)

print("Imagens do dashboard geradas em images/")
