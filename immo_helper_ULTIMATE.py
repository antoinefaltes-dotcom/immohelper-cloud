import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import sqlite3
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# ====================== CONFIG ======================
st.set_page_config(
    page_title="ImmoHelper ULTIMATE - Agence Immobilière",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1E3A5F;}
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;}
    .stButton>button {background-color: #1E3A5F; color: white;}
    .section-header {border-bottom: 2px solid #1E3A5F; padding-bottom: 5px; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

DATA_DIR = "immo_ULTIMATE_data"
IMAGES_DIR = os.path.join(DATA_DIR, "photos")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "immo_ultimate.db")

# ====================== DATABASE ======================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adresse TEXT NOT NULL,
        ville TEXT NOT NULL,
        prix REAL NOT NULL,
        type TEXT,
        chambres INTEGER DEFAULT 0,
        sdb INTEGER DEFAULT 0,
        surface REAL,
        statut TEXT DEFAULT 'Disponible',
        description TEXT,
        date_ajout TEXT,
        photo_path TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT,
        telephone TEXT,
        email TEXT,
        type_client TEXT,
        statut TEXT DEFAULT 'Nouveau',
        notes TEXT,
        date_ajout TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        heure TEXT,
        type_rdv TEXT,
        client_id INTEGER,
        property_id INTEGER,
        notes TEXT,
        statut TEXT DEFAULT 'Planifié',
        FOREIGN KEY (client_id) REFERENCES clients(id),
        FOREIGN KEY (property_id) REFERENCES properties(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        priorite TEXT DEFAULT 'Moyenne',
        statut TEXT DEFAULT 'À faire',
        linked_to TEXT,
        date_creation TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS team_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'Agent'
    )''')
    
    # Add default user if none exists
    c.execute("SELECT COUNT(*) FROM team_users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO team_users (name, role) VALUES ('Agent Principal', 'Admin')")
    
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_FILE)

def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id

init_db()

# ====================== SESSION STATE ======================
for key in ['show_add_prop', 'show_add_client', 'show_add_appt', 'show_add_task', 'current_user']:
    if key not in st.session_state:
        st.session_state[key] = False if 'show' in key else None

if st.session_state.current_user is None:
    users = query_df("SELECT * FROM team_users")
    if not users.empty:
        st.session_state.current_user = users.iloc[0]['name']

# ====================== SIDEBAR ======================
st.sidebar.title("🏠 ImmoHelper ULTIMATE")
st.sidebar.markdown("**Version Finale - Équipe Agence**")

# User selector (simple team simulation)
users_df = query_df("SELECT * FROM team_users")
user_names = users_df['name'].tolist() if not users_df.empty else ["Agent"]
selected_user = st.sidebar.selectbox("👤 Utilisateur connecté", user_names, 
                                     index=user_names.index(st.session_state.current_user) if st.session_state.current_user in user_names else 0)
st.session_state.current_user = selected_user

st.sidebar.caption(f"Connecté en tant que : **{selected_user}**")

page = st.sidebar.radio("Menu", [
    "📊 Dashboard Ultime",
    "🏠 Propriétés + Photos",
    "👥 CRM Clients & Pipeline",
    "📅 Planning & RDV",
    "✅ Kanban Tâches",
    "🛠️ Outils IA & Export"
])

st.sidebar.divider()
st.sidebar.info("""
**Collaboration d'équipe :**
- Partagez le dossier `immo_ULTIMATE_data`
- Via Google Drive / Dropbox / NAS / clé USB
- Tout le monde voit les mêmes données en temps réel (dès que le fichier est synchronisé)
- Pas besoin de serveur pour l'instant
""")

# ====================== DASHBOARD ULTIME ======================
if page == "📊 Dashboard Ultime":
    st.markdown('<h1 class="main-header">📊 Dashboard ImmoHelper ULTIME</h1>', unsafe_allow_html=True)
    st.caption(f"Bienvenue {selected_user} • Mis à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    props = query_df("SELECT * FROM properties")
    clients = query_df("SELECT * FROM clients")
    appts = query_df("SELECT * FROM appointments")
    tasks = query_df("SELECT * FROM tasks")
    
    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Biens Disponibles", len(props[props['statut'] == 'Disponible']) if not props.empty else 0)
    k2.metric("Leads en Pipeline", len(clients[clients['type_client'] == 'Lead']) if not clients.empty else 0)
    k3.metric("RDV Aujourd'hui", len(appts[appts['date'] == date.today().strftime("%Y-%m-%d")]) if not appts.empty else 0)
    k4.metric("Tâches à Faire", len(tasks[tasks['statut'] == 'À faire']) if not tasks.empty else 0)
    k5.metric("Total Biens", len(props) if not props.empty else 0)
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        if not props.empty:
            fig = px.pie(props, names='statut', title="Répartition des Biens par Statut", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if not clients.empty:
            fig2 = px.bar(clients['statut'].value_counts(), title="Pipeline Clients", color_discrete_sequence=['#1E3A5F'])
            st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # Quick views
    st.subheader("🔥 Activité du Jour")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Biens récemment ajoutés**")
        if not props.empty:
            st.dataframe(props.sort_values('date_ajout', ascending=False).head(4)[['adresse', 'ville', 'prix', 'statut']], hide_index=True)
    with col_b:
        st.markdown("**Prochains RDV**")
        today_str = date.today().strftime("%Y-%m-%d")
        upcoming = appts[appts['date'] >= today_str].sort_values(['date', 'heure']).head(4) if not appts.empty else pd.DataFrame()
        if not upcoming.empty:
            st.dataframe(upcoming[['date', 'heure', 'type_rdv', 'notes']], hide_index=True)
        else:
            st.info("Aucun RDV proche")

# ====================== PROPRIÉTÉS ULTIME ======================
elif page == "🏠 Propriétés + Photos":
    st.markdown('<h1 class="main-header">🏠 Propriétés + Galerie Photos</h1>', unsafe_allow_html=True)
    
    # Add form in expander
    with st.expander("➕ Ajouter une nouvelle propriété", expanded=st.session_state.show_add_prop):
        with st.form("add_prop_ultimate", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                adresse = st.text_input("Adresse complète *")
                ville = st.text_input("Ville *")
                prix = st.number_input("Prix de vente (€) *", min_value=1000, step=5000)
            with col2:
                type_bien = st.selectbox("Type de bien", ["Appartement", "Maison", "Villa", "Duplex", "Terrain", "Local pro"])
                chambres = st.number_input("Chambres", 0, 20, 3)
                sdb = st.number_input("Salles de bain", 0, 10, 1)
            with col3:
                surface = st.number_input("Surface (m²)", 10, 1000, 80)
                statut = st.selectbox("Statut", ["Disponible", "Sous offre", "Vendu", "Retiré du marché"])
            
            description = st.text_area("Description détaillée")
            photo_file = st.file_uploader("Photo principale (JPG/PNG)", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("✅ Enregistrer le bien"):
                if adresse and ville and prix > 0:
                    photo_path = None
                    if photo_file:
                        fname = f"prop_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo_file.name}"
                        photo_path = os.path.join(IMAGES_DIR, fname)
                        with open(photo_path, "wb") as f:
                            f.write(photo_file.getbuffer())
                    
                    execute("INSERT INTO properties (adresse, ville, prix, type, chambres, sdb, surface, statut, description, date_ajout, photo_path) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (adresse, ville, prix, type_bien, chambres, sdb, surface, statut, description, datetime.now().strftime("%Y-%m-%d %H:%M"), photo_path))
                    st.success("Bien ajouté avec succès !")
                    st.rerun()
                else:
                    st.error("Adresse, Ville et Prix sont obligatoires.")

    st.divider()
    
    # Advanced filters
    props = query_df("SELECT * FROM properties")
    search = st.text_input("🔍 Recherche globale (adresse, ville, description)")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: f_statut = st.selectbox("Statut", ["Tous"] + ["Disponible", "Sous offre", "Vendu", "Retiré du marché"])
    with c2: f_min = st.number_input("Prix min", 0, step=10000, value=0)
    with c3: f_max = st.number_input("Prix max", 0, step=10000, value=5000000)
    with c4: f_type = st.selectbox("Type", ["Tous"] + list(props['type'].unique()) if not props.empty else ["Tous"])
    
    filtered = props.copy()
    if search:
        filtered = filtered[filtered.apply(lambda r: search.lower() in ' '.join(r.astype(str)).lower(), axis=1)]
    if f_statut != "Tous":
        filtered = filtered[filtered['statut'] == f_statut]
    if f_min > 0:
        filtered = filtered[filtered['prix'] >= f_min]
    if f_max > 0:
        filtered = filtered[filtered['prix'] <= f_max]
    if f_type != "Tous":
        filtered = filtered[filtered['type'] == f_type]
    
    st.markdown(f"**{len(filtered)} bien(s) affiché(s)**")
    
    if not filtered.empty:
        for _, row in filtered.iterrows():
            with st.container(border=True):
                col_photo, col_details, col_actions = st.columns([1.2, 3, 1.5])
                
                with col_photo:
                    if row['photo_path'] and os.path.exists(row['photo_path']):
                        try:
                            img = Image.open(row['photo_path'])
                            st.image(img, use_column_width=True)
                        except:
                            st.write("📷 Erreur photo")
                    else:
                        st.write("📷 Aucune photo")
                
                with col_details:
                    st.markdown(f"### {row['adresse']}")
                    st.write(f"**{row['ville']}** • **{int(row['prix']):,} €** • {row['type']} • {row['chambres']} ch • {row['surface']} m² • **{row['statut']}**")
                    if row['description']:
                        st.caption(row['description'][:200] + ("..." if len(str(row['description'])) > 200 else ""))
                
                with col_actions:
                    if st.button("✏️ Changer statut", key=f"stat_{row['id']}"):
                        new_stat = st.selectbox("Nouveau statut", ["Disponible", "Sous offre", "Vendu", "Retiré du marché"], key=f"ns_{row['id']}")
                        if st.button("Valider", key=f"valstat_{row['id']}"):
                            execute("UPDATE properties SET statut=? WHERE id=?", (new_stat, row['id']))
                            st.success("Mis à jour")
                            st.rerun()
                    
                    if st.button("📅 Planifier visite", key=f"rdv_{row['id']}"):
                        st.session_state.show_add_appt = True
                        # Could preselect property in future versions
                    
                    if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                        execute("DELETE FROM properties WHERE id=?", (row['id'],))
                        st.warning("Bien supprimé")
                        st.rerun()
    else:
        st.info("Aucun bien trouvé avec ces filtres.")

# ====================== CLIENTS ULTIME ======================
elif page == "👥 Clients & Leads":
    st.markdown('<h1 class="main-header">👥 CRM & Pipeline Clients</h1>', unsafe_allow_html=True)
    
    with st.expander("➕ Ajouter un nouveau client/lead"):
        with st.form("add_client_ult"):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom *")
                prenom = st.text_input("Prénom")
                tel = st.text_input("Téléphone")
            with c2:
                email = st.text_input("Email")
                typ = st.selectbox("Type", ["Lead", "Acheteur", "Vendeur", "Locataire"])
                pipeline = st.selectbox("Étape Pipeline", ["Nouveau", "Contacté", "En discussion", "Visite planifiée", "Offre faite", "Conclu", "Perdu"])
            notes = st.text_area("Notes / Historique")
            
            if st.form_submit_button("Enregistrer client"):
                if nom:
                    execute("INSERT INTO clients (nom, prenom, telephone, email, type_client, statut, notes, date_ajout) VALUES (?,?,?,?,?,?,?,?)",
                            (nom, prenom, tel, email, typ, pipeline, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.success("Client ajouté au pipeline !")
                    st.rerun()
    
    st.divider()
    
    clients = query_df("SELECT * FROM clients")
    search_c = st.text_input("Rechercher dans les clients")
    
    if search_c:
        clients = clients[clients.apply(lambda r: search_c.lower() in ' '.join(r.astype(str)).lower(), axis=1)]
    
    if not clients.empty:
        st.dataframe(clients[['id', 'nom', 'prenom', 'telephone', 'email', 'type_client', 'statut']], use_container_width=True, hide_index=True)
        
        # Pipeline Kanban simple
        st.subheader("📌 Vue Pipeline (Kanban)")
        pipeline_stages = ["Nouveau", "Contacté", "En discussion", "Visite planifiée", "Offre faite", "Conclu"]
        cols = st.columns(len(pipeline_stages))
        
        for i, stage in enumerate(pipeline_stages):
            with cols[i]:
                stage_clients = clients[clients['statut'] == stage]
                st.markdown(f"**{stage}** ({len(stage_clients)})")
                for _, cl in stage_clients.iterrows():
                    st.write(f"• {cl['nom']} {cl['prenom'] or ''}")
    else:
        st.info("Ajoutez des clients pour voir le pipeline.")

# ====================== RENDEZ-VOUS ======================
elif page == "📅 Rendez-vous":
    st.markdown('<h1 class="main-header">📅 Planning des Rendez-vous</h1>', unsafe_allow_html=True)
    
    with st.expander("➕ Planifier un nouveau rendez-vous"):
        with st.form("add_appt_ult"):
            d = st.date_input("Date")
            h = st.time_input("Heure")
            typ = st.selectbox("Type de rendez-vous", ["Visite", "Signature compromis", "Signature définitive", "Estimation", "Suivi client", "Autre"])
            
            clients = query_df("SELECT id, nom || ' ' || COALESCE(prenom,'') as name FROM clients")
            props = query_df("SELECT id, adresse || ' - ' || ville as name FROM properties")
            
            sel_client = st.selectbox("Client", clients['id'].tolist(), format_func=lambda x: clients[clients['id']==x]['name'].values[0]) if not clients.empty else None
            sel_prop = st.selectbox("Bien concerné (optionnel)", [None] + props['id'].tolist(), format_func=lambda x: "Aucun" if x is None else props[props['id']==x]['name'].values[0]) if not props.empty else None
            
            notes = st.text_area("Notes / Instructions")
            
            if st.form_submit_button("Planifier le RDV"):
                if sel_client:
                    execute("INSERT INTO appointments (date, heure, type_rdv, client_id, property_id, notes, statut) VALUES (?,?,?,?,?,?,?)",
                            (d.strftime("%Y-%m-%d"), str(h), typ, sel_client, sel_prop, notes, "Planifié"))
                    st.success("Rendez-vous planifié avec succès !")
                    st.rerun()
    
    st.divider()
    st.subheader("Calendrier des RDV à venir")
    upcoming = query_df("SELECT * FROM appointments WHERE date >= ? ORDER BY date, heure", (date.today().strftime("%Y-%m-%d"),))
    if not upcoming.empty:
        st.dataframe(upcoming, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun rendez-vous planifié pour les jours à venir.")

# ====================== KANBAN TÂCHES ======================
elif page == "✅ Tâches":
    st.markdown('<h1 class="main-header">✅ Kanban des Tâches</h1>', unsafe_allow_html=True)
    
    with st.expander("➕ Créer une nouvelle tâche"):
        with st.form("add_task_ult"):
            titre = st.text_input("Titre de la tâche *")
            desc = st.text_area("Description")
            due = st.date_input("Date limite", value=date.today() + timedelta(days=2))
            prio = st.selectbox("Priorité", ["Haute", "Moyenne", "Basse"])
            link = st.text_input("Lier à (ex: Client Dupont ou Bien rue X)")
            
            if st.form_submit_button("Créer la tâche"):
                if titre:
                    execute("INSERT INTO tasks (titre, description, due_date, priorite, statut, linked_to, date_creation) VALUES (?,?,?,?,?,?,?)",
                            (titre, desc, due.strftime("%Y-%m-%d"), prio, "À faire", link, datetime.now().strftime("%Y-%m-%d")))
                    st.success("Tâche créée !")
                    st.rerun()
    
    st.divider()
    
    tasks = query_df("SELECT * FROM tasks")
    if not tasks.empty:
        stages = ["À faire", "En cours", "Terminé"]
        kanban_cols = st.columns(3)
        
        for i, stage in enumerate(stages):
            with kanban_cols[i]:
                st.markdown(f"### {stage}")
                stage_tasks = tasks[tasks['statut'] == stage]
                for _, t in stage_tasks.iterrows():
                    with st.container(border=True):
                        st.write(f"**{t['titre']}**")
                        if t['description']:
                            st.caption(t['description'][:80])
                        st.write(f"📅 {t['due_date']} | {t['priorite']}")
                        if st.button("Changer statut", key=f"change_{t['id']}"):
                            new_s = st.selectbox("Nouveau", stages, key=f"ns_{t['id']}")
                            if st.button("Valider", key=f"val_{t['id']}"):
                                execute("UPDATE tasks SET statut=? WHERE id=?", (new_s, t['id']))
                                st.rerun()
    else:
        st.info("Aucune tâche pour le moment.")

# ====================== OUTILS & EXPORT ======================
elif page == "🛠️ Outils & Export":
    st.markdown('<h1 class="main-header">🛠️ Outils Avancés & Export</h1>', unsafe_allow_html=True)
    
    st.subheader("Estimateur Intelligent")
    # ... (same improved estimator)
    
    st.subheader("Exports Rapides")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        if st.button("📥 Exporter toutes les Propriétés (CSV)"):
            p = query_df("SELECT * FROM properties")
            if not p.empty:
                st.download_button("Télécharger", p.to_csv(index=False).encode(), "proprietes.csv")
    with col_exp2:
        if st.button("📥 Exporter Clients (CSV)"):
            c = query_df("SELECT * FROM clients")
            if not c.empty:
                st.download_button("Télécharger", c.to_csv(index=False).encode(), "clients.csv")

# ====================== FOOTER / COLLAB ======================
st.sidebar.markdown("---")
st.sidebar.subheader("🤝 Collaboration d'Équipe")
st.sidebar.markdown("""
**Comment ça marche pour plusieurs personnes ?**

**Option simple (recommandée pour commencer) :**
- Partagez le dossier **`immo_ULTIMATE_data`** via :
  - Google Drive / Dropbox / OneDrive
  - Un NAS ou serveur de l'agence
  - Clé USB / disque dur partagé

**Avantages :**
- Tout le monde voit exactement les mêmes données
- Mises à jour instantanées dès que le fichier est synchronisé
- Pas besoin d'internet permanent (fonctionne en local)

**Limites actuelles :**
- Pas de synchro temps réel (il faut rafraîchir ou attendre la synchro cloud)
- Pas de verrouillage (évitez de modifier la même chose en même temps)
- Pas de rôles avancés (Admin / Agent) pour l'instant

**Pour passer au niveau supérieur (recommandé si > 3 personnes) :**
Je peux te faire une version avec **Supabase** (gratuit) qui permet :
- Accès depuis n'importe quel téléphone/ordinateur
- Synchronisation en temps réel
- Comptes utilisateurs + rôles (Admin / Agent)
- Version web + PWA mobile

Tu veux que je te prépare **dès maintenant** la version cloud avec Supabase ?
""")