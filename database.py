import psycopg2
import pandas as pd
import os
from datetime import datetime

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

        # Connexion via Render (DATABASE_URL)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            self.database_url = database_url
            self.use_url = True
        else:
            self.use_url = False

    def get_connection(self):
        """Établit une connexion à la base de données"""
        if self.use_url:
            return psycopg2.connect(self.database_url)
        else:
            return psycopg2.connect(**self.connection_params)

    def insert_attendance(self, matricule, statut="present"):
        """
        Insère un pointage dans la table 'attendance' pour un matricule donné.
        """
        try:
            now = datetime.now()
            date_pointage = now.date()
            heure_pointage = now.time()

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO attendance (
                            employee_id, attendance_date, check_in_time, status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (matricule, date_pointage, heure_pointage, statut, now, now))
                conn.commit()
            return True, f"✅ Pointage enregistré pour : {matricule}"
        except Exception as e:
            return False, f"❌ Erreur insertion pointage : {e}"

    def get_attendance_data(self):
        """
        Récupère toutes les données de la table 'attendance' sous forme de DataFrame
        """
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM attendance ORDER BY attendance_date DESC, check_in_time DESC;"
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"❌ Erreur récupération des données : {e}")
            return pd.DataFrame()  # retourne un DataFrame vide en cas d'erreur

    def test_connection(self):
        """Teste la connexion à la base"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
            return True, "✅ Connexion réussie"
        except Exception as e:
            return False, f"❌ Erreur de connexion : {e}"
