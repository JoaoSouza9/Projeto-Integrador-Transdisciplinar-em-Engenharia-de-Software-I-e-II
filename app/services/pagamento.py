"""Gateway de pagamento SIMULADO (RN07/RN08). Dados de cartão nunca são armazenados."""
import re

FORMAS = {"PIX": "PIX", "CARTAO": "Cartão de crédito", "DINHEIRO": "Dinheiro na entrega"}
CARTAO_RECUSA_TESTE = "4000000000000002"  # número de teste que simula recusa


class DadosPagamentoInvalidos(Exception):
    pass


def luhn_valido(numero):
    digitos = [int(c) for c in numero if c.isdigit()]
    if len(digitos) < 13 or len(digitos) > 19:
        return False
    soma = 0
    for i, d in enumerate(reversed(digitos)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        soma += d
    return soma % 10 == 0


def processar(forma, valor, dados=None):
    """Retorna (status, mensagem). status ∈ APROVADO | PENDENTE | RECUSADO."""
    dados = dados or {}
    if forma not in FORMAS:
        raise DadosPagamentoInvalidos("Forma de pagamento inválida.")
    if forma == "PIX":
        return "APROVADO", "Pagamento via PIX confirmado."
    if forma == "DINHEIRO":
        return "PENDENTE", "Pagamento em dinheiro será feito na entrega."
    numero = re.sub(r"\D", "", dados.get("numero", ""))
    cvv = re.sub(r"\D", "", dados.get("cvv", ""))
    if not dados.get("nome", "").strip() or not luhn_valido(numero) or len(cvv) not in (3, 4):
        raise DadosPagamentoInvalidos("Dados do cartão inválidos. Confira número, nome e CVV.")
    if numero == CARTAO_RECUSA_TESTE:
        return "RECUSADO", "Cartão recusado pela operadora. Tente outra forma de pagamento."
    return "APROVADO", "Pagamento no cartão aprovado."
