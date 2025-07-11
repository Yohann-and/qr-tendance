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

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Statistiques QR Pointage",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.title("📊 Dashboard Statistiques QR Pointage")
    st.markdown("---")
    
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

if __name__ == "__main__":
    main()
