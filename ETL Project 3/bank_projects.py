from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime 

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ["Rank", "Bank_Name", "MC_USD_Billion"]
db_name = 'Banks.db'
exchange_rate = './exchange_rate.csv'
table_name = 'Largest_banks'
csv_path = './market_capitalization.csv'

def log_progress(message):
    timestamp_format = '%Y-%h-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("./code_log.txt", "a") as f:
        f.write(f'{timestamp} : {message} \n')

def extract(url, table_attribs):
    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            data_dict = {
                    "Rank": col[0].get_text(strip=True),
                    "Bank_Name": col[1].get_text(strip=True),
                    "MC_USD_Billion": col[2].get_text(strip=True)
            }
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
    return df

def transform(df, csv_path):
    # Change MC_USD_Billion Data Types
    df['MC_USD_Billion'] = (df['MC_USD_Billion'].str.strip().astype(float))

    exchange = pd.read_csv(csv_path)
    exchange_dict = exchange.set_index('Currency').to_dict()['Rate']
    df['MC_GBP_Billion'] = [np.round(x*exchange_dict['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x*exchange_dict['EUR'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x*exchange_dict['INR'],2) for x in df['MC_USD_Billion']]

    return df

def load_to_csv(df, output_path):
    df.to_csv(output_path)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

log_progress('Preliminaries complete. Initiating ETL process')
data = extract(url, table_attribs)

log_progress('Data extraction complete. Initiating Transformation process')
data_transform = transform(data, exchange_rate)

log_progress('Data transformation complete. Initiating loading process')
load_to_csv(data_transform, csv_path)
log_progress('Data saved to CSV file')


sql_connection = sqlite3.connect(db_name)
log_progress('SQL Connection initiated.')

load_to_db(data_transform, sql_connection, table_name)
log_progress('Data loaded to Database as table. Running the query')

query_statement = f'SELECT * FROM Largest_banks'
run_query(query_statement, sql_connection)

query_statement = f'SELECT AVG(MC_GBP_Billion) FROM Largest_banks'
run_query(query_statement, sql_connection)

query_statement = f'SELECT Rank, Bank_Name FROM Largest_banks LIMIT 5'
run_query(query_statement, sql_connection)

log_progress('Process Complete.')

sql_connection.close()