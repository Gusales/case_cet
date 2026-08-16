from decimal import Decimal

import pytest

from src.services.cet_rate_solver import CetRateSolver
from src.services.cet_service import CetService

pytestmark = pytest.mark.unit


@pytest.fixture
def service() -> CetService:
    return CetService()


class TestCalculaPrincipal:
    def test_deve_somar_iof_e_tarifa_ao_valor_solicitado(self, service):
        resultado = service.calcula_principal(
            valor_solicitado=Decimal("10000"),
            iof=Decimal("0.0446070"),
            tarifa_cadastrada=Decimal("150")
        )
        assert resultado == Decimal("10596.0700000")

    def test_deve_devolver_o_proprio_valor_sem_iof_e_sem_tarifa(self, service):
        resultado = service.calcula_principal(
            valor_solicitado=Decimal("10000"),
            iof=Decimal("0"),
            tarifa_cadastrada=Decimal("0")
        )
        assert resultado == Decimal("10000")

    def test_deve_aplicar_o_iof_sobre_o_solicitado_e_nao_sobre_a_tarifa(self, service):
        # Persona 1. A tarifa entra depois do IOF; se entrasse antes, daria 831,43.
        resultado = service.calcula_principal(
            valor_solicitado=Decimal("800"),
            iof=Decimal("0.0239240"),
            tarifa_cadastrada=Decimal("12")
        )
        assert resultado == Decimal("831.1392000")


class TestCalculaPmt:
    def test_deve_seguir_a_tabela_price(self, service, assert_decimal_proximo):
        pmt = service.calcula_pmt(
            principal=Decimal("10596.0700000"), taxa_mensal=Decimal("0.018"), prazo=36
        )
        assert_decimal_proximo(pmt, Decimal("402.4793410691311657794299916"))

    def test_deve_dividir_o_principal_pelo_prazo_quando_a_taxa_e_zero(self, service):
        pmt = service.calcula_pmt(
            principal=Decimal("1200"), taxa_mensal=Decimal("0"), prazo=12
        )
        assert pmt == Decimal("100")

    def test_deve_emitir_warning_quando_a_taxa_e_zero(self, service, caplog):
        service.calcula_pmt(Decimal("1200"), Decimal("0"), 12)

        assert "Taxa mensal igual a zero" in caplog.text
        assert any(registro.levelname == "WARNING" for registro in caplog.records)

    def test_deve_cobrar_principal_mais_juros_quando_o_prazo_e_de_uma_parcela(
            self, service, assert_decimal_proximo
    ):
        # Com n=1 a Tabela Price se reduz a PMT = principal * (1 + i).
        pmt = service.calcula_pmt(
            principal=Decimal("1000"), taxa_mensal=Decimal("0.05"), prazo=1
        )
        assert_decimal_proximo(pmt, Decimal("1050"))

    def test_deve_reduzir_a_parcela_conforme_o_prazo_aumenta(self, service):
        curto = service.calcula_pmt(Decimal("10596.07"), Decimal("0.018"), 12)
        longo = service.calcula_pmt(Decimal("10596.07"), Decimal("0.018"), 36)
        assert longo < curto


class TestCalculaCet:
    def test_deve_retornar_todas_as_chaves_do_dto(self, service, dados_validos):
        resultado = service.calcula_cet(dados_validos)

        assert set(resultado.keys()) == {
            "cet_anual",
            "cet_mensal",
            "pmt",
            "principal_financiado",
            "valor_total_pago"
        }

    def test_deve_calcular_o_cet_da_persona_de_referencia(
            self, service, dados_validos, assert_decimal_proximo
    ):
        resultado = service.calcula_cet(dados_validos)

        assert resultado["principal_financiado"] == Decimal("10596.0700000")
        assert_decimal_proximo(resultado["pmt"], Decimal("402.4793410691311657794299916"))
        assert_decimal_proximo(resultado["cet_mensal"], Decimal("0.02159987048441704357694040418"))
        assert_decimal_proximo(resultado["cet_anual"], Decimal("0.292319657271635223508178191"))

    def test_deve_produzir_um_cet_maior_que_a_taxa_nominal(self, service, dados_validos):
        resultado = service.calcula_cet(dados_validos)
        assert resultado["cet_mensal"] > dados_validos["taxa_juros_mensal"]

    def test_deve_calcular_o_valor_total_pago_como_pmt_vezes_prazo(self, service, dados_validos):
        resultado = service.calcula_cet(dados_validos)
        assert resultado["valor_total_pago"] == resultado["pmt"] * dados_validos["prazo"]

    def test_deve_capitalizar_o_cet_mensal_para_obter_o_anual(
            self, service, dados_validos, assert_decimal_proximo
    ):
        resultado = service.calcula_cet(dados_validos)
        esperado = (1 + resultado["cet_mensal"]) ** 12 - 1
        assert_decimal_proximo(resultado["cet_anual"], esperado)

    def test_deve_cobrar_cet_mesmo_com_taxa_de_juros_zerada(self, service, dados_validos):
        # Sem juros, mas com IOF e tarifa, o custo efetivo continua positivo.
        resultado = service.calcula_cet({**dados_validos, "taxa_juros_mensal": Decimal("0")})
        assert resultado["cet_mensal"] > 0

    def test_deve_propagar_o_erro_do_solver_e_registrar_no_log(
            self, service, dados_validos, monkeypatch, caplog
    ):
        def resolver_quebrado(self, chute_inicial):
            raise ValueError("Não há raiz no intervalo esperado (f(0) <= 0).")

        monkeypatch.setattr(CetRateSolver, "resolver", resolver_quebrado)

        with pytest.raises(ValueError, match="Não há raiz"):
            service.calcula_cet(dados_validos)

        assert "Falha ao resolver a taxa 'r' do CET" in caplog.text
        assert any(registro.levelname == "ERROR" for registro in caplog.records)

    def test_deve_repassar_a_taxa_contratada_como_chute_inicial_do_solver(
            self, service, dados_validos, monkeypatch
    ):
        chutes_recebidos = []
        resolver_original = CetRateSolver.resolver

        def resolver_espiao(self, chute_inicial):
            chutes_recebidos.append(chute_inicial)
            return resolver_original(self, chute_inicial)

        monkeypatch.setattr(CetRateSolver, "resolver", resolver_espiao)
        service.calcula_cet(dados_validos)

        assert chutes_recebidos == [dados_validos["taxa_juros_mensal"]]
