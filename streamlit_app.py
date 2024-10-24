#pip install pysqlite3-binary
import streamlit as st
import pandas as pd
import requests
import sqlite3
import re
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore


api_key = '7952e35b067b484f924800606f19fd65'# Your API key from https://vanna.ai/account/profile

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


vn = MyVanna(config={'api_key': 'sk-rGRJ1CXmbhhlBxC4eJOvVRjlRNVREMs2nucvq9k2f5T3BlbkFJdGTc4iMNd13EIdCG3XfestscKdIfZZxSenlA5zlacA', 'model': 'gpt-4o'})


@st.cache_data
def load_data(file_path1,file_path2):
    df1= pd.read_excel(file_path1)
    df3= pd.read_excel(file_path2)
    return df1, df3
# Load dataframes
df1 , df3= load_data("/content/client_campaigns.xlsx","/content/client_sku_reports.xlsx")
df1=df1[[
    "client_name",
    "channel_name",
    "campaign_name",
    "program_type",
    "impression",
    "click",
    "spend",
    "sale",
    "conversion_rate",
    "orders",
    "report_date",
    "category",
    "subcategory"
]]

df3=df3[[
    "client_name",
    "channel_name",
    "sku_title",
    "brand",
    "report_date",
    "asin_id",
    "bsr",
    "category",
    "subcategory",
    "bb_winner",
    "price",
    "rating",
    "rating_count",
    "sale",
    "spend",
    "orders",
    "click",
    "impression",
    "is_available",
    "total_clicked_ad_units",
    "total_view_ad_units",
    "total_clicked_ad_sales",
    "total_view_ad_sales"
]]
# Create an in-memory SQLite database
conn = sqlite3.connect(':memory:', check_same_thread=False)
df1.to_sql('client_campaigns', conn, index=False, if_exists='replace')
df3.to_sql('client_sku_reports', conn, index=False, if_exists='replace')
# vn.remove_training_data(id='be6f709a-48b6-5368-b264-b81f694f1cd3-ddl')

vn.train(ddl="""
  CREATE TABLE client_campaigns (
  client_name VARCHAR(255), -- Name of the client
  channel_name VARCHAR(255), -- ecommerce channel(amazon, flipkart) where the campaign is executed.
  campaign_name VARCHAR(255), -- Name of the campaign
  program_type VARCHAR(50), -- Type of advertising program
  impression INTEGER, -- Number of impressions
  click INTEGER, -- Number of clicks
  spend DECIMAL(10,2), -- spend on the campaign for report date
  sale DECIMAL(10,2), -- sales generated
  conversion_rate DECIMAL(5,2), -- Orders divided by the number of clicks
  orders INTEGER, -- Number of orders placed
  report_date DATE, -- Campaigns data reporting date in yyyy-mm-dd
  category VARCHAR(100), -- Category of the product being campainged
  subcategory VARCHAR(100), -- Subcategory of the product being campainged
)
""")

vn.train(ddl="""
  TABLE client_sku_reports (
  client_name VARCHAR(255), -- Name of the client
  channel_name VARCHAR(255), -- ecommerce channel(amazon, flipkart) where the campaign is executed.
  sku_title VARCHAR(255), -- Title of the SKU/ASIN
  brand VARCHAR(100), -- Brand of the SKU/ASIN
  report_date DATE, -- Reporting date of the SKU/ASIN data in yyyy-mm-dd
  asin_id VARCHAR(100), -- SKU/ASIN of the product
  bsr INTEGER, -- Best Seller Rank of SKU
  category VARCHAR(100), -- Category of the SKU
  subcategory VARCHAR(100), -- Sub-category of the SKU
  bb_winner BOOLEAN, -- Name of the best buy winner  
  price DECIMAL(10,2), -- Price of the SKU
  rating DECIMAL(3,2), -- Average rating of the SKU
  rating_count INTEGER, -- Count of ratings
  sale DECIMAL(10,2), -- Total sales amount
  spend DECIMAL(10,2), -- Total spend on advertising
  orders INTEGER, -- Number of orders placed
  click INTEGER, -- Number of clicks
  impression INTEGER, -- Number of impressions 
  is_available BOOLEAN, -- Availability status of the SKU
  total_clicked_ad_units INTEGER, -- Total clicked ad units on flipkart
  total_view_ad_units INTEGER, -- Total viewed ad units on fipkart
  total_clicked_ad_sales DECIMAL(10,2), -- Total sales from clicked ads on flipkart
  total_view_ad_sales DECIMAL(10,2) -- Total sales from viewed ads on flipkart
)
""")

vn.train(documentation="The Click Through Rate i.e. CTR is defined as clicks per impression")
vn.train(documentation="ROAS stands for “return on ad spend” and is a marketing metric that estimates the amount of revenue earned per spend allocated to advertising.")
vn.train(documentation="to calculate CTR over time, such as daily, weekly, or monthly, you'll collect impressions and clicks for each time period and calculate the CTR separately for each interva.")
#vn.train(documentation="the data is SQLite, Query has to be write according to SQLite.")
vn.train(documentation="if question is not related to the data, responsd 'I am not able to answer this question as data is not available.'")
vn.train(
    question="sales in sept 2025", 
    sql="SELECT SUM(sale) AS total_sales FROM client_campaigns WHERE strftime('%Y-%m', report_date) = '2025-09'"
)


training_data = vn.get_training_data()
  


def run_sql(sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, conn)
    return df


def main():
    st.dataframe(training_data)
    st.title("Philips Campaigns")

    submit_question()


def submit_question():







  default_question = "Compare Category wise RoAS for amazon monthly"

  # Create a text input with the default question
  question = st.text_input("Enter Question:", value=default_question)

  if st.button("Submit"):
      if not question:
          st.warning("Please enter a question.")
          return

      output = f"You asked: {question}"
      st.write(output)

      
      vn.run_sql = run_sql
      vn.run_sql_is_set = True
      z=vn.ask(question=question, auto_train=False)
      # sql = vn.generate_sql(question)
      # st.write(sql)

      if z is None:
          st.write("I am not able to answer this question as data is not available.")
      else:
          st.write(z[0]) 
          st.dataframe(z[1]) 
          st.write(z[2])
      

if __name__ == "__main__":
    main()

