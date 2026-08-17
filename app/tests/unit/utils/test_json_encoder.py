import json
from decimal import Decimal

import pytest

from src.utils.json_encoder import DecimalEncoder

pytestmark = pytest.mark.unit


def test_deve_serializar_decimal_como_string():
    resultado = json.dumps({"pmt": Decimal("569.6398138287249351997965382")}, cls=DecimalEncoder)
    assert resultado == '{"pmt": "569.6398138287249351997965382"}'


def test_deve_preservar_a_precisao_completa():
    """
    O motivo de a saída ser string: `float` truncaria a precisão que o projeto
    inteiro trabalha para preservar.
    """
    original = Decimal("0.02669314049967152600841711547")

    serializado = json.dumps({"cet": original}, cls=DecimalEncoder)
    recuperado = Decimal(json.loads(serializado)["cet"])

    assert recuperado == original


def test_deve_preservar_zeros_a_direita():
    # 10188.0000 carrega a escala do cálculo; virar 10188.0 perderia informação.
    resultado = json.dumps({"principal": Decimal("10188.0000")}, cls=DecimalEncoder)
    assert resultado == '{"principal": "10188.0000"}'


def test_deve_serializar_dto_completo():
    resposta = {
        "principal_financiado": Decimal("10188.0000"),
        "pmt": Decimal("569.64"),
        "valor_total_pago": Decimal("13671.36"),
        "cet_mensal": Decimal("0.0266931404996715"),
        "cet_anual": Decimal("0.3717909244037562")
    }

    recuperado = json.loads(json.dumps({"data": resposta}, cls=DecimalEncoder))

    assert set(recuperado["data"].keys()) == set(resposta.keys())
    assert all(isinstance(valor, str) for valor in recuperado["data"].values())


def test_deve_delegar_tipos_conhecidos_ao_encoder_padrao():
    resultado = json.dumps({"a": 1, "b": "texto", "c": [1, 2], "d": None}, cls=DecimalEncoder)
    assert json.loads(resultado) == {"a": 1, "b": "texto", "c": [1, 2], "d": None}


def test_deve_falhar_em_tipo_nao_serializavel():
    # O encoder não pode virar um "aceita qualquer coisa": só Decimal é tratado.
    with pytest.raises(TypeError):
        json.dumps({"x": object()}, cls=DecimalEncoder)
