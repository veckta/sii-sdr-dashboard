import streamlit as st
import pandas as pd
import os
import httpx
from dotenv import load_dotenv

# Configuración de página
st.set_page_config(page_title="Veckta SDR - Auditoría Comercial", page_icon="📊", layout="wide")

# Cargar variables de entorno
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Función para obtener datos vía REST API (Arquitectura Antigravity)
def get_chats():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Faltan credenciales de Supabase en el archivo .env")
        return pd.DataFrame()
    
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/historial_chats?select=*&order=timestamp.desc"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            res.raise_for_status()
            return pd.DataFrame(res.json())
    except Exception as e:
        st.error(f"Error al conectar con Supabase REST API: {e}")
        return pd.DataFrame()

# Estilo Personalizado
st.markdown("""
    <style>
    .metric-card {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Veckta SDR: Panel de Auditoría")
st.markdown("---")

# 1. Obtener Datos
df = get_chats()

if not df.empty:
    # 2. KPIs Superiores
    col1, col2, col3, col4 = st.columns(4)
    
    total_convs = df['whatsapp_id'].nunique()
    abono = df[df['clasificacion_sdr'] == 'Abono']['whatsapp_id'].nunique()
    alta_escala = df[df['clasificacion_sdr'] == 'Alta Escala']['whatsapp_id'].nunique()
    rechazo = df[df['clasificacion_sdr'] == 'Rechazo']['whatsapp_id'].nunique()
    
    col1.metric("Conversaciones Únicas", total_convs)
    col2.metric("Abonos Cerrados", abono)
    col3.metric("Leads Alta Escala", alta_escala)
    col4.metric("Descartados", rechazo, delta_color="inverse")
    
    st.markdown("---")
    
    # 3. Sidebar - Selector de Cliente
    st.sidebar.header("🔍 Filtros de Auditoría")
    clientes = sorted(df['whatsapp_id'].unique())
    cliente_sel = st.sidebar.selectbox("Seleccionar Cliente (ID)", clientes)
    
    # Info del Lead en Sidebar
    df_cliente = df[df['whatsapp_id'] == cliente_sel].iloc[0]
    st.sidebar.info(f"Última Actividad: {df_cliente['timestamp'][:16]}")
    
    # 4. Área de Chat
    st.subheader(f"💬 Conversación con: {cliente_sel}")
    
    chats_cliente = df[df['whatsapp_id'] == cliente_sel].sort_values("timestamp")
    
    for _, row in chats_cliente.iterrows():
        role = "user" if row['role'] == "user" else "assistant"
        with st.chat_message(role):
            st.write(row['mensaje'])
            st.caption(f"{row['timestamp'][11:16]}")
            if row['clasificacion_sdr']:
                st.warning(f"🎯 Clasificación detectada: {row['clasificacion_sdr']}")
else:
    st.info("Aún no hay registros en la tabla historial_chats o hubo un error de conexión.")
    st.markdown("Aseguráte de que la tabla exista en Supabase y que las credenciales en el .env sean correctas.")
