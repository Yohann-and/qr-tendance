import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import time
import os
from database import DatabaseManager
from utils import classify_domain, calculate_statistics, format_time_display
from reports import generate_pdf_report, generate_csv_report
from auth import AuthManager
from chatbot import AttendanceChatbot
from prediction import AttendancePrediction
from alerts import AlertSystem


# Configuration de la page
st.set_page_config(
    page_title="Dashboard Statistiques QR Pointage",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de l'authentification
auth = AuthManager()

# Initialisation des modules
@st.cache_resource
def init_modules():
    return {
        'chatbot': AttendanceChatbot(),
        'prediction': AttendancePrediction(),
        'alerts': AlertSystem()
    }

# Initialisation de la base de données
@st.cache_resource
def init_database():
    return DatabaseManager()

# Cache pour les données avec TTL de 1 minute
@st.cache_data(ttl=60)
def load_data(start_date, end_date):
    db = init_database()
    return db.get_attendance_data(start_date, end_date)

def main():
    # Test connexion à la base de données
    db = init_database()
    success, message = db.test_connection()
    st.write("Test de connexion à la base :", message)
    
    # Vérification de l'authentification
    if not auth.is_authenticated():
        auth.login()
        return
    
    # Affichage du statut d'authentification
    auth.show_auth_status()
    
    # Initialisation des modules
    modules = init_modules()
    
    # Titre avec bouton QR
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("📊 Dashboard Statistiques QR Pointage")
    
    with col2:
        st.markdown("### 🔗 Accès rapide")
        if st.button("📱 Application QR", type="primary", use_container_width=True):
            st.markdown("""
            <script>
            window.open('https://worker-tracker-2-0.onrender.com/attendance_log', '_blank');
            </script>
            """, unsafe_allow_html=True)
        st.markdown("[🔗 Ouvrir l'app QR](https://worker-tracker-2-0.onrender.com/attendance_log)", 
                   help="Cliquez pour accéder à l'application de scan QR")
    
    st.markdown("---")
    
    # Navigation principale
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Tableau de Bord", "🤖 Chatbot", "🔮 Prédictions", "🚨 Alertes", "⚙️ Paramètres"])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_chatbot(modules['chatbot'])
    
    with tab3:
        show_predictions(modules['prediction'])
    
    with tab4:
        show_alerts(modules['alerts'])
    
    with tab5:
        if st.session_state.get('user_role') == 'admin':
            show_settings()
        else:
            st.error("Accès refusé. Droits administrateur requis.")

# (Les autres fonctions show_dashboard, show_chatbot, etc restent inchangées)

if __name__ == "__main__":
    main()
