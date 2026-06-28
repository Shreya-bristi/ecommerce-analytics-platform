USE ecom_staging;

DROP TABLE IF EXISTS stg_orders;
CREATE TABLE stg_orders(
    order_id  VARCHAR(50),
    customer_id VARCHAR(50),
    order_status VARCHAR(20),
    order_purchase_timestamp VARCHAR(30),
    order_approved_at VARCHAR(30),
    order_delivered_carrier VARCHAR(30),
    order_delivered_customer VARCHAR(50),
    order_estimated_delivery VARCHAR(30)

);

DROP TABLE IF EXISTS stg_order_items;
CREATE TABLE stg_order_items(
    order_id  VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit VARCHAR(30),
    price DECIMAL(10,2),
    freight_value DECIMAL(10,2)

);

DROP TABLE IF EXISTS stg_customers;
CREATE TABLE stg_customers (
    customer_id               VARCHAR(50),
    customer_unique_id        VARCHAR(50),
    customer_zip_code_prefix  VARCHAR(10),
    customer_city             VARCHAR(100),
    customer_state            VARCHAR(5)
);

DROP TABLE IF EXISTS stg_products;
CREATE TABLE stg_products (
    product_id                VARCHAR(50),
    product_category_name     VARCHAR(100),
    product_name_length       INT,
    product_description_length INT,
    product_photos_qty        INT,
    product_weight_g          INT,
    product_length_cm         INT,
    product_height_cm         INT,
    product_width_cm          INT
);

DROP TABLE IF EXISTS stg_payments;
CREATE TABLE stg_payments (
    order_id             VARCHAR(50),
    payment_sequential   INT,
    payment_type         VARCHAR(30),
    payment_installments INT,
    payment_value        DECIMAL(10,2)
);

DROP TABLE IF EXISTS stg_category_translation;
CREATE TABLE stg_category_translation (
    product_category_name         VARCHAR(100),
    product_category_name_english VARCHAR(100)
);

