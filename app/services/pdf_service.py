"""Generate quote/invoice PDF with reportlab and Smart Anchor for signature."""

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.models.quote import QuoteData, compute_totals


def _smart_anchor(signer_email: str) -> str:
    """Subnoto Smart Anchor: {{ email | signature | width | height }} (PDF points)."""
    return f"{{{{ {signer_email} | signature | 180 | 60 }}}}"


def _format_eur(value: float) -> str:
    return f"€{value:,.2f}"


LEFT_MARGIN = 25 * mm


def build_quote_pdf(quote: QuoteData) -> bytes:
    """Build a one-page invoice-style PDF with optional line items, totals, and Smart Anchor. Returns PDF bytes."""
    buf = BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    y = height - 40 * mm

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(LEFT_MARGIN, y, "Invoice")
    y -= 14 * mm

    # Meta block: quote no., dates
    c.setFont("Helvetica", 9)
    if quote.quote_number:
        c.drawString(LEFT_MARGIN, y, f"Invoice no. {quote.quote_number}")
    if quote.quote_date:
        c.drawString(LEFT_MARGIN, y - 5 * mm, f"Date: {quote.quote_date}")
    if quote.validity_date:
        c.drawString(LEFT_MARGIN, y - 10 * mm, f"Valid until: {quote.validity_date}")
    y -= 18 * mm

    # Client block
    if quote.client_name or quote.company or quote.address or quote.email:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(LEFT_MARGIN, y, "Bill to")
        c.setFont("Helvetica", 9)
        y -= 5 * mm
        if quote.client_name:
            c.drawString(LEFT_MARGIN, y, quote.client_name)
            y -= 5 * mm
        if quote.company:
            c.drawString(LEFT_MARGIN, y, quote.company)
            y -= 5 * mm
        if quote.address:
            c.drawString(LEFT_MARGIN, y, quote.address)
            y -= 5 * mm
        if quote.email:
            c.drawString(LEFT_MARGIN, y, quote.email)
            y -= 5 * mm
        y -= 8 * mm

    # Line items table (invoice-style)
    if quote.line_items:
        subtotal, tax_amount, total = compute_totals(quote)
        col_desc = LEFT_MARGIN
        col_qty = LEFT_MARGIN + 85 * mm
        col_unit = LEFT_MARGIN + 110 * mm
        col_amount = LEFT_MARGIN + 135 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_desc, y, "Description")
        c.drawString(col_qty, y, "Qty")
        c.drawString(col_unit, y, "Unit price")
        c.drawString(col_amount, y, "Amount")
        y -= 6 * mm
        c.setFont("Helvetica", 9)

        for item in quote.line_items:
            c.drawString(col_desc, y, (item.description or "-")[:40])
            c.drawString(col_qty, y, str(item.quantity))
            c.drawString(col_unit, y, _format_eur(item.unit_price))
            c.drawString(col_amount, y, _format_eur(item.amount))
            y -= 6 * mm

        y -= 4 * mm
        c.drawString(col_desc, y, f"Subtotal")
        c.drawString(col_amount, y, _format_eur(subtotal))
        y -= 5 * mm
        c.drawString(col_desc, y, f"VAT ({quote.tax_rate_percent:.0f}%)")
        c.drawString(col_amount, y, _format_eur(tax_amount))
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_desc, y, "Total")
        c.drawString(col_amount, y, _format_eur(total))
        y -= 12 * mm
    else:
        # Fallback: simple quote (title, amount, description)
        c.setFont("Helvetica", 11)
        c.drawString(LEFT_MARGIN, y, f"To: {quote.firstname} {quote.lastname} ({quote.email})")
        y -= 8 * mm
        c.drawString(LEFT_MARGIN, y, f"Title: {quote.title}")
        y -= 8 * mm
        c.drawString(LEFT_MARGIN, y, f"Amount: {quote.amount}")
        if quote.description:
            y -= 8 * mm
            c.drawString(LEFT_MARGIN, y, f"Description: {quote.description}")
        y -= 16 * mm

    # Signature line with Smart Anchor (invisible text so Subnoto can detect it)
    sig_y = 50 * mm
    c.setFont("Helvetica", 10)
    c.drawString(LEFT_MARGIN, sig_y + 8 * mm, "Signature:")
    anchor_text = _smart_anchor(quote.email)
    c.setFillColorRGB(1, 1, 1)  # white so not visible on white background
    c.setFont("Helvetica", 8)
    c.drawString(LEFT_MARGIN, sig_y - 1 * mm, anchor_text)
    c.setFillColorRGB(0, 0, 0)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
