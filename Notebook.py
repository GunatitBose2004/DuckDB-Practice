# %% 
print("Hello, World!")
# %%
import duckdb, pandas, seaborn, matplotlib
print("DuckDB:", duckdb.__version__)
print("Pandas:", pandas.__version__)
print("Seaborn:", seaborn.__version__)
print("Matplotlib:", matplotlib.__version__)

# %%
import pandas as pd
import glob
import time
import duckdb

conn = duckdb.connect() # create an in-memory database
# %%
# with pandas
cur_time = time.time()
df = pd.concat([pd.read_csv(f) for f in glob.glob('Sales_Product_Combined.csv')])
print(f"time: {(time.time() - cur_time)}")
print(df.head(10))
# %%
# with duckdb
cur_time = time.time()
df = conn.execute("""
	SELECT *
	FROM 'Sales_Product_Combined.csv'
	LIMIT 10
""").df()
print(f"time: {(time.time() - cur_time)}")
print(df)
# %%
df = conn.execute("""
	SELECT *
	FROM 'Sales_Product_Combined.csv'
""").df()
conn.register("df_view", df)
conn.execute("DESCRIBE df_view").df() # doesn't work if you don't register df as a virtual table
# %%
conn.execute("SELECT COUNT(*) FROM df_view").df()
 
# %%
conn.execute("""SELECT * FROM df WHERE "Order ID"='295665'""").df()
# %%
conn.execute("""
CREATE OR REPLACE TABLE sales AS
SELECT
    "Order ID"::INTEGER AS order_id,
    Product AS product,
    "Quantity Ordered"::INTEGER AS quantity,
    Price::DECIMAL AS price_each,
    strptime("Order Date", '%m/%d/%Y %H:%M')::DATE AS order_date,
    "Purchase Address" AS purchase_address
FROM df
WHERE TRY_CAST("Order ID" AS INTEGER) NOTNULL
""")
# %%
conn.execute("""
CREATE OR REPLACE TABLE sales AS
SELECT
    "Order ID"::INTEGER AS order_id,
    Product AS product,
    "Quantity Ordered"::INTEGER AS quantity,
    Price::DECIMAL AS price_each,
    strptime("Order Date", '%m/%d/%Y %H:%M')::DATE AS order_date,
    "Purchase Address" AS purchase_address
FROM df
WHERE TRY_CAST("Order ID" AS INTEGER) NOTNULL
""")

# %%
print(df.dtypes)
# %%
conn.execute("""
CREATE OR REPLACE TABLE sales AS
SELECT
    "Order ID"::INTEGER AS order_id,
    Product AS product,
    "Quantity Ordered"::INTEGER AS quantity,
    REPLACE(Price, ',', '')::DECIMAL AS price_each,
    CAST("Order Date" AS DATE) AS order_date,
    "Purchase Address" AS purchase_address
FROM df
WHERE TRY_CAST("Order ID" AS INTEGER) NOTNULL
""")

# %%
conn.execute("FROM sales").df()
# %%
conn.execute("""
	SELECT 
		* EXCLUDE (product, order_date, purchase_address)
	FROM sales
	""").df()
# %%
conn.execute("""
	CREATE OR REPLACE VIEW aggregated_sales AS
	SELECT
		order_id,
		COUNT(1) as nb_orders,
		MONTH(order_date) as month,
		str_split(purchase_address, ',')[2] AS city,
		SUM(quantity * price_each) AS revenue
	FROM sales
	GROUP BY ALL
""")
# %%
conn.execute("From aggregated_sales").df()
# %%
conn.execute(""" 
SELECT 
    city,
    SUM(revenue) AS total
FROM aggregated_sales
GROUP BY city
ORDER BY total DESC
""").df()

# %%
conn.execute("COPY (FROM aggregated_sales) TO 'aggregated_sales.parquet' (FORMAT 'parquet')")
# %%
conn.execute("FROM aggregated_sales.parquet").df()
# %%
