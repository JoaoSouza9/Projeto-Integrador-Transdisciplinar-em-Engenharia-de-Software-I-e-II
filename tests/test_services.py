from decimal import Decimal

import pytest

from app.services.frete import calcular_frete
from app.services.pagamento import DadosPagamentoInvalidos, luhn_valido, processar


@pytest.mark.parametrize("subtotal,esperado", [
    ("0", "0.00"), ("30.00", "10.00"), ("119.99", "10.00"), ("120.00", "0.00"), ("300", "0.00")])
def test_frete(subtotal, esperado):
    assert calcular_frete(Decimal(subtotal)) == Decimal(esperado)


def test_luhn():
    assert luhn_valido("4111 1111 1111 1111")
    assert not luhn_valido("4111 1111 1111 1112")
    assert not luhn_valido("123")


def test_pix_e_dinheiro():
    assert processar("PIX", Decimal("10"))[0] == "APROVADO"
    assert processar("DINHEIRO", Decimal("10"))[0] == "PENDENTE"


def test_cartao_aprovado_recusado_e_invalido():
    ok = {"numero": "4111111111111111", "nome": "Maria", "cvv": "123"}
    assert processar("CARTAO", Decimal("10"), ok)[0] == "APROVADO"
    recusa = dict(ok, numero="4000000000000002")
    assert processar("CARTAO", Decimal("10"), recusa)[0] == "RECUSADO"
    with pytest.raises(DadosPagamentoInvalidos):
        processar("CARTAO", Decimal("10"), dict(ok, cvv="1"))
    with pytest.raises(DadosPagamentoInvalidos):
        processar("BOLETO", Decimal("10"))
