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
            'retard': r'(retard|late|délai|ponctualité|en retard|tardif)',
            'absence': r'(absent|absence|manque|manquant|manqué|pas venu)',
            'presence': r'(présent|presence|présence|assiduité|pointé|venu|arrivé)',
            'domaine': r'(chantre|protocole|régis|domaine|département|service)',
            'statistique': r'(statistique|stat|nombre|combien|taux|pourcentage|total)',
            'aujourd_hui': r'(aujourd\'hui|today|ce jour|maintenant)',
            'semaine': r'(semaine|week|cette semaine|7 jours)',
            'mois': r'(mois|month|ce mois|30 jours)',
            'hier': r'(hier|yesterday|la veille)',
            'employe': r'(employé|ouvrier|agent|personne|matricule|[CPR]\d+)',
            'meilleur': r'(meilleur|best|top|plus|maximum|max)',
            'pire': r'(pire|worst|moins|minimum|min|problème)',
            'comparaison': r'(comparer|versus|vs|différence|entre)',
            'tendance': r'(tendance|évolution|progression|amélioration|détérioration)',
            'alerte': r'(alerte|problème|attention|surveillance|critique)',
            'rapport': r'(rapport|résumé|bilan|synthèse)',
            'prédiction': r'(prédire|prédiction|futur|anticiper|prévoir)',
            'horaire': r'(horaire|heure|temps|timing|schedule)',
            'performance': r'(performance|rendement|efficacité|productivité)'
        }
        
        self.responses = {
            'greeting': [
                "Bonjour! Je suis votre assistant intelligent de statistiques de pointage. Je peux vous aider avec:",
                "Salut! Assistant IA à votre service pour analyser vos données de présence. Que souhaitez-vous savoir?",
                "Hello! Je peux vous renseigner sur les absences, retards, présences, alertes et prédictions. Que désirez-vous?"
            ],
            'unknown': [
                "Je ne comprends pas votre question. Essayez de demander par exemple: 'Combien de retards chez les chantres?'",
                "Désolé, reformulez votre question. Je peux vous aider avec les statistiques, comparaisons, tendances et alertes.",
                "Je peux analyser les présences, absences, retards par domaine ou employé. Reformulez votre question s'il vous plaît."
            ],
            'help': [
                "Voici ce que je peux faire pour vous:",
                "• Statistiques par domaine ou employé",
                "• Comparaisons entre périodes",
                "• Identification des employés problématiques",
                "• Tendances et évolutions",
                "• Alertes et prédictions",
                "• Analyses de performance"
            ]
        }
    
    def process_question(self, question):
        """Traite une question et retourne une réponse appropriée"""
        question_lower = question.lower()
        
        # Détection des salutations
        if any(word in question_lower for word in ['bonjour', 'salut', 'hello', 'bonsoir']):
            return self.responses['greeting'][0]
        
        # Détection de demande d'aide
        if any(word in question_lower for word in ['aide', 'help', 'comment', 'que peux-tu', 'capacité']):
            return "\n".join(self.responses['help'])
        
        # Détection de questions spéciales
        if re.search(self.patterns['alerte'], question_lower):
            return self._handle_alert_question(question_lower)
        
        if re.search(self.patterns['prédiction'], question_lower):
            return self._handle_prediction_question(question_lower)
        
        if re.search(self.patterns['comparaison'], question_lower):
            return self._handle_comparison_question(question_lower)
        
        if re.search(self.patterns['tendance'], question_lower):
            return self._handle_trend_question(question_lower)
        
        if re.search(self.patterns['performance'], question_lower):
            return self._handle_performance_question(question_lower)
        
        if re.search(self.patterns['meilleur'], question_lower) or re.search(self.patterns['pire'], question_lower):
            return self._handle_ranking_question(question_lower)
        
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
        elif re.search(self.patterns['hier'], question):
            return 'yesterday'
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
            elif period == 'yesterday':
                start_date = end_date = datetime.now().date() - timedelta(days=1)
                period_text = "hier"
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
    
    def _handle_alert_question(self, question):
        """Gère les questions sur les alertes"""
        try:
            from alerts import AlertSystem
            alert_system = AlertSystem()
            alerts = alert_system.get_all_alerts(30)
            
            if not alerts:
                return "✅ Aucune alerte détectée actuellement. Tous les employés respectent les seuils de présence."
            
            absence_alerts = [a for a in alerts if a['type'] == 'absence']
            late_alerts = [a for a in alerts if a['type'] == 'retard']
            
            response = "🚨 **Alertes Actives:**\n\n"
            
            if absence_alerts:
                response += f"**Absences Excessives ({len(absence_alerts)} employés):**\n"
                for alert in absence_alerts[:3]:
                    response += f"• {alert['matricule']} ({alert['domaine']}): {alert['count']} absences\n"
                if len(absence_alerts) > 3:
                    response += f"• ... et {len(absence_alerts) - 3} autres employés\n"
                response += "\n"
            
            if late_alerts:
                response += f"**Retards Fréquents ({len(late_alerts)} employés):**\n"
                for alert in late_alerts[:3]:
                    response += f"• {alert['matricule']} ({alert['domaine']}): {alert['count']} retards\n"
                if len(late_alerts) > 3:
                    response += f"• ... et {len(late_alerts) - 3} autres employés\n"
            
            return response
            
        except Exception as e:
            return "❌ Impossible d'accéder aux alertes actuellement. Vérifiez la configuration du système d'alertes."
    
    def _handle_prediction_question(self, question):
        """Gère les questions sur les prédictions"""
        try:
            from prediction import AttendancePrediction
            prediction_system = AttendancePrediction()
            
            # Récupération des données récentes
            df = self.db.get_attendance_data(
                (datetime.now() - timedelta(days=30)).date(),
                datetime.now().date()
            )
            
            if df.empty:
                return "❌ Pas assez de données pour faire des prédictions."
            
            # Analyse des employés à risque
            employees_sample = df['matricule'].unique()[:5]
            risk_employees = []
            
            for emp in employees_sample:
                risk_analysis = prediction_system.get_risk_analysis(emp)
                if risk_analysis and risk_analysis.get('risk_level') in ['Élevé', 'Modéré']:
                    risk_employees.append(risk_analysis)
            
            if risk_employees:
                response = "🔮 **Prédictions Comportementales:**\n\n"
                response += "**Employés à Surveiller:**\n"
                for risk in risk_employees:
                    response += f"• {risk['matricule']} ({risk['domaine']}): Risque {risk['risk_level']}\n"
                    if risk['risk_factors']:
                        response += f"  Facteurs: {', '.join(risk['risk_factors'][:2])}\n"
                return response
            else:
                return "✅ Aucun employé à risque élevé détecté selon les prédictions actuelles."
                
        except Exception as e:
            return "❌ Impossible d'accéder aux prédictions actuellement. Vérifiez la configuration du système de prédiction."
    
    def _handle_comparison_question(self, question):
        """Gère les questions de comparaison"""
        try:
            # Données de cette semaine
            this_week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
            this_week_end = datetime.now().date()
            
            # Données de la semaine dernière
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = this_week_start - timedelta(days=1)
            
            df_this_week = self.db.get_attendance_data(this_week_start, this_week_end)
            df_last_week = self.db.get_attendance_data(last_week_start, last_week_end)
            
            if df_this_week.empty or df_last_week.empty:
                return "❌ Pas assez de données pour effectuer une comparaison."
            
            # Calcul des statistiques
            this_week_present = len(df_this_week[df_this_week['statut'] == 'Présent'])
            last_week_present = len(df_last_week[df_last_week['statut'] == 'Présent'])
            
            this_week_rate = (this_week_present / len(df_this_week)) * 100 if len(df_this_week) > 0 else 0
            last_week_rate = (last_week_present / len(df_last_week)) * 100 if len(df_last_week) > 0 else 0
            
            difference = this_week_rate - last_week_rate
            
            response = "📊 **Comparaison Cette Semaine vs Semaine Dernière:**\n\n"
            response += f"**Cette semaine:** {this_week_present} présents ({this_week_rate:.1f}%)\n"
            response += f"**Semaine dernière:** {last_week_present} présents ({last_week_rate:.1f}%)\n\n"
            
            if difference > 0:
                response += f"📈 **Amélioration:** +{difference:.1f}% de présence"
            elif difference < 0:
                response += f"📉 **Baisse:** {difference:.1f}% de présence"
            else:
                response += "➡️ **Stable:** Pas de changement significatif"
            
            return response
            
        except Exception as e:
            return "❌ Impossible d'effectuer la comparaison actuellement."
    
    def _handle_trend_question(self, question):
        """Gère les questions sur les tendances"""
        try:
            df = self.db.get_attendance_data(
                (datetime.now() - timedelta(days=30)).date(),
                datetime.now().date()
            )
            
            if df.empty:
                return "❌ Pas assez de données pour analyser les tendances."
            
            # Calcul des tendances par semaine
            df['date_pointage'] = pd.to_datetime(df['date_pointage'])
            df['semaine'] = df['date_pointage'].dt.isocalendar().week
            
            weekly_stats = df.groupby('semaine').agg({
                'statut': lambda x: (x == 'Présent').sum() / len(x) * 100
            }).reset_index()
            
            if len(weekly_stats) < 2:
                return "❌ Pas assez de données pour identifier une tendance."
            
            trend = weekly_stats['statut'].iloc[-1] - weekly_stats['statut'].iloc[0]
            
            response = "📈 **Analyse des Tendances (30 derniers jours):**\n\n"
            
            if trend > 5:
                response += "🟢 **Tendance Positive:** Amélioration significative de la présence\n"
                response += f"Évolution: +{trend:.1f}% par rapport au début de la période"
            elif trend < -5:
                response += "🔴 **Tendance Négative:** Dégradation de la présence\n"
                response += f"Évolution: {trend:.1f}% par rapport au début de la période"
            else:
                response += "🟡 **Tendance Stable:** Présence relativement constante\n"
                response += f"Variation: {trend:.1f}%"
            
            return response
            
        except Exception as e:
            return "❌ Impossible d'analyser les tendances actuellement."
    
    def _handle_performance_question(self, question):
        """Gère les questions sur les performances"""
        try:
            df = self.db.get_attendance_data(
                (datetime.now() - timedelta(days=30)).date(),
                datetime.now().date()
            )
            
            if df.empty:
                return "❌ Pas de données disponibles pour l'analyse de performance."
            
            df['domaine'] = df['matricule'].apply(classify_domain)
            domain_stats = generate_domain_summary(df)
            
            response = "💪 **Analyse de Performance par Domaine:**\n\n"
            
            sorted_domains = sorted(domain_stats.items(), 
                                  key=lambda x: x[1]['presence_rate'], reverse=True)
            
            for i, (domain, stats) in enumerate(sorted_domains, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
                response += f"{emoji} **{domain}:** {stats['presence_rate']:.1f}% de présence\n"
                response += f"   Present: {stats['present']}, Absent: {stats['absent']}, Retard: {stats['late']}\n\n"
            
            # Recommandations
            worst_domain = sorted_domains[-1][0]
            best_domain = sorted_domains[0][0]
            
            response += "💡 **Recommandations:**\n"
            response += f"• Féliciter le domaine {best_domain} pour son excellente assiduité\n"
            response += f"• Accompagner le domaine {worst_domain} pour améliorer sa présence\n"
            
            return response
            
        except Exception as e:
            return "❌ Impossible d'analyser les performances actuellement."
    
    def _handle_ranking_question(self, question):
        """Gère les questions de classement (meilleur/pire)"""
        try:
            df = self.db.get_attendance_data(
                (datetime.now() - timedelta(days=30)).date(),
                datetime.now().date()
            )
            
            if df.empty:
                return "❌ Pas de données disponibles pour le classement."
            
            # Analyse par employé
            employee_stats = df.groupby('matricule').agg({
                'statut': lambda x: {
                    'present': (x == 'Présent').sum(),
                    'absent': (x == 'Absent').sum(),
                    'late': (x == 'Retard').sum(),
                    'total': len(x)
                }
            }).reset_index()
            
            # Calcul du taux de présence par employé
            employee_stats['presence_rate'] = employee_stats['statut'].apply(
                lambda x: (x['present'] / x['total']) * 100 if x['total'] > 0 else 0
            )
            
            is_best_question = re.search(self.patterns['meilleur'], question)
            
            if is_best_question:
                # Meilleurs employés
                top_employees = employee_stats.nlargest(5, 'presence_rate')
                response = "🏆 **Top 5 Meilleurs Employés (Présence):**\n\n"
                
                for i, (_, row) in enumerate(top_employees.iterrows(), 1):
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                    response += f"{emoji} {row['matricule']}: {row['presence_rate']:.1f}%\n"
                
            else:
                # Employés problématiques
                bottom_employees = employee_stats.nsmallest(5, 'presence_rate')
                response = "⚠️ **Employés Nécessitant une Attention:**\n\n"
                
                for i, (_, row) in enumerate(bottom_employees.iterrows(), 1):
                    stats = row['statut']
                    response += f"• {row['matricule']}: {row['presence_rate']:.1f}%\n"
                    response += f"  Absences: {stats['absent']}, Retards: {stats['late']}\n"
            
            return response
            
        except Exception as e:
            return "❌ Impossible d'effectuer le classement actuellement."
    
    def get_suggested_questions(self):
        """Retourne des questions suggérées enrichies"""
        return [
            "Combien de retards chez les chantres aujourd'hui?",
            "Quel est le taux de présence du domaine Protocole cette semaine?",
            "Combien d'absences au total ce mois?",
            "Quelles sont les alertes actives?",
            "Montre-moi les prédictions comportementales",
            "Compare cette semaine à la semaine dernière",
            "Quelle est la tendance de présence ce mois?",
            "Quel domaine a la meilleure performance?",
            "Quels sont les employés les plus assidus?",
            "Y a-t-il des employés problématiques?",
            "Analyse les performances par domaine",
            "Quels employés nécessitent une attention?",
            "Évolution de la présence sur 30 jours",
            "Statistiques générales aujourd'hui",
            "Aide - que peux-tu faire?"
        ]