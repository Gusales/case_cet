import logging
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pytest

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from tests.stubs.cet_request_calculate_dto_stub import CetRequestCalculateDtoStub

# ---------------------------------------------------------------------------
# Personas (docs/PERSONAS.md)
#
# As taxas entram como fração, não como percentual: o main.py divide por 100 o
# que o usuário digita, então "8% a.m." chega no service como Decimal("0.08").
#
# O IOF sai da modalidade de crédito de cada persona e depende do prazo, porque
# tem um componente diário. A tabela de alíquotas e as derivações estão em
# PERSONAS.md, seção 2.2; a tarifa (1,5% do valor solicitado), na seção 2.3.
# ---------------------------------------------------------------------------

@pytest.fixture
def persona_compra_urgente() -> CetRequestCalculateDto:
    """
    Persona 1 — R$ 800, 8% a.m., 6 meses, rotativo do cartão.
    Valor baixo, taxa alta e prazo curto.

    IOF do rotativo: 0,38% + 0,01118% ao dia × 180 dias = 2,3924%.
    Tarifa: 1,5% do valor solicitado = R$ 12,00.
    """
    return CetRequestCalculateDtoStub().entity(
        valor_solicitado=Decimal("800"),
        taxa_juros_mensal=Decimal("0.08"),
        prazo=6,
        iof=Decimal("0.0239240"),
        tarifa_cadastrada=Decimal("12")
    )


@pytest.fixture
def persona_aposentada_10k() -> CetRequestCalculateDto:
    """
    Persona 2, cenário A — R$ 10.000, 1,8% a.m., 36 meses, consignado
    (IOF 4,4607%, já com o teto de 365 dias). É o default do stub.

    Tarifa: 1,5% do valor solicitado = R$ 150,00.
    """
    return CetRequestCalculateDtoStub().entity()


@pytest.fixture
def persona_aposentada_15k() -> CetRequestCalculateDto:
    """
    Persona 2, cenário B — R$ 15.000, mesmas condições do cenário A.

    Tarifa: 1,5% do valor solicitado = R$ 225,00. Por ser proporcional, ela
    não distingue este cenário do A — os dois têm o mesmo CET.
    """
    return CetRequestCalculateDtoStub().entity(
        valor_solicitado=Decimal("15000"),
        tarifa_cadastrada=Decimal("225")
    )


@pytest.fixture
def dados_validos(persona_aposentada_10k) -> CetRequestCalculateDto:
    """Entrada válida genérica; usa o cenário A da Persona 2 como referência."""
    return persona_aposentada_10k


@pytest.fixture
def root_project() -> Path:
    return Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Comparadores
# ---------------------------------------------------------------------------

@pytest.fixture
def assert_decimal_proximo():
    """
    Compara Decimals por tolerância.

    O solver chega no resultado por caminhos ligeiramente diferentes conforme o
    chute inicial, então comparar com `==` seria frágil.
    """

    def _assert(obtido: Decimal, esperado: Decimal, tolerancia: Decimal = Decimal("1e-9")):
        diferenca = abs(Decimal(obtido) - Decimal(esperado))
        assert diferenca <= tolerancia, (
            f"esperado {esperado}, obtido {obtido} (diferença {diferenca} > {tolerancia})"
        )

    return _assert


@pytest.fixture
def assert_reais():
    """Compara valores monetários no arredondamento de 2 casas do PERSONAS.md."""

    def _assert(obtido: Decimal, esperado: str):
        arredondado = Decimal(obtido).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert arredondado == Decimal(esperado), (
            f"esperado R$ {esperado}, obtido R$ {arredondado} (valor cheio: {obtido})"
        )

    return _assert


@pytest.fixture
def assert_percentual():
    """Converte a fração para percentual e compara com 2 casas, como no PERSONAS.md."""

    def _assert(obtido: Decimal, esperado: str):
        arredondado = (Decimal(obtido) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert arredondado == Decimal(esperado), (
            f"esperado {esperado}%, obtido {arredondado}% (valor cheio: {obtido})"
        )

    return _assert


# ---------------------------------------------------------------------------
# Isolamento de estado global
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_logger_level():
    """
    `src.utils.logger.set_level()` mexe no root logger — estado global. Sem
    restaurar, um teste que liga o DEBUG deixaria os seguintes verbosos.
    """
    level_original = logging.root.level
    level_logger = logging.getLogger("logger").level
    yield
    logging.root.setLevel(level_original)
    logging.getLogger("logger").setLevel(level_logger)
