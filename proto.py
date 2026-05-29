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
    
    # Menampilkan riwayat chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input chat pelanggan
    if prompt := st.chat_input("Ketik pesan Anda di sini..."):
        # 1. Tampilkan pesan user ke UI
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. Proses ke n8n
        with st.chat_message("model"):
            with st.spinner("AI sedang memproses via n8n..."):
                try:
                    payload = {
                        "pesan_baru": prompt,
                        "riwayat_chat": st.session_state.messages
                    }
                    
                    response = requests.post(N8N_WEBHOOK_URL, json=payload)
                    
                    if response.status_code == 200:
                        n8n_data = response.json()
                        st.write("Data asli dari n8n:", n8n_data)
                        ai_reply = n8n_data.get("balasan_ai", "Maaf, sistem sedang sibuk.")
                        
                        # Ekstraksi LEAD
                        display_reply = ai_reply
                        lead_match = re.search(r'===LEAD:(.*?)===', ai_reply, re.DOTALL)
                        
                        if lead_match:
                            try:
                                lead_json_str = lead_match.group(1).strip()
                                lead_dict = json.loads(lead_json_str)
                                st.session_state.leads_data.append(lead_dict)
                                display_reply = ai_reply.replace(lead_match.group(0), "").strip()
                            except:
                                pass # Abaikan jika JSON rusak

                        st.markdown(display_reply)
                        st.session_state.messages.append({"role": "model", "content": display_reply})
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
        st.info("Belum ada lead yang tertangkap.")
