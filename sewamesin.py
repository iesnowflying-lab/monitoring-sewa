import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sewa Mesin ISG", layout="wide")
st.title("Sistem Monitoring Penyewaan Mesin (Cloud Version)")

# 2. Koneksi ke Google Sheets
# Masukkan URL Google Sheets Anda di sini
url_sheets = "https://docs.google.com/spreadsheets/d/1BvYyCa0DgJrjuMYQzFEL_49_StYhr71rzvNJ8crwHaU/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(spreadsheet=url_sheets, usecols=list(range(10)), ttl="0")

df_original = load_data()

# 3. FORM INPUT
st.subheader("Input Data Sewa Baru 📝")
with st.form(key="input_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        jenis_mesin = st.text_input("Jenis Mesin")
        merek = st.text_input("Merek")
        tipe_spesifik = st.text_input("Type")
        qty = st.number_input("Qty", min_value=1, step=1)
    with col2:
        dari_from = st.text_input("From")
        ke_to = st.text_input("To")
        no_surat = st.text_input("No Surat")
        tgl_start = st.date_input("Start Sewa")
        tgl_akhir = st.date_input("Akhir Sewa")

    submit_button = st.form_submit_button(label="Simpan Data")

    if submit_button:
        new_row = pd.DataFrame([{
            "Jenis_Mesin": jenis_mesin,
            "Merek": merek,
            "Type": tipe_spesifik,
            "Qty": qty,
            "From": dari_from,
            "To": ke_to,
            "No_Surat": no_surat,
            "Start_Sewa": tgl_start.strftime('%Y-%m-%d'),
            "Akhir_Sewa": tgl_akhir.strftime('%Y-%m-%d'),
            "Status_Kembali": False
        }])
        
        # Gabungkan data lama dengan data baru
        updated_df = pd.concat([df_original, new_row], ignore_index=True)
        
        # Update ke Google Sheets
        conn.update(spreadsheet=url_sheets, data=updated_df)
        st.success("Data Berhasil Disimpan ke Cloud!")
        st.rerun()

st.divider()

# 4. TAMPILAN TABEL
if not df_original.empty:
    # Filter data yang belum kembali
    df_display = df_original[df_original['Status_Kembali'] == False].copy()

    if not df_display.empty:
        df_display['Start_Sewa'] = pd.to_datetime(df_display['Start_Sewa']).dt.date
        df_display['Akhir_Sewa'] = pd.to_datetime(df_display['Akhir_Sewa']).dt.date
        df_display = df_display.sort_values(by='Akhir_Sewa')

        hari_ini = datetime.now().date()
        df_display['Sisa Hari'] = df_display['Akhir_Sewa'].apply(lambda x: (x - hari_ini).days)
        
        df_display.insert(0, 'No', range(1, len(df_display) + 1))

        st.subheader("Jadwal Pengembalian Mesin 🗓️")
        
        edited_df = st.data_editor(
            df_display,
            column_config={
                "Status_Kembali": st.column_config.CheckboxColumn("Selesai?", default=False),
                "Sisa Hari": st.column_config.NumberColumn("Sisa Hari", format="%d hari"),
            },
            disabled=["No", "Jenis_Mesin", "Merek", "Type", "Qty", "From", "To", "No_Surat", "Start_Sewa", "Akhir_Sewa", "Sisa Hari"],
            hide_index=True,
            use_container_width=True,
            key="editor_cloud"
        )

        # Update status kembali jika ada perubahan
        if not edited_df['Status_Kembali'].equals(df_display['Status_Kembali']):
            for i, row in edited_df.iterrows():
                if row['Status_Kembali'] == True:
                    mask = (df_original['No_Surat'] == row['No_Surat']) & (df_original['Jenis_Mesin'] == row['Jenis_Mesin'])
                    df_original.loc[mask, 'Status_Kembali'] = True
            
            conn.update(spreadsheet=url_sheets, data=df_original)
            st.rerun()
    else:
        st.success("Semua mesin sudah kembali.")

if st.button("Segarkan Data 🔄"):
    st.rerun()