from decimal import Decimal

import pytest

from src.validators.user_input_validator import UserInputValidator

pytestmark = pytest.mark.unit


@pytest.fixture
def validator() -> UserInputValidator:
    return UserInputValidator()


@pytest.mark.parametrize(
    "persona",
    ["persona_compra_urgente", "persona_aposentada_10k", "persona_aposentada_15k"],
)
def test_deve_aceitar_os_dados_de_todas_as_personas(validator, request, persona):
    dados = request.getfixturevalue(persona)
    assert validator.validate(dados) is None


@pytest.mark.parametrize(
    "campo, valor, mensagem",
    [
        ("valor_solicitado", Decimal("0"), "Valor solicitado deve ser positivo."),
        ("valor_solicitado", Decimal("-1"), "Valor solicitado deve ser positivo."),
        ("taxa_juros_mensal", Decimal("-0.01"), "Taxa de juros não pode ser negativa."),
        ("prazo", 0, "Prazo deve ser maior que zero."),
        ("prazo", -5, "Prazo deve ser maior que zero."),
        ("iof", Decimal("-0.01"), "IOF e tarifa não podem ser negativos."),
        ("tarifa_cadastrada", Decimal("-1"), "IOF e tarifa não podem ser negativos."),
    ],
)
def test_deve_recusar_campos_invalidos(validator, dados_validos, campo, valor, mensagem):
    dados_validos[campo] = valor

    with pytest.raises(ValueError) as erro:
        validator.validate(dados_validos)

    assert str(erro.value) == mensagem


@pytest.mark.parametrize(
    "campo, valor, motivo",
    [
        ("taxa_juros_mensal", Decimal("0"), "empréstimo sem juros é válido"),
        ("prazo", 1, "parcela única é válida"),
        ("iof", Decimal("0"), "operação isenta de IOF é válida"),
        ("tarifa_cadastrada", Decimal("0"), "banco que não cobra tarifa é válido"),
    ],
)
def test_deve_aceitar_as_fronteiras(validator, dados_validos, campo, valor, motivo):
    dados_validos[campo] = valor
    assert validator.validate(dados_validos) is None, motivo


def test_deve_validar_na_ordem_declarada(validator, dados_validos):
    dados_validos["valor_solicitado"] = Decimal("-1")
    dados_validos["prazo"] = 0

    with pytest.raises(ValueError, match="Valor solicitado deve ser positivo."):
        validator.validate(dados_validos)


def test_deve_registrar_o_erro_no_log(validator, dados_validos, caplog):
    dados_validos["prazo"] = 0

    with pytest.raises(ValueError):
        validator.validate(dados_validos)

    assert "Prazo inválido" in caplog.text
    assert any(registro.levelname == "ERROR" for registro in caplog.records)


def test_deve_registrar_o_sucesso_no_log(validator, dados_validos, caplog):
    validator.validate(dados_validos)
    assert "Dados validados com sucesso." in caplog.text
