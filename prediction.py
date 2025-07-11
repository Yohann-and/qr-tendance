import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import DatabaseManager
from utils import classify_domain
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import warnings
warnings.filterwarnings('ignore')

class AttendancePrediction:
    def __init__(self):
        self.db = DatabaseManager()
        self.model = None
        self.label_encoder = LabelEncoder()
        self.features = []
        
    def prepare_data(self, df):
        """Prépare les données pour la prédiction"""
        if df.empty:
            return pd.DataFrame()
        
        # Ajout de la classification des domaines
        df['domaine'] = df['matricule'].apply(classify_domain)
        
        # Conversion des dates
        df['date_pointage'] = pd.to_datetime(df['date_pointage'])
        
        # Création des features temporelles
        df['jour_semaine'] = df['date_pointage'].dt.dayofweek
        df['mois'] = df['date_pointage'].dt.month
        df['jour_mois'] = df['date_pointage'].dt.day
        df['semaine_annee'] = df['date_pointage'].dt.isocalendar().week
        
        # Features d'historique par employé
        employee_features = []
        
        for matricule in df['matricule'].unique():
            emp_data = df[df['matricule'] == matricule].copy()
            emp_data = emp_data.sort_values('date_pointage')
            
            # Calcul des statistiques historiques
            for i in range(len(emp_data)):
                historic_data = emp_data.iloc[:i+1]
                
                # Statistiques de base
                total_days = len(historic_data)
                present_days = len(historic_data[historic_data['statut'] == 'Présent'])
                absent_days = len(historic_data[historic_data['statut'] == 'Absent'])
                late_days = len(historic_data[historic_data['statut'] == 'Retard'])
                
                # Ratios
                presence_rate = present_days / total_days if total_days > 0 else 0
                absence_rate = absent_days / total_days if total_days > 0 else 0
                late_rate = late_days / total_days if total_days > 0 else 0
                
                # Tendances récentes (7 derniers jours)
                recent_data = historic_data.tail(7)
                recent_present = len(recent_data[recent_data['statut'] == 'Présent'])
                recent_absent = len(recent_data[recent_data['statut'] == 'Absent'])
                recent_late = len(recent_data[recent_data['statut'] == 'Retard'])
                
                # Patterns comportementaux
                consecutive_absences = self._count_consecutive_status(historic_data, 'Absent')
                consecutive_lates = self._count_consecutive_status(historic_data, 'Retard')
                
                # Ajout des features
                features = {
                    'matricule': matricule,
                    'date_pointage': emp_data.iloc[i]['date_pointage'],
                    'domaine': emp_data.iloc[i]['domaine'],
                    'jour_semaine': emp_data.iloc[i]['jour_semaine'],
                    'mois': emp_data.iloc[i]['mois'],
                    'jour_mois': emp_data.iloc[i]['jour_mois'],
                    'semaine_annee': emp_data.iloc[i]['semaine_annee'],
                    'total_days': total_days,
                    'presence_rate': presence_rate,
                    'absence_rate': absence_rate,
                    'late_rate': late_rate,
                    'recent_present': recent_present,
                    'recent_absent': recent_absent,
                    'recent_late': recent_late,
                    'consecutive_absences': consecutive_absences,
                    'consecutive_lates': consecutive_lates,
                    'statut': emp_data.iloc[i]['statut']
                }
                
                employee_features.append(features)
        
        return pd.DataFrame(employee_features)
    
    def _count_consecutive_status(self, df, status):
        """Compte les occurrences consécutives d'un statut"""
        if df.empty:
            return 0
        
        recent_statuses = df.tail(5)['statut'].tolist()
        consecutive = 0
        
        for s in reversed(recent_statuses):
            if s == status:
                consecutive += 1
            else:
                break
                
        return consecutive
    
    def train_model(self, feature_df):
        """Entraîne le modèle de prédiction"""
        if feature_df.empty:
            return False
        
        # Sélection des features
        feature_columns = [
            'jour_semaine', 'mois', 'jour_mois', 'semaine_annee',
            'total_days', 'presence_rate', 'absence_rate', 'late_rate',
            'recent_present', 'recent_absent', 'recent_late',
            'consecutive_absences', 'consecutive_lates'
        ]
        
        # Encodage du domaine
        domain_encoded = self.label_encoder.fit_transform(feature_df['domaine'])
        
        # Préparation des données
        X = feature_df[feature_columns].copy()
        X['domaine_encoded'] = domain_encoded
        
        # Variable cible
        y = feature_df['statut']
        
        # Division train/test
        if len(X) < 10:
            # Si peu de données, on utilise tout pour l'entraînement
            X_train, X_test, y_train, y_test = X, X, y, y
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        
        # Entraînement du modèle
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Évaluation
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.features = feature_columns + ['domaine_encoded']
        
        return accuracy
    
    def predict_employee_behavior(self, matricule, days_ahead=7):
        """Prédit le comportement d'un employé pour les prochains jours"""
        if not self.model:
            return None
        
        try:
            # Récupération des données historiques
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)  # 30 jours d'historique
            
            df = self.db.get_attendance_data(start_date, end_date)
            
            if df.empty:
                return None
            
            # Préparation des données
            feature_df = self.prepare_data(df)
            
            # Données de l'employé
            emp_data = feature_df[feature_df['matricule'] == matricule]
            
            if emp_data.empty:
                return None
            
            # Dernières données de l'employé
            last_record = emp_data.iloc[-1]
            
            predictions = []
            
            for i in range(days_ahead):
                future_date = end_date + timedelta(days=i+1)
                
                # Création des features pour le jour futur
                future_features = {
                    'jour_semaine': future_date.weekday(),
                    'mois': future_date.month,
                    'jour_mois': future_date.day,
                    'semaine_annee': future_date.isocalendar().week,
                    'total_days': last_record['total_days'] + i + 1,
                    'presence_rate': last_record['presence_rate'],
                    'absence_rate': last_record['absence_rate'],
                    'late_rate': last_record['late_rate'],
                    'recent_present': last_record['recent_present'],
                    'recent_absent': last_record['recent_absent'],
                    'recent_late': last_record['recent_late'],
                    'consecutive_absences': last_record['consecutive_absences'],
                    'consecutive_lates': last_record['consecutive_lates'],
                    'domaine_encoded': self.label_encoder.transform([last_record['domaine']])[0]
                }
                
                # Prédiction
                X_pred = pd.DataFrame([future_features])
                prediction = self.model.predict(X_pred)[0]
                probability = self.model.predict_proba(X_pred)[0]
                
                predictions.append({
                    'date': future_date,
                    'prediction': prediction,
                    'probability': max(probability),
                    'probabilities': dict(zip(self.model.classes_, probability))
                })
            
            return predictions
            
        except Exception as e:
            st.error(f"Erreur lors de la prédiction: {str(e)}")
            return None
    
    def get_risk_analysis(self, matricule):
        """Analyse les risques pour un employé"""
        try:
            # Récupération des données des 30 derniers jours
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            df = self.db.get_attendance_data(start_date, end_date)
            
            if df.empty:
                return {}
            
            # Données de l'employé
            emp_data = df[df['matricule'] == matricule]
            
            if emp_data.empty:
                return {}
            
            # Calcul des statistiques
            total_days = len(emp_data)
            present_days = len(emp_data[emp_data['statut'] == 'Présent'])
            absent_days = len(emp_data[emp_data['statut'] == 'Absent'])
            late_days = len(emp_data[emp_data['statut'] == 'Retard'])
            
            # Ratios
            presence_rate = present_days / total_days if total_days > 0 else 0
            absence_rate = absent_days / total_days if total_days > 0 else 0
            late_rate = late_days / total_days if total_days > 0 else 0
            
            # Évaluation des risques
            risk_level = "Faible"
            risk_factors = []
            
            if absence_rate > 0.2:  # Plus de 20% d'absences
                risk_level = "Élevé"
                risk_factors.append(f"Taux d'absence élevé ({absence_rate:.1%})")
            elif absence_rate > 0.1:  # Plus de 10% d'absences
                risk_level = "Modéré"
                risk_factors.append(f"Taux d'absence modéré ({absence_rate:.1%})")
            
            if late_rate > 0.15:  # Plus de 15% de retards
                if risk_level == "Faible":
                    risk_level = "Modéré"
                risk_factors.append(f"Taux de retard élevé ({late_rate:.1%})")
            
            # Tendance récente
            recent_data = emp_data.tail(7)
            recent_issues = len(recent_data[recent_data['statut'] != 'Présent'])
            
            if recent_issues > 3:
                risk_level = "Élevé"
                risk_factors.append(f"Problèmes récents ({recent_issues} sur 7 jours)")
            
            return {
                'matricule': matricule,
                'domaine': classify_domain(matricule),
                'total_days': total_days,
                'presence_rate': presence_rate,
                'absence_rate': absence_rate,
                'late_rate': late_rate,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recent_issues': recent_issues
            }
            
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des risques: {str(e)}")
            return {}
    
    def get_global_predictions(self):
        """Prédictions globales pour tous les employés"""
        try:
            # Récupération des données
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            df = self.db.get_attendance_data(start_date, end_date)
            
            if df.empty:
                return {}
            
            # Préparation des données
            feature_df = self.prepare_data(df)
            
            # Entraînement du modèle
            accuracy = self.train_model(feature_df)
            
            if not self.model:
                return {}
            
            # Prédictions pour tous les employés actifs
            employees = df['matricule'].unique()
            predictions = {}
            
            for emp in employees:
                pred = self.predict_employee_behavior(emp, 7)
                if pred:
                    predictions[emp] = pred
            
            return {
                'model_accuracy': accuracy,
                'predictions': predictions,
                'total_employees': len(employees)
            }
            
        except Exception as e:
            st.error(f"Erreur lors des prédictions globales: {str(e)}")
            return {}
    
    def create_prediction_charts(self, predictions):
        """Crée des graphiques de prédiction"""
        if not predictions:
            return None
        
        # Préparation des données pour le graphique
        dates = [pred['date'] for pred in predictions]
        predicted_statuses = [pred['prediction'] for pred in predictions]
        probabilities = [pred['probability'] for pred in predictions]
        
        # Graphique en barres des prédictions
        fig = go.Figure()
        
        colors = {'Présent': 'green', 'Absent': 'red', 'Retard': 'orange'}
        
        fig.add_trace(go.Bar(
            x=dates,
            y=probabilities,
            text=predicted_statuses,
            textposition='auto',
            marker_color=[colors.get(status, 'blue') for status in predicted_statuses],
            name='Prédictions'
        ))
        
        fig.update_layout(
            title='Prédictions de Comportement (7 prochains jours)',
            xaxis_title='Date',
            yaxis_title='Probabilité',
            showlegend=True
        )
        
        return fig