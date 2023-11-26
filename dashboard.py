import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='whitegrid')


# menyiapkan daily_orders_df
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_delivered_customer_date').agg({
        "order_id": "nunique",
        "price": "sum",
        "seller_id": "nunique"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue",
        "seller_id": "seller_count"
    }, inplace=True)

    return daily_orders_df


# menyiapkan sum_orders_items_df
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name").product_photos_qty.sum().sort_values(
        ascending=False).reset_index()
    return sum_order_items_df


# untuk menyiapkan bystate_df
def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count",
        "customer_state": "state"
    }, inplace=True)

    return bystate_df


# untuk menghasilkan rfm_df
def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_delivered_customer_date": "max",  # mengambil tanggal order terakhir
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_delivered_customer_date"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df


# load berkas
main_df = pd.read_csv("main_data.csv")

# mengurutkan DataFrame
datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
main_df.sort_values(by="order_delivered_customer_date", inplace=True)
main_df.reset_index(inplace=True)

for column in datetime_columns:
    main_df[column] = pd.to_datetime(main_df[column])

## Membuat Komponen Filter
min_date = main_df["order_delivered_customer_date"].min()
max_date = main_df["order_delivered_customer_date"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")

    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# data disimpan dalam all_df
all_df = main_df[(main_df["order_delivered_customer_date"] >= str(start_date)) &
                 (main_df["order_delivered_customer_date"] <= str(end_date))]

# memanggil helper function untuk menghasilkan berbagai DataFrame yang dibutuhkan untuk membuat visualisasi data
daily_orders_df = create_daily_orders_df(all_df)
sum_order_items_df = create_sum_order_items_df(all_df)
bystate_df = create_bystate_df(all_df)
rfm_df = create_rfm_df(all_df)

# Melengkapi Dashboard dengan Berbagai Visualisasi Data
st.header('Dicoding Collection Dashboard :sparkles:')

#  menambahkan informasi terkait daily orders pada dashboard_latihan
st.subheader('Daily Orders')

col1, col2, col3 = st.columns(3)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "$", locale='es_CO')
    st.metric("Total Revenue", value=total_revenue)

with col3:
    total_seller = daily_orders_df.seller_count.sum()
    st.metric("Total seller", value=total_seller)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_delivered_customer_date"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

# menyertakan informasi tentang performa penjualan dari setiap produk
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9"]

sns.barplot(x="product_photos_qty", y="product_category_name", data=sum_order_items_df.head(5), palette=colors,
            ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="product_photos_qty", y="product_category_name",
            data=sum_order_items_df.sort_values(by="product_photos_qty", ascending=True).head(5), palette=colors,
            ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

# menambahkan visualisasi Customer Demographics
st.subheader("Customer Demographics")

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9"]
sns.barplot(
    x="customer_count",
    y="state",
    data=bystate_df.sort_values(by="customer_count", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title("Number of Customer by state", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

# menampilkan nilai average atau rata-rata dari ketiga parameter tersebut menggunakan widget metric()
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "$", locale='es_CO')
    st.metric("Average Monetary", value=avg_frequency)

st.caption('Copyright (c) Maulida Nabya Islami 2023')