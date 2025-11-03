# ============================================
# app.py - Olist E-Commerce Dashboard (Streamlit)
# ============================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ===============================
# Konfigurasi Dashboard
# ===============================
st.set_page_config(page_title="Olist E-Commerce Dashboard", layout="wide")

st.title("Olist E-Commerce Dashboard")
st.markdown("""
Dashboard ini dibuat untuk menjawab dua pertanyaan bisnis utama:
1. **Bagaimana pola performa penjualan dari waktu ke waktu?**
2. **Faktor apa yang berpengaruh terhadap kepuasan pelanggan (terutama waktu pengiriman)?**
""")

# ===============================
# Load Data
# ===============================
@st.cache_data
def load_data():
    df = pd.read_csv("olist_cleaned_dataset.csv")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File 'olist_cleaned_dataset.csv' tidak ditemukan.")
    st.stop()

# ===============================
# Preprocessing dasar
# ===============================
# Pastikan kolom tanggal bertipe datetime
date_cols = [col for col in df.columns if "date" in col or "timestamp" in col]
for col in date_cols:
    try:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    except Exception:
        pass

# Buat kolom delivery_time_days jika belum ada
if 'delivery_time_days' not in df.columns:
    if 'order_delivered_customer_date' in df.columns and 'order_purchase_timestamp' in df.columns:
        df['delivery_time_days'] = (
            df['order_delivered_customer_date'] - df['order_purchase_timestamp']
        ).dt.days

# Hapus baris tidak valid
df = df[df['delivery_time_days'].notna()]
df = df[df['delivery_time_days'] >= 0]

# Tambahkan kolom periode
df['order_year_month'] = df['order_purchase_timestamp'].dt.to_period('M')
df['order_year'] = df['order_purchase_timestamp'].dt.year

# ===============================
# Filter Global (Sidebar)
# ===============================
st.sidebar.header("🔍 Filter Data Global")

tahun_opsi = ['Semua'] + sorted(df['order_year'].dropna().unique().tolist())
tahun_terpilih = st.sidebar.selectbox("Pilih Tahun:", options=tahun_opsi, index=0)

# Terapkan filter tahun
filtered_df = df.copy()
if tahun_terpilih != 'Semua':
    filtered_df = filtered_df[filtered_df['order_year'] == tahun_terpilih]

# ===============================
# Tabs untuk Pertanyaan Bisnis
# ===============================
tab1, tab2 = st.tabs([
    "Tren Penjualan dari Waktu ke Waktu",
    "Hubungan Waktu Pengiriman & Kepuasan Pelanggan"
])

# ======================================================
# TAB 1: Tren Penjualan
# ======================================================
with tab1:
    st.header("Bagaimana Pola Performa Penjualan dari Waktu ke Waktu?")
    st.markdown(f"**Tahun:** {tahun_terpilih}")

    # --- Visualisasi 1: Jumlah Pesanan per Bulan ---
    orders_per_month = (
        filtered_df.groupby(filtered_df['order_purchase_timestamp'].dt.to_period('M'))['order_id']
        .nunique()
        .reset_index(name='num_orders')
    )
    orders_per_month['order_purchase_timestamp'] = orders_per_month['order_purchase_timestamp'].dt.to_timestamp()

    st.subheader("Tren Jumlah Pesanan per Bulan")
    fig, ax = plt.subplots(figsize=(12,5))
    sns.lineplot(x='order_purchase_timestamp', y='num_orders', data=orders_per_month, marker='o', linewidth=2.2, ax=ax)
    ax.set_title(f"Tren Jumlah Pesanan {'(Semua Tahun)' if tahun_terpilih == 'Semua' else f'Tahun {tahun_terpilih}'}", fontsize=14)
    ax.set_xlabel('Bulan')
    ax.set_ylabel('Jumlah Pesanan')
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # --- Visualisasi 2: Total Pendapatan per Bulan ---
    st.subheader("Tren Total Pendapatan per Bulan")
    revenue_per_month = (
        filtered_df.groupby(filtered_df['order_purchase_timestamp'].dt.to_period('M'))['price']
        .sum()
        .reset_index()
    )
    revenue_per_month['order_purchase_timestamp'] = revenue_per_month['order_purchase_timestamp'].dt.to_timestamp()

    fig2, ax2 = plt.subplots(figsize=(12,5))
    sns.barplot(x='order_purchase_timestamp', y='price', data=revenue_per_month, color='skyblue', ax=ax2)
    ax2.set_title(f"Total Pendapatan {'(Semua Tahun)' if tahun_terpilih == 'Semua' else f'Tahun {tahun_terpilih}'}", fontsize=14)
    ax2.set_xlabel('Bulan')
    ax2.set_ylabel('Total Pendapatan (BRL)')
    plt.xticks(rotation=45)
    st.pyplot(fig2)

    # --- Visualisasi 3: Top 10 Kategori Produk ---
    st.subheader("Top 10 Kategori Produk Berdasarkan Total Pendapatan")

    top10_products = (
        filtered_df.groupby('product_category_name')['price']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )


    fig3, ax3 = plt.subplots(figsize=(10,6))
    sns.barplot(y='product_category_name', x='price', data=top10_products, palette='cool', ax=ax3)
    ax3.set_title(f"Top 10 Kategori Produk {'(Semua Tahun)' if tahun_terpilih == 'Semua' else f'Tahun {tahun_terpilih}'}", fontsize=14)
    ax3.set_xlabel('Total Pendapatan (BRL)')
    ax3.set_ylabel('Kategori Produk')
    st.pyplot(fig3)

    

# ======================================================
# TAB 2: Waktu Pengiriman & Kepuasan Pelanggan
# ======================================================
with tab2:
    st.header("Hubungan antara Waktu Pengiriman dan Skor Ulasan")
    st.markdown(f"**Tahun:** {tahun_terpilih}")

    # Distribusi Lama Pengiriman
    st.subheader("Distribusi Lama Pengiriman (Hari)")
    fig1, ax1 = plt.subplots(figsize=(10,5))
    sns.histplot(filtered_df['delivery_time_days'], bins=40, kde=True, color='lightblue', ax=ax1)
    ax1.set_title('Distribusi Lama Pengiriman (Hari)')
    ax1.set_xlabel('Lama Pengiriman (hari)')
    ax1.set_ylabel('Jumlah Pesanan')
    st.pyplot(fig1)

    # Rata-rata Waktu Pengiriman per Skor Review
    st.subheader("Rata-rata Lama Pengiriman Berdasarkan Review Score")
    delivery_vs_review = (
        filtered_df.groupby('review_score')['delivery_time_days']
        .mean()
        .reset_index()
    )
    fig2, ax2 = plt.subplots(figsize=(8,5))
    sns.barplot(x='review_score', y='delivery_time_days', data=delivery_vs_review, palette='coolwarm', ax=ax2)
    ax2.set_title('Rata-rata Lama Pengiriman Berdasarkan Review Score')
    ax2.set_xlabel('Review Score')
    ax2.set_ylabel('Rata-rata Lama Pengiriman (hari)')
    st.pyplot(fig2)

    # Hubungan Review Score vs Delivery Time
    st.subheader("Hubungan antara Skor Review dan Lama Pengiriman")
    avg_delivery = (
        filtered_df.groupby('review_score')['delivery_time_days']
        .mean()
        .reset_index()
        .sort_values(by='review_score', ascending=True)
    )

    fig3, ax3 = plt.subplots(figsize=(10,6))
    sns.lineplot(x='delivery_time_days', y='review_score', data=avg_delivery, marker='o', color='orange', ax=ax3)
    ax3.set_title('Hubungan antara Skor Review dan Lama Pengiriman', fontsize=14)
    ax3.set_xlabel('Rata-rata Delivery Time (hari)')
    ax3.set_ylabel('Review Score')
    ax3.grid(True)
    st.pyplot(fig3)

# ======================================================
# Footer
# ======================================================
st.markdown("---")
st.caption("© 2025 - Dicoding Data Analysist ")
