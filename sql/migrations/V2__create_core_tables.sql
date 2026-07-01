USE ecom_core;

-- ========================================
-- NORMALISATION: 3NF
-- No transitive dependencies
-- ========================================

CREATE TABLE categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    name_pt       VARCHAR(100) NOT NULL,
    name_en       VARCHAR(100),
    parent_id     INT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

CREATE TABLE products (
    product_id    INT AUTO_INCREMENT PRIMARY KEY,
    source_id     VARCHAR(50) UNIQUE NOT NULL,
    category_id   INT,
    weight_g      INT,
    length_cm     INT,
    height_cm     INT,
    width_cm      INT,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE customers (
    customer_id       INT AUTO_INCREMENT PRIMARY KEY,
    source_id         VARCHAR(50) NOT NULL,
    unique_id         VARCHAR(50) NOT NULL,
    zip_code_prefix   VARCHAR(10),
    city              VARCHAR(100),
    state             VARCHAR(5),
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_unique_id (unique_id)
);

CREATE TABLE campaigns (
    campaign_id   INT AUTO_INCREMENT PRIMARY KEY,
    channel       VARCHAR(30) NOT NULL,
    name          VARCHAR(100),
    budget        DECIMAL(12,2) DEFAULT 0,
    spend         DECIMAL(12,2) DEFAULT 0,
    start_dt      DATE,
    end_dt        DATE
);

CREATE TABLE orders (
    order_id          INT AUTO_INCREMENT PRIMARY KEY,
    source_id         VARCHAR(50) UNIQUE NOT NULL,
    customer_id       INT NOT NULL,
    campaign_id       INT NULL,
    status            ENUM('created','approved','invoiced','shipped',
                           'delivered','canceled','unavailable','processing')
                      NOT NULL DEFAULT 'created',
    ordered_at        DATETIME NOT NULL,
    approved_at       DATETIME,
    delivered_carrier DATETIME,
    delivered_customer DATETIME,
    estimated_delivery DATETIME,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    INDEX idx_ordered_at (ordered_at),
    INDEX idx_status (status)
);

CREATE TABLE order_items (
    item_id      INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT NOT NULL,
    product_id   INT NOT NULL,
    item_seq     INT NOT NULL DEFAULT 1,
    unit_price   DECIMAL(10,2) NOT NULL,
    freight      DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_order_id (order_id)
);

CREATE TABLE sessions (
    session_id    INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT NOT NULL,
    order_id      INT NULL,
    channel       VARCHAR(30),
    stage         ENUM('visit','product_view','add_to_cart','checkout','purchase')
                  NOT NULL DEFAULT 'visit',
    stage_order   TINYINT NOT NULL DEFAULT 1,
    session_ts    DATETIME NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_stage (stage)
);

CREATE TABLE ab_events (
    event_id       INT AUTO_INCREMENT PRIMARY KEY,
    session_id     INT NOT NULL,
    experiment_id  VARCHAR(50) NOT NULL,
    variant        ENUM('control','variant') NOT NULL,
    converted      TINYINT(1) NOT NULL DEFAULT 0,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    INDEX idx_experiment (experiment_id)
);