import logging
from decimal import Decimal
from pathlib import Path

import pytest

from app.src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from tests.stubs.cet_request_calculate_dto_stub import CetRequestCalculateDtoStub

@pytest.fixture
def dados_validos() -> CetRequestCalculateDto:
    mock: CetRequestCalculateDto = CetRequestCalculateDtoStub()
    return mock


@pytest.fixture
def root_project() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def assert_decimal_proximo():
    def _assert(obtido: Decimal, esperado: Decimal, tolerancia: Decimal = Decimal("1e-9")):
        diferenca = abs(Decimal(obtido) - Decimal(esperado))
        assert diferenca <= tolerancia, (
            f"esperado {esperado}, obtido {obtido} (diferença {diferenca} > {tolerancia})"
        )

    return _assert


@pytest.fixture(autouse=True)
def reset_logger_level():
    level_original = logging.root.level
    level_logger = logging.getLogger("logger").level
    yield
    logging.root.setLevel(level_original)
    logging.getLogger("logger").setLevel(level_logger)