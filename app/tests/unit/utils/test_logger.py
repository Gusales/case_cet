import logging

import pytest

from src.utils.logger import ColoredFormatter, Logger, set_level

pytestmark = pytest.mark.unit


class Exemplo:
    def __init__(self):
        self._logger = Logger(self.__class__)

    def metodo_qualquer(self):
        self._logger.info("mensagem de teste")


def test_deve_prefixar_com_classe_e_metodo(caplog):
    Exemplo().metodo_qualquer()
    assert "[Exemplo.metodo_qualquer] - mensagem de teste" in caplog.text


def test_nao_deve_prefixar_quando_nao_recebe_classe(caplog):
    Logger().info("mensagem solta")

    assert "mensagem solta" in caplog.text
    assert "[" not in caplog.records[-1].getMessage()


def test_deve_exibir_o_debug_quando_o_nivel_e_ajustado(caplog):
    set_level(logging.DEBUG)
    with caplog.at_level(logging.DEBUG, logger="logger"):
        Logger(Exemplo).debug("detalhe interno")

    assert "detalhe interno" in caplog.text


def test_deve_ocultar_o_debug_no_nivel_padrao(caplog):
    set_level(logging.INFO)
    Logger(Exemplo).debug("nao deve aparecer")

    assert "nao deve aparecer" not in caplog.text


def test_deve_reaproveitar_o_mesmo_logger_subjacente():
    assert Logger(Exemplo).get_logger() is Logger().get_logger()
    assert Logger().get_logger().name == "logger"


class TestColoredFormatter:
    def test_deve_restaurar_o_record_apos_formatar(self):
        formatter = ColoredFormatter(fmt="%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="mensagem original",
            args=(),
            exc_info=None
        )

        formatado = formatter.format(record)

        assert "\033[32m" in formatado
        assert record.msg == "mensagem original"
        assert record.levelname == "INFO"

    @pytest.mark.parametrize(
        "nivel, cor",
        [
            (logging.DEBUG, "\033[37m"),
            (logging.INFO, "\033[32m"),
            (logging.WARNING, "\033[33m"),
            (logging.ERROR, "\033[31m"),
            (logging.CRITICAL, "\033[31;1m"),
        ],
    )
    def test_deve_usar_uma_cor_por_nivel(self, nivel, cor):
        formatter = ColoredFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="logger",
            level=nivel,
            pathname=__file__,
            lineno=1,
            msg="msg",
            args=(),
            exc_info=None
        )

        assert formatter.format(record).startswith(cor)
