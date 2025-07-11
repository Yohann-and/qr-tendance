import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from database import DatabaseManager
from utils import classify_domain, calculate_statistics, generate_domain_summary

class AttendanceChatbot:
    def __init__(self):
        self.db = DatabaseManager()
        self.patterns = {
            'retard': r'(retard|late|délai|ponctualité)',
            'absence': r'(absent|absence|manque|manquant)',
            'presence': r'(présent|presence|présence|assiduité)',
            'domaine': r'(chantre|protocole|régis|domaine)',
            'statistique': r'(statistique|stat|nombre|combien|taux)',
            'aujourd_hui': r'(aujourd\'hui|today|ce jour)',
            'semaine': r'(semaine|week|cette semaine)',
            'mois': r'(mois|month|ce mois)',
            'employe': r'(employé|ouvrier|agent|personne|matricule|[CPR]\d+)'
        }
        
        self.responses = {
            'greeting': [
                "Bonjour! Je suis votre assistant de statistiques de pointage. Comment puis-je vous aider?",
                "Salut! Que souhaitez-vous savoir sur les statistiques de présence?",
                "Hello! Je peux vous renseigner sur les absences, retards et présences. Que désirez-vous?"
            ],
            'unknown': [
                "Je ne comprends pas votre question. Pouvez-vous reformuler?",
                "Désolé, je n'ai pas saisi. Essayez de demander les statistiques d'un domaine ou d'une période.",
                "Je peux vous aider avec les statistiques de présence. Reformulez votre question s'il vous plaît."
            ]
        }
    
    def process_question(self, question):
        """Traite une question et retourne une réponse appropriée"""
        question_lower = question.lower()
        
        # Détection des salutations
        if any(word in question_lower for word in ['bonjour', 'salut', 'hello', 'bonsoir']):
            return self.responses['greeting'][0]
        
        # Détection du domaine
        domain = self._extract_domain(question_lower)
        
        # Détection de la période
        period = self._extract_period(question_lower)
        
        # Détection du type de statistique
        stat_type = self._extract_stat_type(question_lower)
        
        # Détection d'un matricule spécifique
        matricule = self._extract_matricule(question)
        
        # Génération de la réponse
        return self._generate_response(domain, period, stat_type, matricule, question_lower)
    
    def _extract_domain(self, question):
        """Extrait le domaine de la question"""
        if 'chantre' in question or 'chantres' in question:
            return 'Chantre'
        elif 'protocole' in question:
            return 'Protocole'
        elif 'régis' in question or 'regis' in question:
            return 'Régis'
        return None
    
    def _extract_period(self, question):
        """Extrait la période de la question"""
        if re.search(self.patterns['aujourd_hui'], question):
            return 'today'
        elif re.search(self.patterns['semaine'], question):
            return 'week'
        elif re.search(self.patterns['mois'], question):
            return 'month'
        return 'today'  # Par défaut
    
    def _extract_stat_type(self, question):
        """Extrait le type de statistique demandée"""
        if re.search(self.patterns['retard'], question):
            return 'retard'
        elif re.search(self.patterns['absence'], question):
            return 'absence'
        elif re.search(self.patterns['presence'], question):
            return 'presence'
        return 'general'
    
    def _extract_matricule(self, question):
        """Extrait un matricule spécifique de la question"""
        matricule_pattern = r'[CPR]\d+'
        match = re.search(matricule_pattern, question.upper())
        return match.group() if match else None
    
    def _generate_response(self, domain, period, stat_type, matricule, question):
        """Génère une réponse basée sur les paramètres extraits"""
        try:
            # Détermination des dates
            if period == 'today':
                start_date = end_date = datetime.now().date()
                period_text = "aujourd'hui"
            elif period == 'week':
                today = datetime.now().date()
                start_date = today - timedelta(days=today.weekday())
                end_date = today
                period_text = "cette semaine"
            elif period == 'month':
                today = datetime.now().date()
                start_date = datetime(today.year, today.month, 1).date()
                end_date = today
                period_text = "ce mois"
            else:
                start_date = end_date = datetime.now().date()
                period_text = "aujourd'hui"
            
            # Récupération des données
            df = self.db.get_attendance_data(start_date, end_date)
            
            if df.empty:
                return f"Aucune donnée disponible pour {period_text}."
            
            # Ajout de la classification des domaines
            df['domaine'] = df['matricule'].apply(classify_domain)
            
            # Filtrage par domaine si spécifié
            if domain:
                df = df[df['domaine'] == domain]
                if df.empty:
                    return f"Aucune donnée pour le domaine {domain} {period_text}."
            
            # Filtrage par matricule si spécifié
            if matricule:
                df = df[df['matricule'] == matricule]
                if df.empty:
                    return f"Aucune donnée pour l'employé {matricule} {period_text}."
            
            # Génération de la réponse selon le type
            if stat_type == 'retard':
                return self._generate_late_response(df, domain, period_text, matricule)
            elif stat_type == 'absence':
                return self._generate_absence_response(df, domain, period_text, matricule)
            elif stat_type == 'presence':
                return self._generate_presence_response(df, domain, period_text, matricule)
            else:
                return self._generate_general_response(df, domain, period_text, matricule)
                
        except Exception as e:
            return f"Erreur lors de la récupération des données: {str(e)}"
    
    def _generate_late_response(self, df, domain, period_text, matricule):
        """Génère une réponse pour les retards"""
        late_count = len(df[df['statut'] == 'Retard'])
        
        if matricule:
            return f"L'employé {matricule} a {late_count} retard(s) {period_text}."
        elif domain:
            return f"Le domaine {domain} a {late_count} retard(s) {period_text}."
        else:
            return f"Il y a {late_count} retard(s) au total {period_text}."
    
    def _generate_absence_response(self, df, domain, period_text, matricule):
        """Génère une réponse pour les absences"""
        absent_count = len(df[df['statut'] == 'Absent'])
        
        if matricule:
            return f"L'employé {matricule} a {absent_count} absence(s) {period_text}."
        elif domain:
            return f"Le domaine {domain} a {absent_count} absence(s) {period_text}."
        else:
            return f"Il y a {absent_count} absence(s) au total {period_text}."
    
    def _generate_presence_response(self, df, domain, period_text, matricule):
        """Génère une réponse pour les présences"""
        present_count = len(df[df['statut'] == 'Présent'])
        total_count = len(df)
        presence_rate = (present_count / total_count * 100) if total_count > 0 else 0
        
        if matricule:
            return f"L'employé {matricule} a {present_count} présence(s) {period_text}."
        elif domain:
            return f"Le domaine {domain} a {present_count} présence(s) {period_text} (taux: {presence_rate:.1f}%)."
        else:
            return f"Il y a {present_count} présence(s) au total {period_text} (taux: {presence_rate:.1f}%)."
    
    def _generate_general_response(self, df, domain, period_text, matricule):
        """Génère une réponse générale"""
        stats = calculate_statistics(df)
        
        if matricule:
            emp_data = df[df['matricule'] == matricule]
            if not emp_data.empty:
                status = emp_data['statut'].iloc[0]
                return f"L'employé {matricule} est {status.lower()} {period_text}."
            else:
                return f"Aucune donnée trouvée pour l'employé {matricule} {period_text}."
        elif domain:
            domain_data = df[df['domaine'] == domain]
            present = len(domain_data[domain_data['statut'] == 'Présent'])
            absent = len(domain_data[domain_data['statut'] == 'Absent'])
            late = len(domain_data[domain_data['statut'] == 'Retard'])
            
            return f"Domaine {domain} {period_text}: {present} présent(s), {absent} absent(s), {late} retard(s)."
        else:
            return f"Statistiques {period_text}: {stats['total_present']} présent(s), {stats['total_absent']} absent(s), {stats['total_late']} retard(s)."
    
    def get_suggested_questions(self):
        """Retourne des questions suggérées"""
        return [
            "Combien de retards chez les chantres aujourd'hui?",
            "Quel est le taux de présence du domaine Protocole cette semaine?",
            "Combien d'absences au total ce mois?",
            "Statistiques générales aujourd'hui",
            "Quel employé a le plus de retards?",
            "Taux de présence par domaine cette semaine"
        ]