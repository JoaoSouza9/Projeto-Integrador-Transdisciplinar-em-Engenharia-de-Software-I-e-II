from decimal import Decimal

FRETE_FIXO = Decimal("10.00")
FRETE_GRATIS_ACIMA = Decimal("120.00")


def calcular_frete(subtotal):
    """RN04: frete fixo de R$ 10,00; grátis para subtotal a partir de R$ 120,00."""
    subtotal = Decimal(subtotal)
    if subtotal <= 0 or subtotal >= FRETE_GRATIS_ACIMA:
        return Decimal("0.00")
    return FRETE_FIXO
