# Dashboard Statistiques QR Pointage

## Overview

This is a comprehensive Streamlit-based dashboard application for tracking and analyzing QR code attendance statistics. The system manages employee attendance data, provides real-time analytics, generates comprehensive reports, and now includes advanced features like AI-powered chatbot assistance, predictive analytics, and automated alert systems. It's designed for organizations using QR code-based attendance tracking systems with domain-based employee classification.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (January 2025)

### Major Feature Additions:
- **Authentication System**: Secure login portal with default credentials (administrator/RichyMLG007)
- **AI Chatbot Module**: Natural language query interface for attendance statistics
- **Predictive Analytics**: Machine learning-based employee behavior prediction
- **Alert System**: Automated notifications for excessive absences (>2) and tardiness (≥3)
- **SMS Notifications**: Twilio integration for real-time alerts
- **Multi-tab Interface**: Organized dashboard, chatbot, predictions, alerts, and settings

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
   - Streamlit dashboard configuration and UI with multi-tab interface
   - Data filtering and visualization logic
   - Integration of all components including authentication, chatbot, predictions, and alerts

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

5. **auth.py** - Authentication and user management
   - Secure login system with configurable credentials
   - User role management (admin/user)
   - Password change and user administration features

6. **chatbot.py** - AI-powered query assistant
   - Natural language processing for attendance queries
   - Domain-specific question understanding
   - Contextual response generation with statistical data

7. **prediction.py** - Predictive analytics module
   - Machine learning models for behavior prediction
   - Risk analysis and employee behavior forecasting
   - Scikit-learn integration for attendance pattern analysis

8. **alerts.py** - Automated alert system
   - Threshold-based absence and tardiness monitoring
   - Twilio SMS integration for real-time notifications
   - Configurable alert rules and notification management

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