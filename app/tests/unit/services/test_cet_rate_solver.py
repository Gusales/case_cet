from decimal import Decimal

import pytest

from src.services.cet_rate_solver import CetRateSolver

pytestmark = pytest.mark.unit

PMT_REFERENCIA = Decimal("402.4793410691311657794299916")
TAXA_CONTRATADA = Decimal("0.018")
CET_ESPERADO = Decimal("0.02159987048441704357694040418")


@pytest.fixture
def solver() -> CetRateSolver:
    return CetRateSolver(
        pmt=PMT_REFERENCIA, valor_solicitado=Decimal("10000"), prazo=36
    )


class TestFuncaoObjetivo:
    def test_f_em_zero_deve_ser_o_total_pago_menos_o_emprestado(
            self, solver, assert_decimal_proximo
    ):
        esperado = PMT_REFERENCIA * 36 - Decimal("10000")
        assert_decimal_proximo(solver.f(Decimal("0")), esperado)

    def test_f_deve_ser_decrescente(self, solver):
        assert solver.f(Decimal("0")) > solver.f(Decimal("0.05")) > solver.f(Decimal("10"))

    def test_f_deve_trocar_de_sinal_dentro_do_intervalo_de_busca(self, solver):
        assert solver.f(Decimal("0")) > 0
        assert solver.f(Decimal("10")) < 0

    def test_f_deve_zerar_na_taxa_do_cet(self, solver):
        assert abs(solver.f(CET_ESPERADO)) < solver.tolerancia

    @pytest.mark.parametrize("r", ["0", "0.02", "0.5", "5"])
    def test_derivada_deve_ser_sempre_negativa(self, solver, r):
        assert solver.f_linha(Decimal(r)) < 0


class TestCandidatoValido:
    @pytest.mark.parametrize(
        "candidato, esperado, motivo",
        [
            (Decimal("0.5"), True, "dentro do intervalo"),
            (None, False, "passo de Newton não pôde ser calculado"),
            (Decimal("-2"), False, "deixaria (1 + r) <= 0"),
            (Decimal("-1"), False, "fronteira onde (1 + r) == 0"),
            (Decimal("20"), False, "acima do limite superior"),
            (Decimal("0"), False, "igual ao limite inferior (exclusivo)"),
            (Decimal("10"), False, "igual ao limite superior (exclusivo)"),
        ],
    )
    def test_deve_validar_o_candidato(self, solver, candidato, esperado, motivo):
        resultado = solver._candidato_valido(candidato, Decimal("0"), Decimal("10"))
        assert resultado is esperado, motivo


class TestResolver:
    def test_deve_convergir_dentro_da_tolerancia(self, solver):
        resultado = solver.resolver(chute_inicial=TAXA_CONTRATADA)
        assert resultado["erro_final"] < solver.tolerancia

    def test_deve_encontrar_a_taxa_esperada(self, solver, assert_decimal_proximo):
        resultado = solver.resolver(chute_inicial=TAXA_CONTRATADA)
        assert_decimal_proximo(resultado["r"], CET_ESPERADO)

    def test_o_r_encontrado_deve_zerar_a_funcao(self, solver):
        resultado = solver.resolver(chute_inicial=TAXA_CONTRATADA)
        assert abs(solver.f(resultado["r"])) < solver.tolerancia

    def test_deve_convergir_em_poucas_iteracoes_com_bom_chute(self, solver):
        resultado = solver.resolver(chute_inicial=TAXA_CONTRATADA)
        # Observado: 4 iterações, 0 fallbacks. A folga evita um teste frágil.
        assert resultado["iteracoes"] <= 10
        assert resultado["usos_fallback"] == 0

    def test_deve_cair_para_a_bisseccao_com_chute_ruim(self, solver):
        # Com chute 5 (500% a.m.) a derivada é quase nula e o passo de Newton
        # sai do intervalo — observado: 13 iterações e 7 quedas para bissecção.
        resultado = solver.resolver(chute_inicial=Decimal("5"))

        assert resultado["usos_fallback"] > 0
        assert resultado["erro_final"] < solver.tolerancia

    def test_deve_convergir_para_a_mesma_raiz_independente_do_chute(
            self, solver, assert_decimal_proximo
    ):
        de_bom_chute = solver.resolver(chute_inicial=TAXA_CONTRATADA)["r"]
        de_chute_ruim = solver.resolver(chute_inicial=Decimal("5"))["r"]
        assert_decimal_proximo(de_chute_ruim, de_bom_chute, Decimal("1e-6"))

    def test_deve_avisar_quando_nao_converge(self, caplog):
        solver = CetRateSolver(
            pmt=PMT_REFERENCIA,
            valor_solicitado=Decimal("10000"),
            prazo=36,
            max_iteracoes=1
        )
        resultado = solver.resolver(chute_inicial=TAXA_CONTRATADA)

        assert resultado["iteracoes"] == 1
        assert resultado["erro_final"] > solver.tolerancia
        assert "terminou sem convergir" in caplog.text
        assert any(registro.levelname == "WARNING" for registro in caplog.records)


class TestPersonaComprarUrgente:
    @pytest.fixture
    def solver_urgente(self) -> CetRateSolver:
        return CetRateSolver(
            pmt=Decimal("179.7881970580702393743198975"),
            valor_solicitado=Decimal("800"),
            prazo=6
        )

    def test_deve_encontrar_a_taxa_da_persona(self, solver_urgente, assert_decimal_proximo):
        resultado = solver_urgente.resolver(chute_inicial=Decimal("0.08"))
        assert_decimal_proximo(resultado["r"], Decimal("0.09272690729579978635521677383"))

    def test_deve_convergir_mesmo_com_a_raiz_longe_do_chute(self, solver_urgente):
        # O chute (8%) parte de baixo da raiz (9,27%) e sobe até ela.
        resultado = solver_urgente.resolver(chute_inicial=Decimal("0.08"))
        assert resultado["erro_final"] < solver_urgente.tolerancia


class TestIntervaloInvalido:
    def test_deve_falhar_quando_nao_ha_raiz(self):
        solver = CetRateSolver(
            pmt=Decimal("100"), valor_solicitado=Decimal("10000"), prazo=10
        )
        with pytest.raises(ValueError, match=r"Não há raiz no intervalo esperado"):
            solver.resolver(chute_inicial=Decimal("0.02"))

    def test_deve_falhar_quando_a_raiz_esta_acima_do_limite(self):
        solver = CetRateSolver(
            pmt=Decimal("10000"), valor_solicitado=Decimal("100"), prazo=24
        )
        with pytest.raises(ValueError, match=r"Intervalo de busca insuficiente"):
            solver.resolver(chute_inicial=Decimal("0.02"))
