import psycopg2
import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        """
        Initialise la connexion à la base PostgreSQL
        avec priorité à DATABASE_URL (Render)
        """
        self.connection_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'qr_attendance'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', '')
        }

        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            self.database_url = database_url
            self.use_url = True
        else:
            self.use_url = False

    def get_connection(self):
        """Établit une connexion à PostgreSQL"""
        try:
            if self.use_url:
                return psycopg2.connect(self.database_url)
            else:
                return psycopg2.connect(**self.connection_params)
        except Exception as e:
            raise Exception(f"Erreur de connexion : {e}")

    def insert_attendance(self, matricule, statut="present"):
        """
        Insère une présence dans la table 'attendance'
        :param matricule: identifiant de l'ouvrier (str)
        :param statut: 'present', 'retard', 'absent' (str)
        """
        try:
            # Nettoyage du matricule
            matricule = matricule.strip().upper()

            # Infos de date/heure actuelles
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

            print(f"✅ Insertion réussie pour {matricule} ({statut})")
            return True, f"✅ Pointage enregistré pour : {matricule}"

        except Exception as e:
            print(f"❌ Erreur d'insertion : {e}")
            return False, f"❌ Erreur insertion pointage : {e}"

    def get_attendance_data(self, date_debut=None, date_fin=None):
        """
        Récupère les données de présence entre 2 dates (ou toutes si vide)
        :return: pandas DataFrame
        """
        try:
            with self.get_connection() as conn:
                if date_debut and date_fin:
                    query = """
                        SELECT * FROM attendance
                        WHERE attendance_date BETWEEN %s AND %s
                        ORDER BY attendance_date DESC, check_in_time DESC;
                    """
                    df = pd.read_sql(query, conn, params=(date_debut, date_fin))
                else:
                    query = """
                        SELECT * FROM attendance
                        ORDER BY attendance_date DESC, check_in_time DESC;
                    """
                    df = pd.read_sql(query, conn)

            print(f"📊 {len(df)} lignes récupérées depuis attendance.")
            return df

        except Exception as e:
            print(f"❌ Erreur de lecture : {e}")
            return pd.DataFrame()

    def test_connection(self):
        """
        Teste si la base est bien accessible
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    _ = cursor.fetchone()
            return True, "✅ Connexion réussie"
        except Exception as e:
            return False, f"❌ Échec connexion : {e}"
