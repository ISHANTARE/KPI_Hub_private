"""
PDF helper: generate PDF bytes from plain text using reportlab if available.
Falls back to a plain-text bytes blob if reportlab is not installed.
"""
import io
import logging

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    letter = None
    canvas = None

logger = logging.getLogger(__name__)


def text_to_pdf_bytes(text: str, title: str = "Summary") -> bytes:
    """Return PDF bytes for the given text. If reportlab is missing, return plain text bytes."""
    if canvas is None:
        logger.warning("reportlab not installed; returning plain-text bytes instead of PDF")
        return text.encode('utf-8')

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    # Simple text wrapping
    lines = text.split('\n')
    y = height - 72
    c.setFont('Helvetica-Bold', 14)
    c.drawString(72, y, title)
    y -= 24
    c.setFont('Helvetica', 10)

    for line in lines:
        # split long lines
        while len(line) > 100:
            chunk = line[:100]
            c.drawString(72, y, chunk)
            y -= 14
            line = line[100:]
        c.drawString(72, y, line)
        y -= 14
        if y < 72:
            c.showPage()
            y = height - 72

    c.save()
    buf.seek(0)
    return buf.read()
