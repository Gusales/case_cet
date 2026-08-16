"""
Testes das personas descritas em docs/PERSONAS.md.

Cada persona é um caso de uso completo, com entradas e saídas documentadas.
Aqui a tabela de saídas esperadas vira assert: se o cálculo mudar, a
documentação fica desatualizada e o teste avisa.

Os valores esperados vêm de docs/PERSONAS.md, onde cada um está
derivado passo a passo. Duas entradas não são arbitrárias:

    IOF     — alíquota da modalidade de crédito (PERSONAS.md, seção 2.2):
              Persona 1, rotativo, 6 meses   →  2,3924%
              Persona 2, consignado, 36 meses →  4,4607%

    Tarifa  — 1,5% do valor solicitado, em todas as personas:
              R$ 800 → R$ 12    R$ 10.000 → R$ 150    R$ 15.000 → R$ 225

Como IOF e tarifa são ambos proporcionais ao valor solicitado, o CET passa a
ser **independente do valor pedido** — ele depende só da taxa contratada e do
prazo. Essa é a propriedade que os testes de insight guardam abaixo.
"""

from decimal import Decimal

import pytest

from src.services.cet_service import CetService

pytestmark = [pytest.mark.e2e, pytest.mark.persona]


@pytest.fixture
def service() -> CetService:
    return CetService()


class TestPersona1CompraUrgente:
    """
    R$ 800, 8% a.m., 6 meses, IOF 2,3924% (rotativo), tarifa R$ 12 (1,5%).

    Compra de valor baixo sob pressão de tempo. A urgência tira dela o tempo de
    comparar ofertas — e o que ela não compara é justamente o custo real, que
    fica acima da taxa anunciada.
    """

    def test_usa_o_iof_do_rotativo_do_cartao(self, persona_compra_urgente):
        # 0,38% + (0,01118% × 180 dias) = 2,3924%
        assert persona_compra_urgente["iof"] == Decimal("0.0239240")

    def test_usa_tarifa_proporcional_ao_valor_solicitado(self, persona_compra_urgente):
        # 1,5% de R$ 800 = R$ 12,00
        valor = persona_compra_urgente["valor_solicitado"]
        assert persona_compra_urgente["tarifa_cadastrada"] == valor * Decimal("0.015")

    def test_saidas_documentadas(
            self, service, persona_compra_urgente, assert_reais, assert_percentual
    ):
        resultado = service.calcula_cet(persona_compra_urgente)

        assert_reais(resultado["principal_financiado"], "831.14")
        assert_reais(resultado["pmt"], "179.79")
        assert_reais(resultado["valor_total_pago"], "1078.73")
        assert_percentual(resultado["cet_mensal"], "9.27")
        assert_percentual(resultado["cet_anual"], "189.83")

    def test_principal_e_o_valor_solicitado_mais_iof_e_tarifa(
            self, service, persona_compra_urgente
    ):
        # 800 + (800 × 0,023924) + 12 = 831,1392
        resultado = service.calcula_cet(persona_compra_urgente)
        assert resultado["principal_financiado"] == Decimal("831.1392000")

    def test_o_custo_real_supera_a_taxa_anunciada(self, service, persona_compra_urgente):
        """
        O insight da persona: ela contrata "8% ao mês" e paga 9,27% — quase 16%
        a mais do que o número que a fez decidir. É essa diferença que a pressa
        impede de enxergar.
        """
        resultado = service.calcula_cet(persona_compra_urgente)

        taxa_contratada = persona_compra_urgente["taxa_juros_mensal"]
        assert resultado["cet_mensal"] > taxa_contratada * Decimal("1.10")
        assert resultado["cet_mensal"] < taxa_contratada * Decimal("1.25")

    def test_o_iof_pesa_mais_que_a_tarifa(self, service, persona_compra_urgente):
        """
        Com a tarifa proporcional, o maior custo acessório deixa de ser ela e
        passa a ser o imposto: R$ 19,14 de IOF contra R$ 12,00 de tarifa.
        """
        valor = persona_compra_urgente["valor_solicitado"]
        custo_iof = valor * persona_compra_urgente["iof"]

        assert custo_iof > persona_compra_urgente["tarifa_cadastrada"]

    def test_urgencia_nao_muda_a_conta_apenas_a_percepcao(
            self, service, persona_compra_urgente
    ):
        """
        A urgência é contexto humano, não entrada do cálculo. O que o teste
        garante é que o CET expõe o custo que a pressa esconderia: a cliente
        paga R$ 278,73 a mais do que os R$ 800 que pediu — 34,8% em 6 meses.
        """
        resultado = service.calcula_cet(persona_compra_urgente)
        valor = persona_compra_urgente["valor_solicitado"]

        custo_total = resultado["valor_total_pago"] - valor
        assert custo_total > valor * Decimal("0.30")

    def test_prazo_maior_reduz_o_cet_mesmo_com_iof_maior(
            self, service, persona_compra_urgente
    ):
        """
        Esticar o prazo de 6 para 24 meses derruba o CET mensal, mesmo com o IOF
        do prazo novo, que quase dobra (2,3924% → 4,4607%, já no teto de 365
        dias). Em compensação, o total pago quase dobra.
        """
        curto = service.calcula_cet(persona_compra_urgente)
        longo = service.calcula_cet(
            {**persona_compra_urgente, "prazo": 24, "iof": Decimal("0.0446070")}
        )

        assert longo["cet_mensal"] < curto["cet_mensal"]
        assert longo["valor_total_pago"] > curto["valor_total_pago"]


class TestPersona2AposentadaIndecisa:
    """
    R$ 10.000 vs R$ 15.000, ambos a 1,8% a.m. por 36 meses, IOF 4,4607%
    (consignado, com o componente diário no teto de 365 dias) e tarifa de 1,5%
    do valor solicitado.

    O insight: com todos os custos proporcionais, o CET é **exatamente o mesmo**
    nos dois cenários. A dúvida "peço 10 ou 15 mil?" não se resolve olhando o
    CET — ele não distingue as opções. Resolve-se pela parcela que cabe no
    orçamento.
    """

    def test_usa_o_iof_do_consignado_com_o_teto_de_365_dias(
            self, persona_aposentada_10k, persona_aposentada_15k
    ):
        # 1.080 dias de operação, mas o componente diário para em 365:
        # 0,38% + (0,01118% × 365) = 4,4607%
        assert persona_aposentada_10k["iof"] == Decimal("0.0446070")
        assert persona_aposentada_15k["iof"] == persona_aposentada_10k["iof"]

    def test_usa_tarifa_proporcional_nos_dois_cenarios(
            self, persona_aposentada_10k, persona_aposentada_15k
    ):
        for persona in (persona_aposentada_10k, persona_aposentada_15k):
            esperado = persona["valor_solicitado"] * Decimal("0.015")
            assert persona["tarifa_cadastrada"] == esperado

    def test_cenario_a_saidas_documentadas(
            self, service, persona_aposentada_10k, assert_reais, assert_percentual
    ):
        resultado = service.calcula_cet(persona_aposentada_10k)

        assert_reais(resultado["principal_financiado"], "10596.07")
        assert_reais(resultado["pmt"], "402.48")
        assert_reais(resultado["valor_total_pago"], "14489.26")
        assert_percentual(resultado["cet_mensal"], "2.16")
        assert_percentual(resultado["cet_anual"], "29.23")

    def test_cenario_b_saidas_documentadas(
            self, service, persona_aposentada_15k, assert_reais, assert_percentual
    ):
        resultado = service.calcula_cet(persona_aposentada_15k)

        assert_reais(resultado["principal_financiado"], "15894.11")
        assert_reais(resultado["pmt"], "603.72")
        assert_reais(resultado["valor_total_pago"], "21733.88")
        assert_percentual(resultado["cet_mensal"], "2.16")
        assert_percentual(resultado["cet_anual"], "29.23")

    def test_pedir_mais_aumenta_a_parcela(
            self, service, persona_aposentada_10k, persona_aposentada_15k
    ):
        # A parte da decisão que continua real: R$ 402,48 contra R$ 603,72.
        cenario_a = service.calcula_cet(persona_aposentada_10k)
        cenario_b = service.calcula_cet(persona_aposentada_15k)

        assert cenario_b["pmt"] > cenario_a["pmt"]
        assert cenario_b["valor_total_pago"] > cenario_a["valor_total_pago"]

    def test_o_cet_nao_distingue_os_dois_cenarios(
            self, service, persona_aposentada_10k, persona_aposentada_15k
    ):
        """
        O insight da persona, e o teste mais importante deste arquivo: com IOF e
        tarifa proporcionais ao valor solicitado, o CET é idêntico nos dois
        cenários. Pedir R$ 5.000 a mais não muda o custo percentual em nada.
        """
        cenario_a = service.calcula_cet(persona_aposentada_10k)
        cenario_b = service.calcula_cet(persona_aposentada_15k)

        assert abs(cenario_b["cet_mensal"] - cenario_a["cet_mensal"]) < Decimal("1e-9")
        assert abs(cenario_b["cet_anual"] - cenario_a["cet_anual"]) < Decimal("1e-9")

    def test_o_cet_independe_do_valor_para_qualquer_montante(
            self, service, persona_aposentada_10k
    ):
        """
        Generalização do insight: a propriedade não vale só para 10k e 15k.
        Enquanto todo custo for proporcional, o CET é o mesmo para qualquer
        valor solicitado — inclusive um fora da faixa que ela considera.
        """
        referencia = service.calcula_cet(persona_aposentada_10k)

        for valor in [Decimal("2000"), Decimal("50000"), Decimal("120000")]:
            resultado = service.calcula_cet({
                **persona_aposentada_10k,
                "valor_solicitado": valor,
                "tarifa_cadastrada": valor * Decimal("0.015")
            })
            assert abs(resultado["cet_mensal"] - referencia["cet_mensal"]) < Decimal("1e-9"), (
                f"CET deveria ser o mesmo para R$ {valor}"
            )

    def test_so_uma_tarifa_fixa_faria_o_valor_importar(
            self, service, persona_aposentada_10k, persona_aposentada_15k
    ):
        """
        Contraprova, e registro do que mudou: se a tarifa fosse um valor fixo em
        vez de proporcional, o cenário maior passaria a ter CET menor — porque a
        tarifa se diluiria. É a tarifa fixa, e nada mais, que faz o valor pesar.
        """
        fixa_a = service.calcula_cet(
            {**persona_aposentada_10k, "tarifa_cadastrada": Decimal("150")}
        )
        fixa_b = service.calcula_cet(
            {**persona_aposentada_15k, "tarifa_cadastrada": Decimal("150")}
        )

        assert fixa_b["cet_anual"] < fixa_a["cet_anual"]

    def test_a_decisao_se_resolve_pela_parcela(
            self, service, persona_aposentada_10k, persona_aposentada_15k
    ):
        """
        Consequência prática para a persona: como o CET empata, o que separa as
        duas opções é o quanto a parcela cresce — 50% a mais, na mesma proporção
        do valor pedido.
        """
        cenario_a = service.calcula_cet(persona_aposentada_10k)
        cenario_b = service.calcula_cet(persona_aposentada_15k)

        proporcao = cenario_b["pmt"] / cenario_a["pmt"]
        assert abs(proporcao - Decimal("1.5")) < Decimal("1e-9")


class TestComparacaoEntrePersonas:
    """O contraste entre as duas personas é a mensagem do desafio."""

    def test_o_que_encarece_o_credito_e_a_taxa_e_o_prazo(
            self, service, persona_compra_urgente, persona_aposentada_10k
    ):
        """
        Com custos proporcionais dos dois lados, o valor solicitado sai da conta
        e sobra o que de fato importa: a Persona 1 paga 4,3× mais caro que a
        Persona 2 porque contratou 8% a.m., não porque pediu pouco.
        """
        pequeno = service.calcula_cet(persona_compra_urgente)
        grande = service.calcula_cet(persona_aposentada_10k)

        assert pequeno["cet_mensal"] > grande["cet_mensal"] * 4

    def test_o_credito_mais_barato_paga_o_iof_mais_caro(
            self, persona_compra_urgente, persona_aposentada_10k
    ):
        """
        Contra-senso aparente da tabela de alíquotas: o consignado é o crédito
        mais barato em juros, mas tem o IOF maior — porque o componente diário
        remunera tempo de exposição, e a aposentada fica 3 anos devendo.
        """
        assert persona_aposentada_10k["taxa_juros_mensal"] < persona_compra_urgente["taxa_juros_mensal"]
        assert persona_aposentada_10k["iof"] > persona_compra_urgente["iof"]

    @pytest.mark.parametrize(
        "persona, taxa_contratada, iof_esperado, tarifa_esperada",
        [
            ("persona_compra_urgente", Decimal("0.08"), Decimal("0.0239240"), Decimal("12")),
            ("persona_aposentada_10k", Decimal("0.018"), Decimal("0.0446070"), Decimal("150")),
            ("persona_aposentada_15k", Decimal("0.018"), Decimal("0.0446070"), Decimal("225")),
        ],
    )
    def test_cet_sempre_supera_a_taxa_contratada(
            self, service, request, persona, taxa_contratada, iof_esperado, tarifa_esperada
    ):
        """
        Invariante de negócio válido para toda persona: o CET embute IOF e
        tarifa, então nunca pode ser menor que a taxa nominal do contrato.
        """
        dados = request.getfixturevalue(persona)
        resultado = service.calcula_cet(dados)

        assert dados["taxa_juros_mensal"] == taxa_contratada
        assert dados["iof"] == iof_esperado
        assert dados["tarifa_cadastrada"] == tarifa_esperada
        assert resultado["cet_mensal"] > taxa_contratada
