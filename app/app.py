
# from dotenv import load_dotenv
# load_dotenv('./.env')


#%% Imports

from ddb.bigquery import BigQuery
import ddb
from demail.gmail import SendEmail
import pandas as pd
import os
import datetime as dt
import matplotlib.pyplot as plt
from pretty_html_table import build_table
import pandas_datareader.data as web


#%% SQL Credentials

sql_credential = os.getenv('sql_credential')
con = BigQuery(sql_credential)
sql_table = os.getenv('sql_table')


#%% Get Treasury Rates

yrmnth = (dt.date.today() + dt.timedelta(days=-1)).strftime('%Y%m')
df = pd.read_csv(f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all/{yrmnth}?type=daily_treasury_yield_curve&field_tdr_date_value_month={yrmnth}&page&_format=csv')

df['Date'] = pd.to_datetime(df['Date'])
df = df.melt(id_vars='Date', var_name='duration', value_name='yield')
df['yield'] = df['yield'] / 100
df = ddb.clean(df, rowloadtime=True, drop_cols=False)
df = df.sort_values('Date')


#%% Load Treasury Rates

df = con.where_not_exists(df, sql_table, ['Date', 'duration'])
con.to_sql(df, sql_table, if_exists='append', index=False)


#%% Get Recent Data for Email

df_send = con.read(f'select * from {sql_table} where `Date` >= DATE_ADD(CURRENT_DATE(), INTERVAL -30 DAY)')
df_send['Date'] = df_send['Date'].dt.date
df_send = df_send.sort_values('Date')
df_send['yield'] = df_send['yield'] * 100

clm_list = ['1 Mo', '2 Mo', '3 Mo', '4 Mo', '6 Mo', '1 Yr', '2 Yr', '3 Yr', '5 Yr', '7 Yr', '10 Yr', '20 Yr', '30 Yr']
df_piv = df_send.pivot(index='Date', columns='duration', values='yield')[clm_list].sort_values('Date')
df_piv.columns.name = None


#%% Current Treasury Curve Chart

img_rate_shape = './rate_shape.png'
df_recent1 = df_piv.iloc[-1:].reset_index()
df_recent2 = df_piv.iloc[-2:-1].reset_index()
df_recent3 = df_piv.iloc[-7:-6].reset_index()

shape = df_piv.shape[1]
y_1 = df_recent1.drop('Date', axis=1).to_numpy().reshape(shape)
label_1 = df_recent1.at[0, 'Date']
y_2 = df_recent2.drop('Date', axis=1).to_numpy().reshape(shape)
label_2 = df_recent2.at[0, 'Date']
y_3 = df_recent3.drop('Date', axis=1).to_numpy().reshape(shape)
label_3 = df_recent3.at[0, 'Date']

fig, ax = plt.subplots()
ax.plot(clm_list, y_1, label=label_1, color='r')
ax.plot(clm_list, y_2, label=label_2, color='b', alpha=0.5)
ax.plot(clm_list, y_3, label=label_3, color='gray', alpha=0.25)
ax.set_title('Treasury Yield Curve Shape', loc='center')
ax.set_ylabel('Yield')
ax.set_xlabel('Duration')
ax.legend()
fig.autofmt_xdate()
plt.grid(True)
plt.tight_layout()
plt.savefig(img_rate_shape)


#%% Trended Treasury Rates Chart

img_rate_trend = './rate_trend.png'
df_1yr = df_send[df_send['duration'] == '1 Yr'][['Date', 'yield']]
df_10yr = df_send[df_send['duration'] == '10 Yr'][['Date', 'yield']]
df_30yr = df_send[df_send['duration'] == '30 Yr'][['Date', 'yield']]

fig, ax = plt.subplots()
ax.plot(df_1yr['Date'], df_1yr['yield'], label='1 Yr')
ax.plot(df_10yr['Date'], df_10yr['yield'], label='10 Yr')
ax.plot(df_30yr['Date'], df_30yr['yield'], label='30 Yr')
ax.set_title('Treasury Yield Trend', loc='center')
ax.set_ylabel('Yield')
ax.set_xlabel('Date')
ax.legend()
fig.autofmt_xdate()
plt.grid(True)
plt.tight_layout()
plt.savefig(img_rate_trend)


#%% Recent Treasury Rates Differential Table

df_tbl = df_piv.iloc[-2:].reset_index()
df_tbl_diff = df_tbl - df_tbl.shift(1)
df_tbl_diff['Date'] = 'Diff'
df_tbl_diff = df_tbl_diff.iloc[[1]]
df_tbl = pd.concat([df_tbl, df_tbl_diff])

body_table = build_table(df_tbl, 'green_light', font_size='small').replace('\n', '')
# with open(r"C:\Users\ericd\Downloads\tbl.html", 'w') as f:
#     f.write(body_table)


#%% Get S&P 500 Data

start = dt.date.today() + dt.timedelta(days=-31)
end = dt.date.today() + dt.timedelta(days=-1)

df_sp500 = web.DataReader(['sp500'], 'fred', start, end)


#%% Trend S&P 500 Chart

img_sp500 = './sp500.png'

fig, ax = plt.subplots()
ax.plot(df_sp500.index, df_sp500['sp500'], label='S&P 500')
ax.set_title('S&P 500 Trend', loc='center')
ax.set_ylabel('Price')
ax.set_xlabel('Date')
ax.legend()
fig.autofmt_xdate()
plt.grid(True)
plt.tight_layout()
plt.savefig(img_sp500)


#%% Send Email

body = [body_table, '<br>', img_rate_shape, '<br>', img_rate_trend, '<br>', img_sp500]

SendEmail(
    to_email_addresses=os.getenv('email_send')
    , subject=os.getenv('email_subject')
    , body=body
    , user=os.getenv('email_uid')
    , password=os.getenv('email_pwd')
    )


#%%