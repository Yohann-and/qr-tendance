import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import random
from database import DatabaseManager
import streamlit as st

class SampleDataGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        self.employees = self._generate_employees()
        self.statuses = ['Présent', 'Absent', 'Retard']
        self.weights = [0.75, 0.15, 0.10]  # 75% présent, 15% absent, 10% retard
        
    def _generate_employees(self):
        """Génère une liste d'employés avec des matricules réalistes"""
        employees = []
        
        # Domaine Chantre (C)
        for i in range(1, 16):  # 15 employés
            employees.append(f"C{i:03d}")
        
        # Domaine Protocole (P)
        for i in range(1, 13):  # 12 employés
            employees.append(f"P{i:03d}")
        
        # Domaine Régis (R)
        for i in range(1, 11):  # 10 employés
            employees.append(f"R{i:03d}")
        
        return employees
    
    def generate_sample_data(self, days_back=30):
        """Génère des données de test pour les derniers jours"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        data = []
        
        # Pour chaque jour dans la période
        current_date = start_date
        while current_date <= end_date:
            # Pour chaque employé
            for emp in self.employees:
                # Probabilité de présence selon le domaine et l'employé
                base_weights = self._get_employee_weights(emp, current_date)
                
                # Choix du statut
                status = np.random.choice(self.statuses, p=base_weights)
                
                # Génération de l'heure de pointage
                hour, minute = self._generate_time(status)
                
                # Création de l'enregistrement
                record = {
                    'matricule': emp,
                    'date_pointage': current_date,
                    'heure_pointage': f"{hour:02d}:{minute:02d}:00",
                    'statut': status,
                    'created_at': datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute)),
                    'updated_at': datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                }
                
                data.append(record)
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(data)
    
    def _get_employee_weights(self, matricule, date):
        """Calcule les probabilités de statut pour un employé donné"""
        base_weights = list(self.weights)
        
        # Simulation de patterns comportementaux
        emp_hash = hash(matricule) % 100
        
        # Certains employés sont plus fiables
        if emp_hash < 20:  # 20% d'employés très fiables
            base_weights = [0.90, 0.05, 0.05]
        elif emp_hash < 40:  # 20% d'employés problématiques
            base_weights = [0.60, 0.25, 0.15]
        
        # Effet du jour de la semaine
        weekday = date.weekday()
        if weekday == 0:  # Lundi - plus d'absences
            base_weights[1] *= 1.5
        elif weekday == 4:  # Vendredi - plus de retards
            base_weights[2] *= 1.3
        
        # Normalisation
        total = sum(base_weights)
        return [w/total for w in base_weights]
    
    def _generate_time(self, status):
        """Génère une heure de pointage réaliste selon le statut"""
        if status == 'Présent':
            # Arrivée normale entre 7h30 et 8h30
            hour = random.choice([7, 8])
            minute = random.randint(0, 59)
            if hour == 7 and minute < 30:
                minute += 30
        elif status == 'Retard':
            # Arrivée en retard entre 8h30 et 10h
            hour = random.choice([8, 9, 10])
            minute = random.randint(0, 59)
            if hour == 8 and minute < 30:
                minute += 30
        else:  # Absent
            # Pas de pointage, mais on génère une heure fictive
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
        
        return hour, minute
    
    def create_database_table(self):
        """Crée la table de pointage si elle n'existe pas"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Création de la table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS pointages (
                id SERIAL PRIMARY KEY,
                matricule VARCHAR(10) NOT NULL,
                date_pointage DATE NOT NULL,
                heure_pointage TIME NOT NULL,
                statut VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            
            # Création d'un index pour améliorer les performances
            index_query = """
            CREATE INDEX IF NOT EXISTS idx_pointages_date_matricule 
            ON pointages(date_pointage, matricule)
            """
            
            cursor.execute(index_query)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de la création de la table: {str(e)}")
            return False
    
    def insert_sample_data(self, df):
        """Insère les données de test dans la base"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Suppression des données existantes pour éviter les doublons
            cursor.execute("DELETE FROM pointages")
            
            # Insertion des nouvelles données
            for _, row in df.iterrows():
                insert_query = """
                INSERT INTO pointages (matricule, date_pointage, heure_pointage, statut, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    row['matricule'],
                    row['date_pointage'],
                    row['heure_pointage'],
                    row['statut'],
                    row['created_at'],
                    row['updated_at']
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de l'insertion des données: {str(e)}")
            return False
    
    def setup_sample_data(self, days_back=30):
        """Configure complètement les données de test"""
        st.info("Création de la table de pointage...")
        
        if not self.create_database_table():
            return False
        
        st.info("Génération des données de test...")
        sample_df = self.generate_sample_data(days_back)
        
        st.info(f"Insertion de {len(sample_df)} enregistrements...")
        
        if self.insert_sample_data(sample_df):
            st.success(f"✅ {len(sample_df)} enregistrements créés avec succès!")
            st.info(f"Données générées pour {len(self.employees)} employés sur {days_back} jours")
            
            # Affichage des statistiques
            stats = self._get_data_statistics(sample_df)
            st.write("📊 **Statistiques des données générées:**")
            st.write(f"- Total employés: {stats['total_employees']}")
            st.write(f"- Présences: {stats['present']} ({stats['present_rate']:.1f}%)")
            st.write(f"- Absences: {stats['absent']} ({stats['absent_rate']:.1f}%)")
            st.write(f"- Retards: {stats['late']} ({stats['late_rate']:.1f}%)")
            
            return True
        else:
            return False
    
    def _get_data_statistics(self, df):
        """Calcule les statistiques des données générées"""
        total_employees = df['matricule'].nunique()
        total_records = len(df)
        
        status_counts = df['statut'].value_counts()
        present = status_counts.get('Présent', 0)
        absent = status_counts.get('Absent', 0)
        late = status_counts.get('Retard', 0)
        
        return {
            'total_employees': total_employees,
            'total_records': total_records,
            'present': present,
            'absent': absent,
            'late': late,
            'present_rate': (present / total_records * 100) if total_records > 0 else 0,
            'absent_rate': (absent / total_records * 100) if total_records > 0 else 0,
            'late_rate': (late / total_records * 100) if total_records > 0 else 0
        }
    
    def get_employee_list(self):
        """Retourne la liste des employés générés"""
        return self.employees
    
    def clear_data(self):
        """Efface toutes les données de test"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pointages")
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erreur lors de la suppression: {str(e)}")
            return False