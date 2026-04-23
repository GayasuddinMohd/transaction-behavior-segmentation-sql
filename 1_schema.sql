-- ============================================================
--  PROJECT  : Transaction Behavior & Segmentation Analysis
--  FILE     : 1_schema.sql
--  PURPOSE  : Create the database and all required tables
--  ENGINE   : MySQL
-- ============================================================

-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS transaction_analysis;
USE transaction_analysis;

-- ============================================================
-- TABLE 1 : users
-- Stores customer profile information
-- 1 row per user (~1000 users total)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id       INT           PRIMARY KEY AUTO_INCREMENT,
    full_name     VARCHAR(100)  NOT NULL,
    city          VARCHAR(50)   NOT NULL,
    age           INT           NOT NULL,          -- range: 18–60
    gender        ENUM('M','F') NOT NULL,
    signup_date   DATE          NOT NULL           -- when they joined the platform
);

-- ============================================================
-- TABLE 2 : products
-- Stores product catalogue
-- 1 row per product (~50 products total)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    product_id    INT            PRIMARY KEY AUTO_INCREMENT,
    product_name  VARCHAR(150)   NOT NULL,
    category      VARCHAR(50)    NOT NULL,          -- Electronics, Fashion, Food, etc.
    base_price    DECIMAL(10,2)  NOT NULL           -- price in INR
);

-- ============================================================
-- TABLE 3 : transactions
-- Every order placed by a user
-- 1 row per order (~12,000 orders → expands to 48K+ line items)
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    txn_id        INT            PRIMARY KEY AUTO_INCREMENT,
    user_id       INT            NOT NULL,
    txn_datetime  DATETIME       NOT NULL,          -- full timestamp (date + time)
    total_amount  DECIMAL(10,2)  NOT NULL,          -- sum of all items in this order
    status        ENUM(
                    'completed',
                    'cancelled',
                    'refunded'
                  )              NOT NULL DEFAULT 'completed',

    -- Foreign key → links each transaction to a user
    CONSTRAINT fk_txn_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLE 4 : transaction_items
-- Line-item breakdown of each transaction
-- 1 row per product per order (avg 4 items per order = 48K rows)
-- ============================================================
CREATE TABLE IF NOT EXISTS transaction_items (
    item_id       INT            PRIMARY KEY AUTO_INCREMENT,
    txn_id        INT            NOT NULL,
    product_id    INT            NOT NULL,
    quantity      INT            NOT NULL DEFAULT 1,
    unit_price    DECIMAL(10,2)  NOT NULL,          -- price at time of purchase

    -- Foreign keys
    CONSTRAINT fk_item_txn
        FOREIGN KEY (txn_id)
        REFERENCES transactions(txn_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_item_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE
);

-- ============================================================
-- INDEXES : Speed up the queries we'll run in Phase 3
-- ============================================================

-- We'll GROUP BY hour a lot → index on txn_datetime
CREATE INDEX idx_txn_datetime  ON transactions(txn_datetime);

-- We'll JOIN on user_id frequently
CREATE INDEX idx_txn_user      ON transactions(user_id);

-- We'll JOIN transaction_items on txn_id
CREATE INDEX idx_items_txn     ON transaction_items(txn_id);

-- We'll GROUP BY category (via product_id JOIN)
CREATE INDEX idx_items_product ON transaction_items(product_id);

-- ============================================================
-- VERIFY : Check all 4 tables were created successfully
-- ============================================================
SHOW TABLES;


USE transaction_analysis;
SHOW TABLES;
DESC transactions;



USE transaction_analysis;

CREATE TABLE IF NOT EXISTS users (
    user_id       INT           PRIMARY KEY AUTO_INCREMENT,
    full_name     VARCHAR(100)  NOT NULL,
    city          VARCHAR(50)   NOT NULL,
    age           INT           NOT NULL,
    gender        ENUM('M','F') NOT NULL,
    signup_date   DATE          NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id    INT            PRIMARY KEY AUTO_INCREMENT,
    product_name  VARCHAR(150)   NOT NULL,
    category      VARCHAR(50)    NOT NULL,
    base_price    DECIMAL(10,2)  NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id        INT            PRIMARY KEY AUTO_INCREMENT,
    user_id       INT            NOT NULL,
    txn_datetime  DATETIME       NOT NULL,
    total_amount  DECIMAL(10,2)  NOT NULL,
    status        ENUM('completed','cancelled','refunded') NOT NULL DEFAULT 'completed',
    CONSTRAINT fk_txn_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transaction_items (
    item_id       INT            PRIMARY KEY AUTO_INCREMENT,
    txn_id        INT            NOT NULL,
    product_id    INT            NOT NULL,
    quantity      INT            NOT NULL DEFAULT 1,
    unit_price    DECIMAL(10,2)  NOT NULL,
    CONSTRAINT fk_item_txn FOREIGN KEY (txn_id) REFERENCES transactions(txn_id) ON DELETE CASCADE,
    CONSTRAINT fk_item_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX idx_txn_datetime  ON transactions(txn_datetime);
CREATE INDEX idx_txn_user      ON transactions(user_id);
CREATE INDEX idx_items_txn     ON transaction_items(txn_id);
CREATE INDEX idx_items_product ON transaction_items(product_id);

SHOW TABLES;


