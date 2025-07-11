import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import DatabaseManager
from utils import classify_domain
from twilio.rest import Client
import os

class AlertSystem:
    def __init__(self):
        self.db = DatabaseManager()
        self.twilio_client = None
        self.setup_twilio()
        
    def setup_twilio(self):
        """Configure Twilio client"""
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                return True
        except Exception as e:
            st.error(f"Erreur configuration Twilio: {str(e)}")
        return False
    
    def send_sms_alert(self, to_phone, message):
        """Envoie un SMS d'alerte"""
        if not self.twilio_client:
            st.warning("Twilio non configuré. Impossible d'envoyer des SMS.")
            return False
        
        try:
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            if not twilio_phone:
                st.error("Numéro Twilio non configuré.")
                return False
            
            message = self.twilio_client.messages.create(
                body=message,
                from_=twilio_phone,
                to=to_phone
            )
            
            st.success(f"SMS envoyé avec succès (SID: {message.sid})")
            return True
            
        except Exception as e:
            st.error(f"Erreur envoi SMS: {str(e)}")
            return False
    
    def check_absence_alerts(self, days_to_check=30):
        """Vérifie les alertes d'absence (plus de 2 absences)"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_to_check)
            
            df = self.db.get_attendance_data(start_date, end_date)
            
            if df.empty:
                return []
            
            # Ajout de la classification des domaines
            df['domaine'] = df['matricule'].apply(classify_domain)
            
            # Comptage des absences par employé
            absence_counts = df[df['statut'] == 'Absent'].groupby('matricule').size()
            
            # Employés avec plus de 2 absences
            problematic_employees = absence_counts[absence_counts > 2]
            
            alerts = []
            for matricule, count in problematic_employees.items():
                # Informations sur l'employé
                emp_data = df[df['matricule'] == matricule]
                domaine = emp_data['domaine'].iloc[0] if not emp_data.empty else 'Inconnu'
                
                # Dernières absences
                recent_absences = emp_data[emp_data['statut'] == 'Absent'].tail(3)
                last_absence_date = recent_absences['date_pointage'].max() if not recent_absences.empty else None
                
                alert = {
                    'type': 'absence',
                    'matricule': matricule,
                    'domaine': domaine,
                    'count': count,
                    'period': f"{days_to_check} jours",
                    'last_occurrence': last_absence_date,
                    'message': f"🚨 ALERTE ABSENCE: L'employé {matricule} ({domaine}) a {count} absences dans les {days_to_check} derniers jours.",
                    'severity': 'high' if count > 5 else 'medium'
                }
                
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            st.error(f"Erreur vérification alertes absences: {str(e)}")
            return []
    
    def check_lateness_alerts(self, days_to_check=30):
        """Vérifie les alertes de retard (3 retards ou plus)"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_to_check)
            
            df = self.db.get_attendance_data(start_date, end_date)
            
            if df.empty:
                return []
            
            # Ajout de la classification des domaines
            df['domaine'] = df['matricule'].apply(classify_domain)
            
            # Comptage des retards par employé
            late_counts = df[df['statut'] == 'Retard'].groupby('matricule').size()
            
            # Employés avec 3 retards ou plus
            problematic_employees = late_counts[late_counts >= 3]
            
            alerts = []
            for matricule, count in problematic_employees.items():
                # Informations sur l'employé
                emp_data = df[df['matricule'] == matricule]
                domaine = emp_data['domaine'].iloc[0] if not emp_data.empty else 'Inconnu'
                
                # Derniers retards
                recent_lates = emp_data[emp_data['statut'] == 'Retard'].tail(3)
                last_late_date = recent_lates['date_pointage'].max() if not recent_lates.empty else None
                
                alert = {
                    'type': 'retard',
                    'matricule': matricule,
                    'domaine': domaine,
                    'count': count,
                    'period': f"{days_to_check} jours",
                    'last_occurrence': last_late_date,
                    'message': f"⚠️ ALERTE RETARD: L'employé {matricule} ({domaine}) a {count} retards dans les {days_to_check} derniers jours.",
                    'severity': 'high' if count > 5 else 'medium'
                }
                
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            st.error(f"Erreur vérification alertes retards: {str(e)}")
            return []
    
    def get_all_alerts(self, days_to_check=30):
        """Récupère toutes les alertes"""
        absence_alerts = self.check_absence_alerts(days_to_check)
        lateness_alerts = self.check_lateness_alerts(days_to_check)
        
        all_alerts = absence_alerts + lateness_alerts
        
        # Tri par sévérité puis par nombre d'occurrences
        all_alerts.sort(key=lambda x: (x['severity'] == 'high', x['count']), reverse=True)
        
        return all_alerts
    
    def send_alert_notifications(self, alerts, phone_numbers):
        """Envoie des notifications pour les alertes"""
        if not alerts or not phone_numbers:
            return
        
        # Regroupement des alertes par type
        absence_alerts = [a for a in alerts if a['type'] == 'absence']
        lateness_alerts = [a for a in alerts if a['type'] == 'retard']
        
        # Message de synthèse
        summary_message = f"📊 RAPPORT D'ALERTES QR POINTAGE\n\n"
        
        if absence_alerts:
            summary_message += f"🚨 ABSENCES: {len(absence_alerts)} employé(s)\n"
            for alert in absence_alerts[:3]:  # Top 3
                summary_message += f"• {alert['matricule']} ({alert['domaine']}): {alert['count']} absences\n"
        
        if lateness_alerts:
            summary_message += f"\n⚠️ RETARDS: {len(lateness_alerts)} employé(s)\n"
            for alert in lateness_alerts[:3]:  # Top 3
                summary_message += f"• {alert['matricule']} ({alert['domaine']}): {alert['count']} retards\n"
        
        summary_message += f"\n📅 Période: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Envoi des SMS
        for phone in phone_numbers:
            self.send_sms_alert(phone, summary_message)
    
    def create_alerts_dashboard(self, alerts):
        """Crée un tableau de bord des alertes"""
        if not alerts:
            st.info("Aucune alerte détectée.")
            return
        
        # Métriques d'alertes
        col1, col2, col3 = st.columns(3)
        
        absence_alerts = [a for a in alerts if a['type'] == 'absence']
        lateness_alerts = [a for a in alerts if a['type'] == 'retard']
        high_severity = [a for a in alerts if a['severity'] == 'high']
        
        with col1:
            st.metric("Alertes Absences", len(absence_alerts))
        
        with col2:
            st.metric("Alertes Retards", len(lateness_alerts))
        
        with col3:
            st.metric("Alertes Critiques", len(high_severity))
        
        # Tableau des alertes
        st.subheader("📋 Détail des Alertes")
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'Type': alert['type'].title(),
                'Matricule': alert['matricule'],
                'Domaine': alert['domaine'],
                'Occurrences': alert['count'],
                'Période': alert['period'],
                'Dernière Date': alert['last_occurrence'],
                'Sévérité': alert['severity'].title()
            })
        
        alerts_df = pd.DataFrame(alerts_data)
        
        # Coloration par sévérité
        def highlight_severity(row):
            if row['Sévérité'] == 'High':
                return ['background-color: #ffebee'] * len(row)
            elif row['Sévérité'] == 'Medium':
                return ['background-color: #fff3e0'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = alerts_df.style.apply(highlight_severity, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Graphique des alertes par domaine
        if alerts_data:
            st.subheader("📊 Alertes par Domaine")
            
            domain_counts = alerts_df.groupby(['Domaine', 'Type']).size().unstack(fill_value=0)
            
            if not domain_counts.empty:
                st.bar_chart(domain_counts)
    
    def get_alert_summary(self, alerts):
        """Génère un résumé des alertes"""
        if not alerts:
            return "Aucune alerte détectée."
        
        absence_count = len([a for a in alerts if a['type'] == 'absence'])
        lateness_count = len([a for a in alerts if a['type'] == 'retard'])
        high_severity_count = len([a for a in alerts if a['severity'] == 'high'])
        
        summary = f"""
        ## Résumé des Alertes
        
        **Total des alertes**: {len(alerts)}
        
        **Par type**:
        - Absences excessives: {absence_count}
        - Retards fréquents: {lateness_count}
        
        **Sévérité**:
        - Alertes critiques: {high_severity_count}
        
        **Recommandations**:
        - Contacter immédiatement les employés avec alertes critiques
        - Planifier des entretiens individuels pour comprendre les causes
        - Mettre en place des mesures correctives adaptées
        """
        
        return summary