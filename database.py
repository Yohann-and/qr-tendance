import psycopg2
import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        """Initialise la connexion PostgreSQL (Render ou locale)"""
        
        # ✅ Cas 1 : Render → Variable Database_url
        self.database_url = os.getenv('Database_url')
        self.use_url = False

        if self.database_url:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
            self.use_url = True

        # ✅ Cas 2 : Connexion locale (fallback)
        self.connection_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'qr_attendance'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', '')
        }

    def get_connection(self):
        """Connexion fiable à PostgreSQL"""
        try:
            if self.use_url:
                return psycopg2.connect(self.database_url)
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            raise Exception(f"❌ Erreur de connexion PostgreSQL : {e}")

    def ajouter_ouvrier_et_pointage(self, matricule, nom, poste, statut="present"):
        """Ajoute un ouvrier et son pointage dans la base"""
        matricule = matricule.strip().upper()
        nom = nom.strip().title()
        poste = poste.strip().title()
        statut = statut.strip().lower()
        now = datetime.now()

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Ajout ouvrier
                    cur.execute("""
                        INSERT INTO workers (matricule, nom, poste)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (matricule) DO NOTHING;
                    """, (matricule, nom, poste))

                    # Ajout pointage
                    cur.execute("""
                        INSERT INTO attendance (
                            employee_id, attendance_date, check_in_time, status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (matricule, now.date(), now.time(), statut, now, now))

                conn.commit()
            print(f"✅ Ouvrier {matricule} et pointage {statut} enregistrés")
            return True, f"✅ Enregistré : {matricule} ({statut})"

        except Exception as e:
            print(f"❌ Erreur d’ajout : {e}")
            return False, f"❌ Erreur ajout : {e}"

    def insert_attendance(self, matricule, statut="present"):
        """Insère un pointage sans créer l’ouvrier"""
        matricule = matricule.strip().upper()
        now = datetime.now()

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO attendance (
                            employee_id, attendance_date, check_in_time, status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (matricule, now.date(), now.time(), statut, now, now))
                conn.commit()

            print(f"✅ Pointage ajouté : {matricule} ({statut})")
            return True, f"✅ Pointage enregistré : {matricule}"

        except Exception as e:
            print(f"❌ Erreur insertion attendance : {e}")
            return False, f"❌ Erreur pointage : {e}"

    def get_attendance_data(self, date_debut=None, date_fin=None, avec_jointure=False):
        """Récupère les données de pointage avec ou sans jointure"""
        try:
            with self.get_connection() as conn:
                if avec_jointure:
                    base_query = """
                        SELECT 
                            a.employee_id AS matricule,
                            w.nom,
                            w.poste,
                            a.attendance_date,
                            a.check_in_time,
                            a.status,
                            a.created_at
                        FROM attendance a
                        JOIN workers w ON a.employee_id = w.matricule
                    """
                else:
                    base_query = "SELECT * FROM attendance"

                params = ()
                if date_debut and date_fin:
                    base_query += " WHERE attendance_date BETWEEN %s AND %s"
                    params = (date_debut, date_fin)

                base_query += " ORDER BY attendance_date DESC, check_in_time DESC"

                df = pd.read_sql(base_query, conn, params=params if params else None)

            print(f"📊 {len(df)} pointages chargés.")
            return df

        except Exception as e:
            print(f"❌ Erreur récupération : {e}")
            return pd.DataFrame()

    def test_connection(self):
        """Teste la connexion PostgreSQL"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True, "✅ Connexion PostgreSQL OK"
        except Exception as e:
            return False, f"❌ Connexion échouée : {e}"
