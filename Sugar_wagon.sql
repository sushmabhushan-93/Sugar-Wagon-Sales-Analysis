USE DATABASE CANDY_DB;
SELECT * FROM FACTORIES;
SELECT * FROM PRODUCTS;
SELECT * FROM SALES;
SELECT * FROM TARGETS;


-- Checking for duplicate records
SELECT ORDER_ID, COUNT(*) FROM SALES
GROUP BY ORDER_ID
HAVING COUNT(*)>1;                 -- Many duplicate records
    
select count(distinct order_id ) from sales;
-- 1. Handling exact duplicates
-- Preveiw of exact duplicates

SELECT *
FROM sales
WHERE ROW_ID NOT IN(
    SELECT MIN(ROW_ID)
    FROM sales
    GROUP BY ORDER_ID, ORDER_DATE, SHIP_DATE, SHIP_MODE, CUSTOMER_ID,
             "Country/Region", CITY, "State/Province", POSTAL_CODE,
             DIVISION, REGION, PRODUCT_ID, PRODUCT_NAME,
             SALES, UNITS, GROSS_PROFIT, COST);

-- Deleting exact duplicates
delete from sales
where row_id not in (
    select min(row_id) from sales
    group by ORDER_ID, ORDER_DATE, SHIP_DATE, SHIP_MODE, CUSTOMER_ID,
             "Country/Region", CITY, "State/Province", POSTAL_CODE,
             DIVISION, REGION, PRODUCT_ID, PRODUCT_NAME,
             SALES, UNITS, GROSS_PROFIT, COST);

-- Handling duplicates with same product id but different Unit, sales and profit
select 
    min(row_id) as row_id,
    min(order_id) as order_id,
    min(order_date) as order_date,
    min(ship_date) as ship_date,
    min(ship_mode) as ship_mode,
    min(customer_id) as customer_id,
    min("Country/Region") as "Country/Region",
    min(city) as city,
    min("State/Province") as "State/Province",
    min(postal_code) as postal_code,
    min(division) as division,
    min(region) as region,
    product_id,
    min(product_name) as product_name,
    sum(sales) as sales,
    sum(units) as units,
    sum(gross_profit) as gross_profit,
    sum(cost) as cost
from sales
group by order_id, product_id;

-- Applying permenently
create or replace table sales_clean as 
select 
    min(row_id) as row_id,
    min(order_id) as order_id,
    min(order_date) as order_date,
    min(ship_date) as ship_date,
    min(ship_mode) as ship_mode,
    min(customer_id) as customer_id,
    min("Country/Region") as "Country/Region",
    min(city) as city,
    min("State/Province") as "State/Province",
    min(postal_code) as postal_code,
    min(division) as division,
    min(region) as region,
    product_id,
    min(product_name) as product_name,
    sum(sales) as sales,
    sum(units) as units,
    sum(gross_profit) as gross_profit,
    sum(cost) as cost
from sales
group by order_id, product_id;

-- Renaming the tables
alter table sales rename to sales_backup;
alter table sales_clean rename to sales;

select count(distinct order_id) from sales;


-- Missing value in Sales table
select 
    count(*) - count(order_id) as null_order_id,
    count(*) - count(order_date) as null_date,
    count(*) - count(ship_date) as null_shipdate,
    count(*) - count(customer_id) as null_customer, 
    count(*) - count("Country/Region") as null_country,
    count(*) - count(city) as null_city,
    count(*) - count("State/Province") as null_state,
    count(*) - count(postal_code) as null_postal,
    count(*) - count(division) as null_division,
    count(*) - count(region) as null_region,
    count(*) - count(product_id) as null_productid,
    count(*) - count(product_name) as null_productname,
    count(*) - count(sales) as null_sales,
    count(*) - count(units) as null_units,
    count(*) - count(gross_profit) as null_profit,
    count(*) - count(cost)as null_cost from sales;             -- No Missing values 

-- Referal integrity
-- Every Product ID in Sales exists in Products?

select distinct s.product_id, count(*) as occurance_in_sales from sales s 
left join products p on s.product_id = p.product_id
where p.product_id is null
group by s.product_id
order by occurance_in_sales desc; 

-- Every Factory in Products exists in Factories?
select p.factory, count(*) from products p left join factories f on p.factory = f.factory
where f.factory is null
group by p.factory
order by count(*) desc;


 -- Checking for inconsistent values

select * from sales
where sales < 0;

-- Date range check
select min(order_date), max(order_date) from sales;             -- Data from Jan 2021 to December 2024
select min(ship_date), max(ship_date) from sales;               -- June 2026 to June 2030 - Suspicious

select row_id, order_id, order_date, ship_date, 
    datediff('year', order_date, ship_date) as days_to_ship
from sales
where datediff('year', order_date, ship_date) > 1
order by days_to_ship desc;                                    -- Every product has been shipped after 5-6 years

-- Checking data types of every column
-- in sales

select column_name, data_type from information_schema.columns
where table_name = 'SALES';

select column_name, data_type from information_schema.columns
where table_name = 'PRODUCTS';

select column_name, data_type from information_schema.columns
where table_name = 'FACTORIES';

select column_name, data_type from information_schema.columns
where table_name = 'TARGETS';

-- Business Rule Validation — Do the numbers make sense?
-- Sales = Cost + Gross Profit → does this hold for every row?
select sales, gross_profit + cost as total_sales from sales
where sales != gross_profit + cost
order by total_sales desc;

-- Units should always be > 0
select order_id, units  from sales
where units <= 0;

--Sales and Cost should never be negative
select sales, cost from sales
where sales<0 or cost<0;

-- Consistency — Same values written differently?
-- ship mode
select distinct ship_mode from sales;

-- Region, city, division
select distinct region, count(*) from sales
group by region;

select distinct city, count(*) from sales
group by city;

select distinct division, count(*) from sales
group by division;

-- product name - Same Product, Slightly Different Names
select distinct product_id, product_name, count(*) from sales
group by product_id, product_name
order by product_name;

-- CHECK: All distinct Country/Region values
SELECT DISTINCT
    "Country/Region",
    COUNT(*) AS occurrence
FROM sales
GROUP BY "Country/Region"
ORDER BY "Country/Region";

-- Outlier detection
-- CHECK: Basic statistics for all numeric columns
SELECT
    ROUND(MIN(SALES), 2)         AS min_sales,
    ROUND(MAX(SALES), 2)         AS max_sales,
    ROUND(AVG(SALES), 2)         AS avg_sales,
    ROUND(MEDIAN(SALES), 2)      AS median_sales,
    ROUND(STDDEV(SALES), 2)      AS stddev_sales,

    ROUND(MIN(UNITS), 2)         AS min_units,
    ROUND(MAX(UNITS), 2)         AS max_units,
    ROUND(AVG(UNITS), 2)         AS avg_units,
    ROUND(MEDIAN(UNITS), 2)      AS median_units,
    ROUND(STDDEV(UNITS), 2)      AS stddev_units,

    ROUND(MIN(GROSS_PROFIT), 2)  AS min_gross_profit,
    ROUND(MAX(GROSS_PROFIT), 2)  AS max_gross_profit,
    ROUND(AVG(GROSS_PROFIT), 2)  AS avg_gross_profit,
    ROUND(MEDIAN(GROSS_PROFIT), 2) AS median_gross_profit,
    ROUND(STDDEV(GROSS_PROFIT), 2) AS stddev_gross_profit,

    ROUND(MIN(COST), 2)          AS min_cost,
    ROUND(MAX(COST), 2)          AS max_cost,
    ROUND(AVG(COST), 2)          AS avg_cost,
    ROUND(MEDIAN(COST), 2)       AS median_cost,
    ROUND(STDDEV(COST), 2)       AS stddev_cost
FROM sales;




