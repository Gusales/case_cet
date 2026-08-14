from decimal import Decimal
from cet_rate_solver import CetRateSolver

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from src.dtos.cet_response_calculate_dto import CetResponseCalculateDto

class CetService:

    def calcula_pmt(self, principal: Decimal, taxa_mensal: Decimal, prazo: int) -> Decimal:
        if taxa_mensal == 0:
            return principal / prazo

        fator_comum = (1 + taxa_mensal) ** prazo
        return principal * (taxa_mensal * fator_comum) / (fator_comum - 1)

    def _valida_intervalo(self, r_candidato: Decimal, x: Decimal, y: Decimal) -> bool:
        if r_candidato is None:
            return False

        if r_candidato <= Decimal("-1"):
            return False

        if r_candidato <= x or r_candidato >= y:
            return False

        return True

    def calcula_principal(self, valor_solicitado: Decimal, iof: Decimal, tarifa_cadastrada: Decimal) -> Decimal:
        valor_iof = valor_solicitado * iof
        return valor_solicitado + valor_iof + tarifa_cadastrada

    def calcula_cet(self, dados: CetRequestCalculateDto) -> CetResponseCalculateDto:
        principal = self.calcula_principal(
            valor_solicitado=dados["valor_solicitado"],
            iof=dados["iof"],
            tarifa_cadastrada=dados["tarifa_cadastrada"]
        )

        pmt = self.calcula_pmt(
            principal=principal,
            taxa_mensal=dados["taxa_juros_mensal"],
            prazo=dados["prazo"]
        )

        valor_total_pago = pmt * dados["prazo"]

        rate_solver = CetRateSolver(
            pmt=pmt,
            valor_solicitado=dados["valor_solicitado"],
            prazo=dados["prazo"]
        )

        rate_resultado = rate_solver.resolver(chute_inicial=dados["taxa_juros_mensal"])

        cet_mensal = rate_resultado["r"]
        cet_anual = (1 + cet_mensal) ** 12 - 1

        resultado_final: CetResponseCalculateDto = {
            "cet_anual": cet_anual,
            "cet_mensal": cet_mensal,
            "pmt": pmt,
            "principal_financiado": principal,
            "valor_total_pago": valor_total_pago
        }

        return resultado_final