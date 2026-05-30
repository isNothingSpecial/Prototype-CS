import streamlit as st
import requests
import pandas as pd
import json
import re

# ==========================================
# 1. KONFIGURASI
# ==========================================
N8N_WEBHOOK_URL = "https://nspstudio13.app.n8n.cloud/webhook/ujicoba-chat"

st.set_page_config(page_title="AI CS Prototype", layout="wide")

# Inisialisasi Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "leads_data" not in st.session_state:
    st.session_state.leads_data = []

# ==========================================
# 2. TAMPILAN ANTARMUKA
# ==========================================
col1, col2 = st.columns([2, 1])

with col1:
    st.title("📱 Simulasi Chat CS WhatsApp")
    st.caption("Berperanlah sebagai pelanggan, lalu berikan data untuk order.")
    
    # Menampilkan riwayat chat di layar
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input chat pelanggan
    if prompt := st.chat_input("Ketik pesan Anda di sini..."):
        
        # 1. Tampilkan pesan user ke layar
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. Proses pengiriman ke n8n
        with st.spinner("AI sedang memproses via n8n..."):
            try:
                # KARENA N8N SUDAH PAKAI MEMORY, KITA CUKUP KIRIM PESAN BARU & SESSION ID
                payload = {
                    "pesan_user": prompt,
                    "session_id": "sesi_chat_01" 
                }
                
                response = requests.post(N8N_WEBHOOK_URL, json=payload)
                
                if response.status_code == 200:
                    n8n_data = response.json()
                    
                    # === TAMBAHKAN BARIS INI UNTUK DEBUGGING ===
                    st.error("DEBUG DATA MENTAH DARI N8N:")
                    st.json(n8n_data)
                    # ===========================================
                    
                    # Ambil balasan dari n8n
                    ai_reply = n8n_data.get("output", "Maaf, sistem sedang sibuk.")
                    
                    # 3. Ekstraksi LEAD (Filter format JSON tersembunyi)
                    display_reply = ai_reply
                    lead_match = re.search(r'===LEAD:(.*?)===', ai_reply, re.DOTALL)
                    
                    if lead_match:
                        try:
                            lead_json_str = lead_match.group(1).strip()
                            lead_dict = json.loads(lead_json_str)
                            # Masukkan data ke tabel CRM
                            st.session_state.leads_data.append(lead_dict)
                            # Hapus teks ===LEAD:...=== agar tidak terbaca oleh pelanggan
                            display_reply = ai_reply.replace(lead_match.group(0), "").strip()
                        except:
                            pass # Abaikan jika format JSON rusak dari AI

                    # 4. Tampilkan balasan AI yang sudah bersih ke layar
                    with st.chat_message("assistant"):
                        st.markdown(display_reply)
                    
                    # Simpan ke memori lokal Streamlit agar tetap tampil saat layar di-refresh
                    st.session_state.messages.append({"role": "assistant", "content": display_reply})
                
                else:
                    st.error(f"Error HTTP {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"Terjadi kesalahan koneksi: {e}")

# ==========================================
# 3. DASHBOARD CRM (DATA LEAD)
# ==========================================
with col2:
    st.title("🗄️ Database Lead (CRM)")
    
    if st.session_state.leads_data:
        df_leads = pd.DataFrame(st.session_state.leads_data)
        st.dataframe(df_leads, use_container_width=True)
    else:
        st.info("Belum ada lead yang tertangkap. Minta pelanggan menyebutkan pesanan, nama, dan no HP.")
