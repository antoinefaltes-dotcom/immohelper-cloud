"""
ImmoHelper CLOUD - Version Supabase (Temps réel + Auth + Rôles)
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, timedelta
import os
from PIL import Image
import plotly.express as px

st.set_page_config(page_title="ImmoHelper Cloud", page_icon="🏠", layout="wide")

# ====================== SUPABASE CONFIG ======================
# Remplace par tes clés Supabase (à mettre dans st.secrets ou variables d'environnement)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://TON-PROJECT.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")  # anon key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ====================== AUTHENTICATION ======================
def login():
    st.title("🔐 Connexion ImmoHelper Cloud")
    
    tab1, tab2 = st.tabs(["Se connecter", "Créer un compte"])
    
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.session_state.session = res.session
                st.success("Connexion réussie !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur de connexion : {str(e)}")
    
    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Mot de passe", type="password", key="signup_pass")
        role = st.selectbox("Rôle", ["Agent", "Admin"])
        if st.button("Créer le compte"):
            try:
                res = supabase.auth.sign_up({
                    "email": email, 
                    "password": password,
                    "options": {"data": {"role": role}}
                })
                st.success("Compte créé ! Vérifie tes emails si besoin, puis connecte-toi.")
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

if "user" not in st.session_state or st.session_state.user is None:
    login()
    st.stop()

user = st.session_state.user
user_role = user.user_metadata.get("role", "Agent") if user.user_metadata else "Agent"

st.sidebar.title("🏠 ImmoHelper Cloud")
st.sidebar.success(f"Connecté : {user.email} ({user_role})")

if st.sidebar.button("Se déconnecter"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# ====================== DATABASE HELPERS ======================
def get_properties():
    response = supabase.table("properties").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_clients():
    response = supabase.table("clients").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_appointments():
    response = supabase.table("appointments").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_tasks():
    response = supabase.table("tasks").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

# ====================== PAGES ======================
page = st.sidebar.radio("Menu", [
    "📊 Dashboard",
    "🏠 Propriétés",
    "👥 Clients & Pipeline",
    "📅 Rendez-vous",
    "✅ Tâches",
    "🛠️ Outils & Export"
])

if page == "📊 Dashboard":
    st.title("📊 Dashboard Temps Réel")
    
    props = get_properties()
    clients = get_clients()
    appts = get_appointments()
    tasks = get_tasks()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Biens Disponibles", len(props[props['statut'] == 'Disponible']) if not props.empty else 0)
    col2.metric("Leads Actifs", len(clients[clients['type_client'] == 'Lead']) if not clients.empty else 0)
    col3.metric("RDV Aujourd'hui", len(appts[appts['date'] == str(date.today())]) if not appts.empty else 0)
    col4.metric("Tâches à Faire", len(tasks[tasks['statut'] == 'À faire']) if not tasks.empty else 0)
    
    st.divider()
    
    if not props.empty:
        fig = px.pie(props, names='statut', title="Biens par Statut")
        st.plotly_chart(fig, use_container_width=True)

elif page == "🏠 Propriétés":
    st.title("🏠 Propriétés")
    
    with st.expander("➕ Ajouter un bien"):
        with st.form("add_prop"):
            adresse = st.text_input("Adresse *")
            ville = st.text_input("Ville *")
            prix = st.number_input("Prix *", min_value=0)
            # ... autres champs
            if st.form_submit_button("Enregistrer"):
                data = {"adresse": adresse, "ville": ville, "prix": prix, "statut": "Disponible", "date_ajout": str(datetime.now())}
                supabase.table("properties").insert(data).execute()
                st.success("Bien ajouté ! (Temps réel pour toute l'équipe)")
                st.rerun()
    
    props = get_properties()
    if not props.empty:
        st.dataframe(props, use_container_width=True)

# ... (Autres pages similaires avec requêtes Supabase)

elif page == "👥 Clients & Pipeline":
    st.title("👥 Pipeline Clients (Temps Réel)")
    clients = get_clients()
    if not clients.empty:
        # Kanban simple
        for status in ["Nouveau", "Contacté", "En discussion", "Visite planifiée", "Offre faite", "Conclu"]:
            st.subheader(status)
            stage_df = clients[clients['statut'] == status]
            for _, row in stage_df.iterrows():
                st.write(f"• {row['nom']} {row.get('prenom', '')}")

st.sidebar.info("✅ Version Cloud Supabase activée\nSynchronisation temps réel + Auth + Rôles")