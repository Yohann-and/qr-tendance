import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
import streamlit as st
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from utils import generate_domain_summary, format_time_display

def generate_pdf_report(df, stats, start_date, end_date):
    """
    Génère un rapport PDF complet des statistiques de pointage
    """
    buffer = BytesIO()
    
    # Configuration du document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20
    )
    
    normal_style = styles['Normal']
    
    # Éléments du document
    elements = []
    
    # Titre principal
    title = Paragraph("RAPPORT DE STATISTIQUES QR POINTAGE", title_style)
    elements.append(title)
    
    # Informations générales
    period_info = f"Période: {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
    generation_info = f"Généré le: {format_time_display(datetime.now())}"
    
    elements.append(Paragraph(period_info, normal_style))
    elements.append(Paragraph(generation_info, normal_style))
    elements.append(Spacer(1, 20))
    
    # Résumé exécutif
    elements.append(Paragraph("RÉSUMÉ EXÉCUTIF", heading_style))
    
    summary_data = [
        ['Indicateur', 'Valeur'],
        ['Total Employés', str(stats.get('total_employees', 0))],
        ['Total Enregistrements', str(stats.get('total_records', 0))],
        ['Employés Présents', str(stats.get('total_present', 0))],
        ['Employés Absents', str(stats.get('total_absent', 0))],
        ['Employés en Retard', str(stats.get('total_late', 0))],
        ['Taux de Présence Global', f"{(stats.get('total_present', 0) / max(stats.get('total_records', 1), 1) * 100):.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Statistiques par domaine
    elements.append(Paragraph("STATISTIQUES PAR DOMAINE", heading_style))
    
    domain_summary = generate_domain_summary(df)
    
    domain_data = [['Domaine', 'Total', 'Présents', 'Absents', 'Retards', 'Taux Présence']]
    
    for domain, data in domain_summary.items():
        domain_data.append([
            domain,
            str(data['total']),
            str(data['present']),
            str(data['absent']),
            str(data['late']),
            f"{data['presence_rate']:.1f}%"
        ])
    
    domain_table = Table(domain_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
    domain_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    
    elements.append(domain_table)
    elements.append(Spacer(1, 20))
    
    # Analyse détaillée
    elements.append(Paragraph("ANALYSE DÉTAILLÉE", heading_style))
    
    analysis_text = []
    
    # Analyse globale
    total_employees = stats.get('total_employees', 0)
    presence_rate = (stats.get('total_present', 0) / max(stats.get('total_records', 1), 1) * 100)
    
    if presence_rate >= 90:
        analysis_text.append("• Excellent taux de présence global (≥90%)")
    elif presence_rate >= 75:
        analysis_text.append("• Bon taux de présence global (75-89%)")
    else:
        analysis_text.append("• Taux de présence à améliorer (<75%)")
    
    # Analyse par domaine
    best_domain = max(domain_summary.items(), key=lambda x: x[1]['presence_rate'])
    worst_domain = min(domain_summary.items(), key=lambda x: x[1]['presence_rate'])
    
    analysis_text.append(f"• Meilleur domaine: {best_domain[0]} ({best_domain[1]['presence_rate']:.1f}% de présence)")
    analysis_text.append(f"• Domaine à surveiller: {worst_domain[0]} ({worst_domain[1]['presence_rate']:.1f}% de présence)")
    
    # Retards
    total_late = stats.get('total_late', 0)
    late_rate = (total_late / max(stats.get('total_records', 1), 1) * 100)
    
    if late_rate <= 5:
        analysis_text.append(f"• Taux de retard acceptable ({late_rate:.1f}%)")
    else:
        analysis_text.append(f"• Taux de retard préoccupant ({late_rate:.1f}%) - Actions correctives recommandées")
    
    for text in analysis_text:
        elements.append(Paragraph(text, normal_style))
    
    elements.append(Spacer(1, 20))
    
    # Recommandations
    elements.append(Paragraph("RECOMMANDATIONS", heading_style))
    
    recommendations = [
        "• Maintenir le suivi régulier des statistiques de présence",
        "• Organiser des sessions de sensibilisation pour les domaines avec faible taux de présence",
        "• Mettre en place des mesures incitatives pour réduire les retards",
        "• Analyser les causes d'absence récurrentes par domaine",
        "• Considérer l'ajustement des horaires de travail si nécessaire"
    ]
    
    for recommendation in recommendations:
        elements.append(Paragraph(recommendation, normal_style))
    
    # Génération du PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer.getvalue()

def generate_csv_report(df):
    """
    Génère un rapport CSV des données de pointage
    """
    if df.empty:
        return "Aucune donnée disponible"
    
    # Préparation des données pour l'export
    export_df = df.copy()
    
    # Ajout de colonnes calculées
    if 'date_pointage' in export_df.columns:
        export_df['semaine'] = pd.to_datetime(export_df['date_pointage']).dt.isocalendar().week
        export_df['mois'] = pd.to_datetime(export_df['date_pointage']).dt.month
        export_df['annee'] = pd.to_datetime(export_df['date_pointage']).dt.year
    
    # Réorganisation des colonnes
    column_order = [
        'matricule', 'domaine', 'date_pointage', 'heure_pointage', 
        'statut', 'semaine', 'mois', 'annee'
    ]
    
    # Garde seulement les colonnes qui existent
    available_columns = [col for col in column_order if col in export_df.columns]
    export_df = export_df[available_columns]
    
    # Conversion en CSV
    output = StringIO()
    export_df.to_csv(output, index=False, encoding='utf-8-sig')
    
    return output.getvalue()

def generate_excel_report(df, stats):
    """
    Génère un rapport Excel avec plusieurs feuilles
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Feuille 1: Données brutes
        if not df.empty:
            df.to_excel(writer, sheet_name='Données Pointage', index=False)
        
        # Feuille 2: Statistiques globales
        stats_df = pd.DataFrame([
            ['Total Employés', stats.get('total_employees', 0)],
            ['Total Enregistrements', stats.get('total_records', 0)],
            ['Présents', stats.get('total_present', 0)],
            ['Absents', stats.get('total_absent', 0)],
            ['Retards', stats.get('total_late', 0)]
        ], columns=['Indicateur', 'Valeur'])
        
        stats_df.to_excel(writer, sheet_name='Statistiques Globales', index=False)
        
        # Feuille 3: Statistiques par domaine
        domain_summary = generate_domain_summary(df)
        domain_df = pd.DataFrame.from_dict(domain_summary, orient='index')
        domain_df.reset_index(inplace=True)
        domain_df.rename(columns={'index': 'Domaine'}, inplace=True)
        
        domain_df.to_excel(writer, sheet_name='Statistiques Domaines', index=False)
    
    output.seek(0)
    return output.getvalue()

def create_attendance_summary(df, period_name):
    """
    Crée un résumé d'assiduité pour une période donnée
    """
    summary = {
        'periode': period_name,
        'date_generation': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'total_employes': df['matricule'].nunique() if not df.empty else 0,
        'total_enregistrements': len(df),
    }
    
    if not df.empty:
        # Calculs par statut
        status_counts = df['statut'].value_counts()
        summary.update({
            'presents': status_counts.get('Présent', 0),
            'absents': status_counts.get('Absent', 0),
            'retards': status_counts.get('Retard', 0)
        })
        
        # Taux de présence
        summary['taux_presence'] = (summary['presents'] / max(summary['total_enregistrements'], 1)) * 100
        
        # Statistiques par domaine
        domain_stats = {}
        for domain in ['Chantre', 'Protocole', 'Régis']:
            domain_data = df[df['domaine'] == domain]
            if not domain_data.empty:
                domain_stats[domain] = {
                    'total': len(domain_data),
                    'presents': len(domain_data[domain_data['statut'] == 'Présent']),
                    'taux_presence': len(domain_data[domain_data['statut'] == 'Présent']) / len(domain_data) * 100
                }
            else:
                domain_stats[domain] = {'total': 0, 'presents': 0, 'taux_presence': 0}
        
        summary['domaines'] = domain_stats
    
    return summary

def format_report_filename(report_type, start_date, end_date):
    """
    Formate le nom de fichier pour les rapports
    """
    date_str = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
    timestamp = datetime.now().strftime('%H%M%S')
    
    return f"rapport_{report_type}_{date_str}_{timestamp}"
