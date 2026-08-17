from decimal import Decimal

import pytest

from src.validators.http_request_validator import HttpRequestValidator

pytestmark = pytest.mark.unit

CORPO_VALIDO = {
    "valor_solicitado": 10000,
    "taxa_juros_mensal": 2.5,
    "prazo": 24,
    "iof": 0.38,
    "tarifa_cadastrada": 150
}


class TestConversao:
    def test_deve_converter_o_corpo_em_dto(self):
        dados = HttpRequestValidator(CORPO_VALIDO).validate()

        assert dados == {
            "valor_solicitado": Decimal("10000"),
            "taxa_juros_mensal": Decimal("0.025"),
            "prazo": 24,
            "iof": Decimal("0.0038"),
            "tarifa_cadastrada": Decimal("150")
        }

    def test_deve_dividir_por_cem_apenas_os_campos_percentuais(self):
        # Mesma convenção da CLI: taxa e IOF chegam em %, os demais em reais.
        dados = HttpRequestValidator(CORPO_VALIDO).validate()

        assert dados["taxa_juros_mensal"] == Decimal("0.025")
        assert dados["iof"] == Decimal("0.0038")
        assert dados["valor_solicitado"] == Decimal("10000")
        assert dados["tarifa_cadastrada"] == Decimal("150")

    def test_deve_aceitar_numeros_como_string(self):
        corpo = {campo: str(valor) for campo, valor in CORPO_VALIDO.items()}
        dados = HttpRequestValidator(corpo).validate()

        assert dados["valor_solicitado"] == Decimal("10000")
        assert dados["prazo"] == 24

    def test_deve_evitar_o_erro_binario_do_float(self):
        """
        `Decimal(0.38)` herda o erro do float e vira 0.38000000000000000444…
        Passando pela string, o valor decimal é preservado.
        """
        dados = HttpRequestValidator({**CORPO_VALIDO, "iof": 0.38}).validate()

        assert dados["iof"] == Decimal("0.0038")
        assert str(dados["iof"]) == "0.0038"

    def test_deve_ignorar_campos_extras(self):
        dados = HttpRequestValidator({**CORPO_VALIDO, "campo_extra": "ignorado"}).validate()
        assert "campo_extra" not in dados


class TestCorpoInvalido:
    @pytest.mark.parametrize(
        "corpo, motivo",
        [
            (None, "corpo ausente ou JSON malformado"),
            ([], "array no lugar de objeto"),
            ("texto", "string no lugar de objeto"),
            (42, "número no lugar de objeto"),
        ],
    )
    def test_deve_recusar_corpo_que_nao_e_objeto(self, corpo, motivo):
        with pytest.raises(ValueError, match="corpo da requisição"):
            HttpRequestValidator(corpo).validate(), motivo

    def test_deve_listar_todos_os_campos_ausentes(self):
        with pytest.raises(ValueError) as erro:
            HttpRequestValidator({"valor_solicitado": 10000, "prazo": 24}).validate()

        mensagem = str(erro.value)
        for campo in ["taxa_juros_mensal", "iof", "tarifa_cadastrada"]:
            assert campo in mensagem

    @pytest.mark.parametrize(
        "campo",
        ["valor_solicitado", "taxa_juros_mensal", "iof", "tarifa_cadastrada"],
    )
    def test_deve_recusar_valor_nao_numerico(self, campo):
        with pytest.raises(ValueError, match=f"'{campo}' deve ser um número"):
            HttpRequestValidator({**CORPO_VALIDO, campo: "abc"}).validate()

    @pytest.mark.parametrize("valor", [24.5, "abc", None, True])
    def test_deve_recusar_prazo_que_nao_e_inteiro(self, valor):
        with pytest.raises(ValueError, match="'prazo' deve ser um número inteiro"):
            HttpRequestValidator({**CORPO_VALIDO, "prazo": valor}).validate()

    def test_deve_aceitar_prazo_inteiro_expresso_como_float(self):
        # 24.0 é inteiro — recusar seria pedantismo com quem manda JSON.
        dados = HttpRequestValidator({**CORPO_VALIDO, "prazo": 24.0}).validate()
        assert dados["prazo"] == 24


class TestSeparacaoDeResponsabilidade:
    def test_nao_deve_aplicar_regra_de_negocio(self):
        """
        Valor zerado é inválido, mas quem recusa é o `UserInputValidator`.
        Aqui só se verifica que o transporte está bem formado — separar os dois
        é o que permite distinguir "JSON malformado" de "empréstimo inválido".
        """
        dados = HttpRequestValidator({**CORPO_VALIDO, "valor_solicitado": 0}).validate()
        assert dados["valor_solicitado"] == Decimal("0")

    def test_deve_registrar_o_sucesso_no_log(self, caplog):
        HttpRequestValidator(CORPO_VALIDO).validate()
        assert "Corpo da requisição validado com sucesso." in caplog.text

    def test_deve_registrar_o_erro_no_log(self, caplog):
        with pytest.raises(ValueError):
            HttpRequestValidator({}).validate()

        assert any(registro.levelname == "ERROR" for registro in caplog.records)
