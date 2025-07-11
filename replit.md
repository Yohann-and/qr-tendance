# Dashboard Statistiques QR Pointage

## Overview

This is a Streamlit-based dashboard application for tracking and analyzing QR code attendance statistics. The system manages employee attendance data, provides real-time analytics, and generates comprehensive reports. It's designed for organizations using QR code-based attendance tracking systems with domain-based employee classification.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application framework
- **UI Components**: Interactive dashboard with sidebar filters, data visualizations using Plotly
- **Layout**: Wide layout with expandable sidebar for filters and controls
- **Caching**: Streamlit's built-in caching for database connections and data with 60-second TTL

### Backend Architecture
- **Application Layer**: Python-based with modular design separating concerns
- **Database Layer**: PostgreSQL database integration using psycopg2
- **Data Processing**: Pandas for data manipulation and analysis
- **Report Generation**: PDF reports using ReportLab, CSV exports

### Data Storage
- **Primary Database**: PostgreSQL
- **Connection Management**: Environment variable-based configuration supporting both individual parameters and DATABASE_URL
- **Schema**: Attendance tracking table (`pointages`) with fields for employee ID, date, time, status, and timestamps

## Key Components

### Core Modules

1. **app.py** - Main application entry point
   - Streamlit dashboard configuration and UI
   - Data filtering and visualization logic
   - Integration of all components

2. **database.py** - Database management layer
   - PostgreSQL connection handling
   - Data retrieval methods for attendance records
   - Environment-based configuration for flexible deployment

3. **utils.py** - Utility functions
   - Employee domain classification based on matricule prefixes
   - Statistical calculations and data processing
   - Time formatting utilities

4. **reports.py** - Report generation system
   - PDF report creation with ReportLab
   - CSV export functionality
   - Statistical summaries and domain-based analysis

### Employee Classification System
- **Domain Classification**: Automatic categorization based on matricule prefixes
  - 'C' prefix → Chantre domain
  - 'P' prefix → Protocole domain  
  - 'R' prefix → Régis domain
  - Other → Autre domain

### Attendance Status Tracking
- **Status Types**: Présent (Present), Absent, Retard (Late)
- **Time-based Analysis**: Daily, weekly, monthly reporting periods
- **Statistical Metrics**: Total employees, attendance rates, domain-specific statistics

## Data Flow

1. **Data Input**: Attendance records stored in PostgreSQL database
2. **Data Retrieval**: Database manager fetches filtered attendance data
3. **Data Processing**: Utils module classifies employees and calculates statistics
4. **Visualization**: Streamlit displays interactive charts and metrics
5. **Report Generation**: On-demand PDF and CSV report creation

## External Dependencies

### Python Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive data visualization
- **psycopg2**: PostgreSQL database adapter
- **reportlab**: PDF generation
- **datetime**: Date and time handling

### Database
- **PostgreSQL**: Primary data storage with attendance tracking schema

## Deployment Strategy

### Environment Configuration
- Supports both individual database parameters and DATABASE_URL for flexible deployment
- Environment variables for database connection (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
- Streamlit configuration for production deployment

### Performance Optimization
- Resource caching for database connections
- Data caching with TTL for improved response times
- Modular architecture for maintainability

### Database Schema Requirements
The application expects a `pointages` table with the following structure:
- `matricule`: Employee ID/badge number
- `date_pointage`: Attendance date
- `heure_pointage`: Attendance time
- `statut`: Attendance status (Présent/Absent/Retard)
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp