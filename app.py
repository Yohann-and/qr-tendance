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
    # Vérification de l'authentification
    if not auth.is_authenticated():
        auth.login()
        return
    
    # Affichage du statut d'authentification
    auth.show_auth_status()
    
    # Initialisation des modules
    modules = init_modules()
    
    st.title("📊 Dashboard Statistiques QR Pointage")
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

def show_dashboard():
    """Affiche le tableau de bord principal"""
    # Sidebar pour les filtres
    with st.sidebar:
        st.header("🔍 Filtres")
        
        # Sélection de la période
        st.subheader("Période")
        date_range = st.selectbox(
            "Période prédéfinie",
            ["Aujourd'hui", "Cette semaine", "Ce mois", "Période personnalisée"]
        )
        
        if date_range == "Aujourd'hui":
            start_date = end_date = date.today()
        elif date_range == "Cette semaine":
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif date_range == "Ce mois":
            today = date.today()
            start_date = date(today.year, today.month, 1)
            end_date = today
        else:  # Période personnalisée
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Du", value=date.today() - timedelta(days=7))
            with col2:
                end_date = st.date_input("Au", value=date.today())
        
        # Sélection du domaine
        domain_filter = st.selectbox(
            "Domaine",
            ["Tous", "Chantre", "Protocole", "Régis"]
        )
        
        # Sélection du type de statut
        status_filter = st.multiselect(
            "Type de statut",
            ["Présent", "Absent", "Retard"],
            default=["Présent", "Absent", "Retard"]
        )
        
        st.markdown("---")
        
        # Actualisation automatique
        auto_refresh = st.checkbox("Actualisation automatique (1 min)", value=True)
        
        if st.button("🔄 Actualiser maintenant"):
            st.cache_data.clear()
            st.rerun()
    
    # Chargement des données
    try:
        with st.spinner("Chargement des données..."):
            df = load_data(start_date, end_date)
        
        if df.empty:
            st.warning("Aucune donnée disponible pour la période sélectionnée.")
            return
        
        # Classification des domaines
        df['domaine'] = df['matricule'].apply(classify_domain)
        
        # Filtrage par domaine
        if domain_filter != "Tous":
            df = df[df['domaine'] == domain_filter]
        
        # Filtrage par statut
        if status_filter:
            df = df[df['statut'].isin(status_filter)]
        
        # Calcul des statistiques
        stats = calculate_statistics(df)
        
        # Affichage des KPI principaux
        st.subheader("📈 Indicateurs Clés de Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Employés",
                stats['total_employees'],
                delta=f"{stats['new_employees_today']} nouveaux aujourd'hui" if stats['new_employees_today'] > 0 else None
            )
        
        with col2:
            presence_rate = (stats['total_present'] / max(stats['total_records'], 1)) * 100
            st.metric(
                "Taux de Présence",
                f"{presence_rate:.1f}%",
                delta=f"{presence_rate - stats['yesterday_presence_rate']:.1f}%" if 'yesterday_presence_rate' in stats else None
            )
        
        with col3:
            st.metric(
                "Présents",
                stats['total_present'],
                delta=stats['present_vs_yesterday'] if 'present_vs_yesterday' in stats else None
            )
        
        with col4:
            st.metric(
                "Retards",
                stats['total_late'],
                delta=stats['late_vs_yesterday'] if 'late_vs_yesterday' in stats else None
            )
        
        st.markdown("---")
        
        # Graphiques principaux
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Répartition par Statut")
            
            # Graphique en camembert
            status_counts = df['statut'].value_counts()
            fig_pie = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Répartition des Statuts",
                color_discrete_map={
                    'Présent': '#28a745',
                    'Absent': '#dc3545',
                    'Retard': '#ffc107'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Statistiques par Domaine")
            
            # Graphique en barres par domaine
            domain_stats = df.groupby(['domaine', 'statut']).size().unstack(fill_value=0)
            fig_bar = px.bar(
                domain_stats,
                title="Statuts par Domaine",
                color_discrete_map={
                    'Présent': '#28a745',
                    'Absent': '#dc3545',
                    'Retard': '#ffc107'
                }
            )
            fig_bar.update_layout(barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Évolution temporelle
        st.subheader("📈 Évolution Temporelle")
        
        if len(df) > 0 and 'date_pointage' in df.columns:
            # Grouper par date et statut
            daily_stats = df.groupby([df['date_pointage'].dt.date, 'statut']).size().unstack(fill_value=0)
            
            fig_line = go.Figure()
            
            for status in daily_stats.columns:
                color_map = {'Présent': '#28a745', 'Absent': '#dc3545', 'Retard': '#ffc107'}
                fig_line.add_trace(go.Scatter(
                    x=daily_stats.index,
                    y=daily_stats[status],
                    mode='lines+markers',
                    name=status,
                    line=dict(color=color_map.get(status, '#007bff'))
                ))
            
            fig_line.update_layout(
                title="Évolution des Statuts dans le Temps",
                xaxis_title="Date",
                yaxis_title="Nombre d'Employés",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_line, use_container_width=True)
        
        # Tableau détaillé par domaine
        st.subheader("📋 Détails par Domaine")
        
        domain_details = []
        for domain in ['Chantre', 'Protocole', 'Régis']:
            domain_data = df[df['domaine'] == domain]
            if not domain_data.empty:
                present = len(domain_data[domain_data['statut'] == 'Présent'])
                absent = len(domain_data[domain_data['statut'] == 'Absent'])
                late = len(domain_data[domain_data['statut'] == 'Retard'])
                total = len(domain_data)
                
                domain_details.append({
                    'Domaine': domain,
                    'Total': total,
                    'Présents': present,
                    'Absents': absent,
                    'Retards': late,
                    'Taux Présence': f"{(present/total*100):.1f}%" if total > 0 else "0%"
                })
        
        if domain_details:
            domain_df = pd.DataFrame(domain_details)
            st.dataframe(domain_df, use_container_width=True)
        
        # Section des rapports
        st.markdown("---")
        st.subheader("📄 Génération de Rapports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Rapport PDF"):
                with st.spinner("Génération du rapport PDF..."):
                    pdf_buffer = generate_pdf_report(df, stats, start_date, end_date)
                    st.download_button(
                        label="Télécharger le rapport PDF",
                        data=pdf_buffer,
                        file_name=f"rapport_pointage_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
        
        with col2:
            if st.button("📈 Export CSV"):
                csv_data = generate_csv_report(df)
                st.download_button(
                    label="Télécharger les données CSV",
                    data=csv_data,
                    file_name=f"donnees_pointage_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        
        with col3:
            st.info(f"Dernière mise à jour: {format_time_display(datetime.now())}")
        
        # Tableau des données récentes
        if st.checkbox("Afficher les données détaillées"):
            st.subheader("📊 Données Récentes")
            
            # Sélection des colonnes à afficher
            display_columns = ['matricule', 'domaine', 'statut', 'date_pointage', 'heure_pointage']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                recent_data = df[available_columns].sort_values('date_pointage', ascending=False).head(100)
                st.dataframe(recent_data, use_container_width=True)
            else:
                st.warning("Structure de données inattendue. Affichage de toutes les colonnes disponibles:")
                st.dataframe(df.head(100), use_container_width=True)
    
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        st.info("Vérifiez que la base de données est accessible et que les tables existent.")
    
    # Actualisation automatique
    if auto_refresh:
        time.sleep(60)
        st.rerun()

def show_chatbot(chatbot):
    """Affiche l'interface du chatbot"""
    st.subheader("🤖 Assistant Intelligent")
    st.markdown("Posez vos questions sur les statistiques de pointage en langage naturel.")
    
    # Historique des conversations
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Questions suggérées
    st.markdown("### Questions suggérées:")
    suggested_questions = chatbot.get_suggested_questions()
    
    col1, col2 = st.columns(2)
    for i, question in enumerate(suggested_questions):
        with col1 if i % 2 == 0 else col2:
            if st.button(f"💬 {question}", key=f"suggested_{i}"):
                st.session_state.chat_history.append({"type": "user", "message": question})
                response = chatbot.process_question(question)
                st.session_state.chat_history.append({"type": "bot", "message": response})
                st.rerun()
    
    # Zone de chat
    st.markdown("### Conversation")
    
    # Affichage de l'historique
    for chat in st.session_state.chat_history:
        if chat["type"] == "user":
            st.markdown(f"**👤 Vous:** {chat['message']}")
        else:
            st.markdown(f"**🤖 Assistant:** {chat['message']}")
    
    # Nouvelle question
    with st.form("chat_form"):
        user_question = st.text_input("Posez votre question:", placeholder="Ex: Combien de retards chez les chantres aujourd'hui?")
        submitted = st.form_submit_button("Envoyer")
        
        if submitted and user_question:
            # Ajout de la question à l'historique
            st.session_state.chat_history.append({"type": "user", "message": user_question})
            
            # Génération de la réponse
            response = chatbot.process_question(user_question)
            st.session_state.chat_history.append({"type": "bot", "message": response})
            
            st.rerun()
    
    # Bouton pour effacer l'historique
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.chat_history = []
        st.rerun()

def show_predictions(prediction_module):
    """Affiche l'interface des prédictions"""
    st.subheader("🔮 Prédictions Comportementales")
    st.markdown("Analysez les tendances et prédisez le comportement futur des employés.")
    
    # Sélection d'un employé
    try:
        # Récupération des employés actifs
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        db = init_database()
        df = db.get_attendance_data(start_date, end_date)
        
        if not df.empty:
            df['domaine'] = df['matricule'].apply(classify_domain)
            employees = sorted(df['matricule'].unique())
            
            selected_employee = st.selectbox("Choisir un employé:", employees)
            
            if selected_employee:
                # Analyse des risques
                st.markdown("### 📊 Analyse des Risques")
                risk_analysis = prediction_module.get_risk_analysis(selected_employee)
                
                if risk_analysis:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Taux de Présence", f"{risk_analysis['presence_rate']:.1%}")
                    
                    with col2:
                        st.metric("Taux d'Absence", f"{risk_analysis['absence_rate']:.1%}")
                    
                    with col3:
                        st.metric("Taux de Retard", f"{risk_analysis['late_rate']:.1%}")
                    
                    # Niveau de risque
                    risk_level = risk_analysis['risk_level']
                    if risk_level == "Élevé":
                        st.error(f"🚨 Risque {risk_level}")
                    elif risk_level == "Modéré":
                        st.warning(f"⚠️ Risque {risk_level}")
                    else:
                        st.success(f"✅ Risque {risk_level}")
                    
                    # Facteurs de risque
                    if risk_analysis['risk_factors']:
                        st.markdown("#### Facteurs de risque identifiés:")
                        for factor in risk_analysis['risk_factors']:
                            st.markdown(f"• {factor}")
                
                # Prédictions
                st.markdown("### 📈 Prédictions (7 prochains jours)")
                predictions = prediction_module.predict_employee_behavior(selected_employee, 7)
                
                if predictions:
                    # Graphique des prédictions
                    chart = prediction_module.create_prediction_charts(predictions)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # Tableau des prédictions
                    pred_data = []
                    for pred in predictions:
                        pred_data.append({
                            'Date': pred['date'].strftime('%d/%m/%Y'),
                            'Prédiction': pred['prediction'],
                            'Probabilité': f"{pred['probability']:.1%}"
                        })
                    
                    pred_df = pd.DataFrame(pred_data)
                    st.dataframe(pred_df, use_container_width=True)
                else:
                    st.info("Pas assez de données pour faire des prédictions fiables.")
        else:
            st.info("Aucune donnée disponible pour les prédictions.")
    
    except Exception as e:
        st.error(f"Erreur lors du chargement des prédictions: {str(e)}")

def show_alerts(alert_system):
    """Affiche l'interface des alertes"""
    st.subheader("🚨 Système d'Alertes")
    st.markdown("Surveillez les employés avec des absences ou retards excessifs.")
    
    # Configuration des alertes
    col1, col2 = st.columns(2)
    
    with col1:
        days_to_check = st.slider("Période d'analyse (jours)", 7, 60, 30)
    
    with col2:
        auto_check = st.checkbox("Vérification automatique", value=True)
    
    # Récupération des alertes
    alerts = alert_system.get_all_alerts(days_to_check)
    
    # Affichage du tableau de bord des alertes
    alert_system.create_alerts_dashboard(alerts)
    
    # Configuration des notifications SMS
    st.markdown("### 📱 Configuration des Notifications")
    
    with st.expander("Paramètres SMS"):
        phone_numbers = st.text_area(
            "Numéros de téléphone (un par ligne):",
            placeholder="+33123456789\n+33987654321",
            help="Saisissez les numéros au format international"
        )
        
        if st.button("📤 Envoyer les alertes par SMS"):
            if phone_numbers and alerts:
                phone_list = [phone.strip() for phone in phone_numbers.split('\n') if phone.strip()]
                alert_system.send_alert_notifications(alerts, phone_list)
            else:
                st.warning("Veuillez saisir au moins un numéro de téléphone et avoir des alertes disponibles.")
    
    # Résumé des alertes
    if alerts:
        st.markdown("### 📋 Résumé des Alertes")
        summary = alert_system.get_alert_summary(alerts)
        st.markdown(summary)

def show_settings():
    """Affiche l'interface des paramètres"""
    st.subheader("⚙️ Paramètres Système")
    
    # Gestion des utilisateurs
    auth.show_user_management()
    
    # Configuration de la base de données
    with st.expander("🗄️ Configuration Base de Données"):
        st.info("Configuration actuelle de la base de données:")
        db = init_database()
        success, message = db.test_connection()
        
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        
        # Structure des tables
        if st.button("📊 Afficher la structure des tables"):
            table_structure = db.get_table_structure()
            if not table_structure.empty:
                st.dataframe(table_structure)
            else:
                st.info("Aucune table de pointage trouvée.")
    
    # Configuration des alertes
    with st.expander("🚨 Configuration des Alertes"):
        st.markdown("**Seuils d'alertes:**")
        absence_threshold = st.slider("Seuil d'alertes absence", 1, 10, 2)
        lateness_threshold = st.slider("Seuil d'alertes retard", 1, 10, 3)
        
        st.markdown("**Configuration Twilio:**")
        twilio_configured = all([
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN'),
            os.getenv('TWILIO_PHONE_NUMBER')
        ])
        
        if twilio_configured:
            st.success("✅ Twilio configuré")
        else:
            st.warning("⚠️ Twilio non configuré - Les notifications SMS ne fonctionneront pas")
    
    # Statistiques système
    with st.expander("📈 Statistiques Système"):
        st.markdown("**Utilisation de l'application:**")
        st.info("Statistiques d'utilisation à venir...")



if __name__ == "__main__":
    main()
