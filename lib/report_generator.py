"""
lib/report_generator.py
-----------------------
PDF and document report generation utilities for KPI Hub using ReportLab.
Provides functions to generate executive governance summaries and project health reports.
"""

import io
import logging
from typing import Dict, Any, Optional
import pandas as pd

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

def generate_pdf_governance_report(project_id: str, kpi_data: Dict[str, Any]) -> Optional[bytes]:
    """
    Generate a formatted PDF executive governance report for a specified project.
    Returns bytes of the PDF or None on failure.
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("ReportLab library is not installed.")
        return None

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F1923'),
            spaceAfter=12
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=20
        )

        story.append(Paragraph(f"Executive Governance Summary: {project_id}", title_style))
        story.append(Paragraph("Generated automatically by KPI Hub Engineering PMO Platform", subtitle_style))
        story.append(Spacer(1, 12))

        # Core Metrics Table
        table_data = [
            ["Metric Category", "Status / Value"],
            ["Portfolio Health Score", f"{kpi_data.get('portfolio_health', 'N/A')}%"],
            ["Release Readiness", f"{kpi_data.get('release_readiness', 'N/A')}%"],
            ["ASPICE Process Compliance", f"{kpi_data.get('aspice_compliance', 'N/A')}%"],
            ["Open Critical Defects", str(kpi_data.get('critical_defects', 0))],
        ]

        t = Table(table_data, colWidths=[250, 250])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))

        story.append(t)
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    except Exception as e:
        logger.exception(f"Failed to generate PDF report: {e}")
        return None
