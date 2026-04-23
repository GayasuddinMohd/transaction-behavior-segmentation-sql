-- ============================================================
--  PROJECT  : Transaction Behavior & Segmentation Analysis
--  FILE     : 3_analysis_queries.sql
--  PURPOSE  : Core analysis queries — revenue, demand, segments
--  ENGINE   : MySQL
-- ============================================================

USE transaction_analysis;

-- ============================================================
-- QUERY 1 : Total Revenue Overview
-- "Analyzed 48K+ transactions to surface revenue drivers"
-- ============================================================
SELECT
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    COUNT(ti.item_id)                               AS total_line_items,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS total_revenue_inr,
    ROUND(AVG(t.total_amount), 2)                   AS avg_order_value,
    COUNT(DISTINCT t.user_id)                       AS unique_customers
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
WHERE t.status = 'completed';


-- ============================================================
-- QUERY 2 : Revenue by Category
-- "Identified top revenue-driving product categories"
-- ============================================================
SELECT
    p.category,
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    SUM(ti.quantity)                                AS units_sold,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS total_revenue,
    ROUND(AVG(ti.unit_price), 2)                    AS avg_unit_price,
    ROUND(
        SUM(ti.quantity * ti.unit_price) * 100.0 /
        SUM(SUM(ti.quantity * ti.unit_price)) OVER (), 2
    )                                               AS revenue_pct
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
JOIN products p            ON ti.product_id = p.product_id
WHERE t.status = 'completed'
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 3 : Revenue by Hour of Day  ← THE KEY INSIGHT
-- "Evening hours (6–10 PM) contribute ~40% of total revenue"
-- ============================================================
SELECT
    HOUR(t.txn_datetime)                            AS hour_of_day,
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS revenue,
    ROUND(
        SUM(ti.quantity * ti.unit_price) * 100.0 /
        SUM(SUM(ti.quantity * ti.unit_price)) OVER (), 2
    )                                               AS revenue_pct
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
WHERE t.status = 'completed'
GROUP BY HOUR(t.txn_datetime)
ORDER BY hour_of_day;


-- ============================================================
-- QUERY 4 : Evening vs Non-Evening Revenue Split
-- Direct proof of the 40% evening revenue bullet point
-- ============================================================
SELECT
    CASE
        WHEN HOUR(t.txn_datetime) BETWEEN 18 AND 22
        THEN 'Evening (6PM–10PM)'
        ELSE 'Other Hours'
    END                                             AS time_window,
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS total_revenue,
    ROUND(
        SUM(ti.quantity * ti.unit_price) * 100.0 /
        SUM(SUM(ti.quantity * ti.unit_price)) OVER (), 2
    )                                               AS revenue_pct
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
WHERE t.status = 'completed'
GROUP BY time_window
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 5 : Revenue by Day of Week
-- "Demand patterns across the week"
-- ============================================================
SELECT
    DAYNAME(t.txn_datetime)                         AS day_name,
    DAYOFWEEK(t.txn_datetime)                       AS day_num,
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS total_revenue,
    ROUND(AVG(t.total_amount), 2)                   AS avg_order_value
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
WHERE t.status = 'completed'
GROUP BY day_name, day_num
ORDER BY day_num;


-- ============================================================
-- QUERY 6 : Revenue by City
-- "Geographic demand distribution"
-- ============================================================
SELECT
    u.city,
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS total_revenue,
    ROUND(AVG(t.total_amount), 2)                   AS avg_order_value,
    COUNT(DISTINCT t.user_id)                       AS active_users
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
JOIN users u               ON t.user_id = u.user_id
WHERE t.status = 'completed'
GROUP BY u.city
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 7 : User Segmentation by Frequency & Order Value
-- "Segmented users into retention and upsell cohorts"
-- ============================================================
WITH user_stats AS (
    SELECT
        t.user_id,
        COUNT(DISTINCT t.txn_id)                    AS order_count,
        ROUND(SUM(ti.quantity * ti.unit_price), 2)  AS total_spent,
        ROUND(AVG(t.total_amount), 2)               AS avg_order_value
    FROM transactions t
    JOIN transaction_items ti ON t.txn_id = ti.txn_id
    WHERE t.status = 'completed'
    GROUP BY t.user_id
),
segmented AS (
    SELECT
        user_id,
        order_count,
        total_spent,
        avg_order_value,
        CASE
            WHEN order_count >= 20  THEN 'High Frequency'
            WHEN order_count >= 10  THEN 'Mid Frequency'
            ELSE                         'Low Frequency'
        END AS frequency_segment,
        CASE
            WHEN avg_order_value >= 15000 THEN 'High Value'
            WHEN avg_order_value >= 5000  THEN 'Mid Value'
            ELSE                               'Low Value'
        END AS value_segment
    FROM user_stats
)
SELECT
    frequency_segment,
    value_segment,
    COUNT(user_id)                                  AS user_count,
    ROUND(AVG(order_count), 1)                      AS avg_orders,
    ROUND(AVG(total_spent), 2)                      AS avg_lifetime_value,
    ROUND(SUM(total_spent), 2)                      AS segment_revenue
FROM segmented
GROUP BY frequency_segment, value_segment
ORDER BY segment_revenue DESC;


-- ============================================================
-- QUERY 8 : Top 10 High-Value Users (VIP Cohort)
-- "High-value repeat users for upsell strategy"
-- ============================================================
SELECT
    t.user_id,
    u.full_name,
    u.city,
    u.age,
    COUNT(DISTINCT t.txn_id)                        AS total_orders,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS lifetime_value,
    ROUND(AVG(t.total_amount), 2)                   AS avg_order_value,
    MIN(DATE(t.txn_datetime))                       AS first_order,
    MAX(DATE(t.txn_datetime))                       AS last_order
FROM transactions t
JOIN transaction_items ti ON t.txn_id = ti.txn_id
JOIN users u               ON t.user_id = u.user_id
WHERE t.status = 'completed'
GROUP BY t.user_id, u.full_name, u.city, u.age
ORDER BY lifetime_value DESC
LIMIT 10;


-- ============================================================
-- QUERY 9 : Churn Risk Users
-- Users who ordered but haven't ordered in last 90 days
-- ============================================================
WITH user_last_order AS (
    SELECT
        user_id,
        MAX(txn_datetime)                           AS last_order_date,
        COUNT(txn_id)                               AS total_orders
    FROM transactions
    WHERE status = 'completed'
    GROUP BY user_id
)
SELECT
    u.user_id,
    u.full_name,
    u.city,
    ulo.total_orders,
    DATE(ulo.last_order_date)                       AS last_order_date,
    DATEDIFF(NOW(), ulo.last_order_date)            AS days_since_last_order
FROM user_last_order ulo
JOIN users u ON ulo.user_id = u.user_id
WHERE DATEDIFF(NOW(), ulo.last_order_date) > 90
  AND ulo.total_orders >= 3
ORDER BY days_since_last_order DESC
LIMIT 20;


-- ============================================================
-- QUERY 10 : Top 10 Best-Selling Products
-- "Top products driving transaction volume"
-- ============================================================
SELECT
    p.product_name,
    p.category,
    SUM(ti.quantity)                                AS units_sold,
    COUNT(DISTINCT ti.txn_id)                       AS times_ordered,
    ROUND(SUM(ti.quantity * ti.unit_price), 2)      AS total_revenue,
    ROUND(AVG(ti.unit_price), 2)                    AS avg_selling_price
FROM transaction_items ti
JOIN products p      ON ti.product_id = p.product_id
JOIN transactions t  ON ti.txn_id = t.txn_id
WHERE t.status = 'completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;
