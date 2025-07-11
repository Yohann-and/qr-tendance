import psycopg2
import pandas as pd
import os
from datetime import datetime, date
import streamlit as st

class DatabaseManager:
    def __init__(self):
        """Initialise la connexion à la base de données PostgreSQL"""
        self.connection_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'qr_attendance'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', '')
        }
        
        # Alternative avec DATABASE_URL si disponible
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            self.database_url = database_url
            self.use_url = True
        else:
            self.use_url = False
    
    def get_connection(self):
        """Établit une connexion à la base de données"""
        try:
            if self.use_url:
                conn = psycopg2.connect(self.database_url)
            else:
                conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.Error as e:
            st.error(f"Erreur de connexion à la base de données: {e}")
            raise
    
    def get_attendance_data(self, start_date, end_date):
        """
        Récupère les données de pointage pour la période spécifiée
        """
        query = """
        SELECT 
            matricule,
            date_pointage,
            heure_pointage,
            statut,
            created_at,
            updated_at
        FROM pointages 
        WHERE date_pointage BETWEEN %s AND %s
        ORDER BY date_pointage DESC, heure_pointage DESC
        """
        
        try:
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=[start_date, end_date])
            conn.close()
            
            # Conversion des types de données
            if not df.empty:
                df['date_pointage'] = pd.to_datetime(df['date_pointage'])
                if 'heure_pointage' in df.columns:
                    df['heure_pointage'] = pd.to_datetime(df['heure_pointage'], format='%H:%M:%S').dt.time
                
                # Nettoyage des données
                df['matricule'] = df['matricule'].astype(str).str.upper().str.strip()
                df['statut'] = df['statut'].str.strip()
            
            return df
            
        except psycopg2.Error as e:
            st.error(f"Erreur lors de la récupération des données: {e}")
            return pd.DataFrame()
        except Exception as e:
            # Fallback: tentative avec une structure de table alternative
            return self.get_attendance_data_fallback(start_date, end_date)
    
    def get_attendance_data_fallback(self, start_date, end_date):
        """
        Méthode de fallback avec une structure de table alternative
        """
        queries_to_try = [
            # Structure alternative 1
            """
            SELECT 
                employee_id as matricule,
                attendance_date as date_pointage,
                check_in_time as heure_pointage,
                status as statut,
                created_at,
                updated_at
            FROM attendance 
            WHERE attendance_date BETWEEN %s AND %s
            ORDER BY attendance_date DESC, check_in_time DESC
            """,
            
            # Structure alternative 2
            """
            SELECT 
                emp_code as matricule,
                punch_date as date_pointage,
                punch_time as heure_pointage,
                attendance_status as statut,
                created_at,
                updated_at
            FROM employee_attendance 
            WHERE punch_date BETWEEN %s AND %s
            ORDER BY punch_date DESC, punch_time DESC
            """,
            
            # Structure alternative 3 - très générique
            """
            SELECT 
                *
            FROM (
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND (table_name LIKE '%pointage%' 
                     OR table_name LIKE '%attendance%'
                     OR table_name LIKE '%presence%')
                LIMIT 1
            ) t
            """
        ]
        
        for query in queries_to_try:
            try:
                conn = self.get_connection()
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                conn.close()
                
                if not df.empty:
                    # Normalisation des colonnes
                    column_mapping = {
                        'employee_id': 'matricule',
                        'emp_code': 'matricule',
                        'attendance_date': 'date_pointage',
                        'punch_date': 'date_pointage',
                        'check_in_time': 'heure_pointage',
                        'punch_time': 'heure_pointage',
                        'status': 'statut',
                        'attendance_status': 'statut'
                    }
                    
                    df.rename(columns=column_mapping, inplace=True)
                    
                    # Assurer la présence des colonnes essentielles
                    required_columns = ['matricule', 'date_pointage', 'statut']
                    if all(col in df.columns for col in required_columns):
                        return self.process_dataframe(df)
                
            except Exception:
                continue
        
        # Si aucune requête ne fonctionne, retourner un DataFrame vide
        return pd.DataFrame()
    
    def process_dataframe(self, df):
        """
        Traite et nettoie le DataFrame
        """
        if df.empty:
            return df
        
        # Conversion des types
        if 'date_pointage' in df.columns:
            df['date_pointage'] = pd.to_datetime(df['date_pointage'])
        
        if 'heure_pointage' in df.columns:
            try:
                df['heure_pointage'] = pd.to_datetime(df['heure_pointage'], format='%H:%M:%S').dt.time
            except:
                # Si la conversion échoue, essayer d'autres formats
                try:
                    df['heure_pointage'] = pd.to_datetime(df['heure_pointage']).dt.time
                except:
                    pass
        
        # Nettoyage des données
        if 'matricule' in df.columns:
            df['matricule'] = df['matricule'].astype(str).str.upper().str.strip()
        
        if 'statut' in df.columns:
            df['statut'] = df['statut'].astype(str).str.strip()
            
            # Normalisation des statuts
            status_mapping = {
                'present': 'Présent',
                'presente': 'Présent',
                'attendance': 'Présent',
                'on_time': 'Présent',
                'absent': 'Absent',
                'absente': 'Absent',
                'missing': 'Absent',
                'late': 'Retard',
                'retard': 'Retard',
                'delayed': 'Retard',
                'tardy': 'Retard'
            }
            
            df['statut'] = df['statut'].str.lower().map(status_mapping).fillna(df['statut'])
        
        return df
    
    def get_table_structure(self):
        """
        Récupère la structure des tables disponibles pour diagnostic
        """
        query = """
        SELECT 
            table_name,
            column_name,
            data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND (table_name LIKE '%pointage%' 
             OR table_name LIKE '%attendance%'
             OR table_name LIKE '%presence%')
        ORDER BY table_name, ordinal_position
        """
        
        try:
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erreur lors de la récupération de la structure: {e}")
            return pd.DataFrame()
    
    def test_connection(self):
        """
        Teste la connexion à la base de données
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return True, "Connexion réussie"
        except Exception as e:
            return False, str(e)
