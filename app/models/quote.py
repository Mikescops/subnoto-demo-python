"""Quote/Invoice data model for form and API."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LineItem:
    """Single line item for invoice: description, quantity, unit price; amount = quantity * unit_price."""

    description: str
    quantity: float
    unit_price: float

    @property
    def amount(self) -> float:
        return self.quantity * self.unit_price

    @classmethod
    def from_dict(cls, d: dict) -> "LineItem":
        return cls(
            description=(d.get("description") or "").strip(),
            quantity=float(d.get("quantity") or 0),
            unit_price=float(d.get("unitPrice") or d.get("unit_price") or 0),
        )


@dataclass
class QuoteData:
    """Quote/Invoice form/API payload: customer, line items, and signer."""

    email: str
    firstname: str
    lastname: str
    title: str
    amount: str
    description: Optional[str] = None
    # Invoice-style fields
    quote_number: str = ""
    quote_date: str = ""
    validity_date: str = ""
    client_name: str = ""
    company: str = ""
    address: str = ""
    line_items: list[LineItem] = field(default_factory=list)
    tax_rate_percent: float = 20.0

    @classmethod
    def from_json(cls, data: dict) -> "QuoteData":
        """Build from request JSON; apply defaults."""
        raw_items = data.get("lineItems") or data.get("line_items") or []
        if isinstance(raw_items, list):
            line_items = [LineItem.from_dict(item) if isinstance(item, dict) else LineItem("", 0, 0) for item in raw_items]
        else:
            line_items = []
        # If no line items but we have description/amount, use one line
        if not line_items and (data.get("description") or data.get("amount")):
            desc = (data.get("description") or "").strip() or "Services"
            try:
                amt = float(data.get("amount") or 0)
            except (TypeError, ValueError):
                amt = 0.0
            line_items = [LineItem(description=desc, quantity=1, unit_price=amt)] if amt or desc != "Services" else []

        return cls(
            email=(data.get("email") or "").strip(),
            firstname=(data.get("firstname") or "Demo").strip(),
            lastname=(data.get("lastname") or "Signer").strip(),
            title=(data.get("title") or "Invoice").strip(),
            amount=(data.get("amount") or "0").strip(),
            description=(data.get("description") or "").strip() or None,
            quote_number=(data.get("quoteNumber") or data.get("quote_number") or "").strip(),
            quote_date=(data.get("quoteDate") or data.get("quote_date") or "").strip(),
            validity_date=(data.get("validityDate") or data.get("validity_date") or "").strip(),
            client_name=(data.get("clientName") or data.get("client_name") or "").strip(),
            company=(data.get("company") or "").strip(),
            address=(data.get("address") or "").strip(),
            line_items=line_items,
            tax_rate_percent=float(data.get("taxRatePercent") or data.get("tax_rate_percent") or 20),
        )


def compute_totals(quote: QuoteData) -> tuple[float, float, float]:
    """Return (subtotal, tax_amount, total)."""
    subtotal = sum(item.amount for item in quote.line_items)
    tax = subtotal * (quote.tax_rate_percent / 100)
    return subtotal, tax, subtotal + tax
