USE ecom_analytics;

-- ========================================
-- STAR SCHEMA: Optimised for Power BI
-- Denormalised dimensions, surrogate keys
-- ========================================

-- === DIMENSIONS ===

CREATE TABLE dim_date (
    date_key     INT PRIMARY KEY,          -- YYYYMMDD format
    full_date    DATE NOT NULL,
    day_of_week  TINYINT,
    day_name     VARCHAR(10),
    month_num    TINYINT,
    month_name   VARCHAR(10),
    quarter      TINYINT,
    year         SMALLINT,
    is_weekend   TINYINT(1),
    INDEX idx_full_date (full_date)
);

CREATE TABLE dim_customer (
    customer_key    INT AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT NOT NULL,              
    unique_id       VARCHAR(50),
    city            VARCHAR(100),
    state           VARCHAR(5),
    first_order_dt  DATE,
    total_orders    INT DEFAULT 0,
    total_spend     DECIMAL(12,2) DEFAULT 0,
    customer_tier   ENUM('new','returning','vip') DEFAULT 'new'
);

CREATE TABLE dim_product (
    product_key     INT AUTO_INCREMENT PRIMARY KEY,
    product_id      INT NOT NULL,
    source_id       VARCHAR(50),
    category_en     VARCHAR(100),
    category_pt     VARCHAR(100),
    weight_g        INT,
    avg_price       DECIMAL(10,2)
);

CREATE TABLE dim_channel (
    channel_key     INT AUTO_INCREMENT PRIMARY KEY,
    channel_name    VARCHAR(50) NOT NULL
);

CREATE TABLE dim_campaign (
    campaign_key    INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id     INT,
    channel         VARCHAR(30),
    name            VARCHAR(100),
    budget          DECIMAL(12,2),
    spend           DECIMAL(12,2)
);

-- === FACTS ===

CREATE TABLE fact_orders (
    order_key       INT AUTO_INCREMENT PRIMARY KEY,
    order_id        INT NOT NULL,
    date_key        INT NOT NULL,
    customer_key    INT NOT NULL,
    campaign_key    INT,
    status          VARCHAR(20),
    item_count      INT,
    revenue         DECIMAL(12,2),
    freight_total   DECIMAL(10,2),
    payment_value   DECIMAL(12,2),
    delivery_days   INT,
    FOREIGN KEY (date_key)     REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    INDEX idx_date (date_key)
);

CREATE TABLE fact_sessions (
    session_key     INT AUTO_INCREMENT PRIMARY KEY,
    session_id      INT NOT NULL,
    date_key        INT NOT NULL,
    customer_key    INT NOT NULL,
    channel_key     INT,
    stage           VARCHAR(20),
    stage_order     TINYINT,
    converted       TINYINT(1) DEFAULT 0,
    FOREIGN KEY (date_key)     REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key)
);

CREATE TABLE fact_ab_events (
    ab_key          INT AUTO_INCREMENT PRIMARY KEY,
    session_key     INT,
    experiment_id   VARCHAR(50),
    variant         VARCHAR(10),
    converted       TINYINT(1),
    event_date_key  INT,
    FOREIGN KEY (event_date_key) REFERENCES dim_date(date_key)
);