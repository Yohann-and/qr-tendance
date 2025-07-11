import pandas as pd
from datetime import datetime, timedelta
import re

def classify_domain(matricule):
    """
    Classifie un employé dans un domaine selon le préfixe de son matricule
    """
    if not isinstance(matricule, str):
        matricule = str(matricule)
    
    matricule = matricule.upper().strip()
    
    if matricule.startswith('C'):
        return 'Chantre'
    elif matricule.startswith('P'):
        return 'Protocole'
    elif matricule.startswith('R'):
        return 'Régis'
    else:
        return 'Autre'

def calculate_statistics(df):
    """
    Calcule les statistiques principales à partir du DataFrame
    """
    if df.empty:
        return {
            'total_employees': 0,
            'total_records': 0,
            'total_present': 0,
            'total_absent': 0,
            'total_late': 0,
            'new_employees_today': 0
        }
    
    stats = {}
    
    # Statistiques générales
    stats['total_employees'] = df['matricule'].nunique()
    stats['total_records'] = len(df)
    
    # Comptage par statut
    status_counts = df['statut'].value_counts()
    stats['total_present'] = status_counts.get('Présent', 0)
    stats['total_absent'] = status_counts.get('Absent', 0)
    stats['total_late'] = status_counts.get('Retard', 0)
    
    # Statistiques par domaine
    domain_stats = df.groupby(['domaine', 'statut']).size().unstack(fill_value=0)
    stats['domain_breakdown'] = domain_stats.to_dict()
    
    # Calculs supplémentaires si les données le permettent
    try:
        # Employés nouveaux aujourd'hui (basé sur created_at si disponible)
        if 'created_at' in df.columns:
            today = datetime.now().date()
            new_today = df[pd.to_datetime(df['created_at']).dt.date == today]['matricule'].nunique()
            stats['new_employees_today'] = new_today
        else:
            stats['new_employees_today'] = 0
        
        # Comparaison avec hier si possible
        if 'date_pointage' in df.columns:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            today_data = df[pd.to_datetime(df['date_pointage']).dt.date == today]
            yesterday_data = df[pd.to_datetime(df['date_pointage']).dt.date == yesterday]
            
            if not yesterday_data.empty:
                yesterday_present = len(yesterday_data[yesterday_data['statut'] == 'Présent'])
                yesterday_late = len(yesterday_data[yesterday_data['statut'] == 'Retard'])
                yesterday_total = len(yesterday_data)
                
                stats['yesterday_presence_rate'] = (yesterday_present / max(yesterday_total, 1)) * 100
                stats['present_vs_yesterday'] = stats['total_present'] - yesterday_present
                stats['late_vs_yesterday'] = stats['total_late'] - yesterday_late
    
    except Exception:
        # En cas d'erreur, continuer avec les stats de base
        pass
    
    return stats

def format_time_display(dt):
    """
    Formate une datetime pour l'affichage
    """
    return dt.strftime("%d/%m/%Y à %H:%M:%S")

def validate_matricule(matricule):
    """
    Valide le format d'un matricule
    """
    if not isinstance(matricule, str):
        return False
    
    # Doit commencer par C, P, ou R suivi de chiffres
    pattern = r'^[CPR]\d+$'
    return bool(re.match(pattern, matricule.upper().strip()))

def calculate_presence_rate(df, domain=None):
    """
    Calcule le taux de présence pour un domaine spécifique ou global
    """
    if df.empty:
        return 0
    
    if domain:
        df = df[df['domaine'] == domain]
    
    if df.empty:
        return 0
    
    total = len(df)
    present = len(df[df['statut'] == 'Présent'])
    
    return (present / total) * 100

def get_time_period_stats(df, period='today'):
    """
    Récupère les statistiques pour une période donnée
    """
    if df.empty or 'date_pointage' not in df.columns:
        return {}
    
    now = datetime.now()
    
    if period == 'today':
        target_date = now.date()
        period_data = df[pd.to_datetime(df['date_pointage']).dt.date == target_date]
    elif period == 'week':
        start_week = now.date() - timedelta(days=now.weekday())
        period_data = df[pd.to_datetime(df['date_pointage']).dt.date >= start_week]
    elif period == 'month':
        start_month = now.date().replace(day=1)
        period_data = df[pd.to_datetime(df['date_pointage']).dt.date >= start_month]
    else:
        period_data = df
    
    return calculate_statistics(period_data)

def export_summary_stats(stats):
    """
    Exporte un résumé des statistiques en format texte
    """
    summary = f"""
    RAPPORT DE POINTAGE - {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    STATISTIQUES GÉNÉRALES:
    - Total employés: {stats.get('total_employees', 0)}
    - Total enregistrements: {stats.get('total_records', 0)}
    
    RÉPARTITION PAR STATUT:
    - Présents: {stats.get('total_present', 0)}
    - Absents: {stats.get('total_absent', 0)}  
    - Retards: {stats.get('total_late', 0)}
    
    TAUX DE PRÉSENCE:
    - Global: {(stats.get('total_present', 0) / max(stats.get('total_records', 1), 1) * 100):.1f}%
    """
    
    return summary

def clean_dataframe(df):
    """
    Nettoie et standardise un DataFrame de pointage
    """
    if df.empty:
        return df
    
    # Copie pour éviter les modifications en place
    df_clean = df.copy()
    
    # Nettoyage des matricules
    if 'matricule' in df_clean.columns:
        df_clean['matricule'] = df_clean['matricule'].astype(str).str.upper().str.strip()
        # Supprime les matricules invalides
        df_clean = df_clean[df_clean['matricule'].str.match(r'^[CPR]\d+$', na=False)]
    
    # Nettoyage des statuts
    if 'statut' in df_clean.columns:
        df_clean['statut'] = df_clean['statut'].astype(str).str.strip()
        # Garde seulement les statuts valides
        valid_statuses = ['Présent', 'Absent', 'Retard']
        df_clean = df_clean[df_clean['statut'].isin(valid_statuses)]
    
    # Supprime les doublons
    if 'matricule' in df_clean.columns and 'date_pointage' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['matricule', 'date_pointage'], keep='last')
    
    return df_clean

def generate_domain_summary(df):
    """
    Génère un résumé par domaine
    """
    if df.empty:
        return {}
    
    summary = {}
    
    for domain in ['Chantre', 'Protocole', 'Régis']:
        domain_data = df[df['domaine'] == domain]
        
        if not domain_data.empty:
            summary[domain] = {
                'total': len(domain_data),
                'present': len(domain_data[domain_data['statut'] == 'Présent']),
                'absent': len(domain_data[domain_data['statut'] == 'Absent']),
                'late': len(domain_data[domain_data['statut'] == 'Retard']),
                'presence_rate': calculate_presence_rate(domain_data)
            }
        else:
            summary[domain] = {
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'presence_rate': 0
            }
    
    return summary
