-- ============================================================
-- Consultas SQL de negócio — Projeto Olist
-- Cada query responde a uma das perguntas de negócio do projeto.
-- ============================================================

USE olist_ecommerce;

-- 1) Receita mensal
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS mes,
    ROUND(SUM(oi.price), 2) AS receita
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY mes
ORDER BY mes;

-- 2) Top 10 categorias por receita
SELECT
    p.product_category_name AS categoria,
    ROUND(SUM(oi.price), 2) AS receita,
    COUNT(*) AS qtd_itens_vendidos
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY categoria
ORDER BY receita DESC
LIMIT 10;

-- 3) Tempo médio de entrega (em dias) por estado do cliente
SELECT
    c.customer_state AS estado,
    ROUND(AVG(DATEDIFF(o.order_delivered_customer_date, o.order_purchase_timestamp)), 1) AS dias_medio_entrega
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY estado
ORDER BY dias_medio_entrega DESC;

-- 4) Relação entre atraso na entrega e nota da avaliação
SELECT
    CASE
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Atrasado'
        ELSE 'No prazo'
    END AS status_entrega,
    ROUND(AVG(r.review_score), 2) AS nota_media,
    COUNT(*) AS qtd_pedidos
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY status_entrega;

-- 5) Métodos de pagamento mais usados
SELECT
    payment_type AS metodo,
    COUNT(*) AS qtd,
    ROUND(SUM(payment_value), 2) AS valor_total
FROM order_payments
GROUP BY metodo
ORDER BY qtd DESC;

-- 6) Pedidos e receita por estado (para mapa/ranking no BI)
SELECT
    c.customer_state AS estado,
    COUNT(DISTINCT o.order_id) AS qtd_pedidos,
    ROUND(SUM(oi.price), 2) AS receita
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY estado
ORDER BY receita DESC;

-- 7) KPIs gerais (para os cartões do topo do dashboard)
SELECT
    COUNT(DISTINCT o.order_id) AS total_pedidos,
    ROUND(SUM(oi.price), 2) AS receita_total,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS ticket_medio,
    ROUND(AVG(r.review_score), 2) AS nota_media_geral
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered';
