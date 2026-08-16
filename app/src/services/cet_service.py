from decimal import Decimal

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from src.dtos.cet_response_calculate_dto import CetResponseCalculateDto

from src.services.cet_rate_solver import CetRateSolver
from src.utils.logger import Logger

class CetService:
    def __init__(self):
        self._logger = Logger(self.__class__)

    def calcula_pmt(self, principal: Decimal, taxa_mensal: Decimal, prazo: int) -> Decimal:
        self._logger.info(f"Calculando o PMT com principal={principal}, taxa_mensal={taxa_mensal} e prazo={prazo}")

        if taxa_mensal == 0:
            self._logger.warning("Taxa mensal igual a zero, o PMT será apenas o principal dividido pelo prazo.")
            pmt_sem_juros = principal / prazo
            self._logger.info(f"O resultado do 'pmt' é {pmt_sem_juros}")
            return pmt_sem_juros

        self._logger.info("Calculando o fator comum da Tabela Price: (1 + taxa_mensal) ^ prazo")
        fator_comum = (1 + taxa_mensal) ** prazo
        self._logger.info(f"O resultado do 'fator_comum' é {fator_comum}")

        pmt = principal * (taxa_mensal * fator_comum) / (fator_comum - 1)
        self._logger.info(f"O resultado do 'pmt' é {pmt}")
        return pmt

    def calcula_principal(self, valor_solicitado: Decimal, iof: Decimal, tarifa_cadastrada: Decimal) -> Decimal:
        self._logger.info("Calculando o valor multiplicado ao iof")
        valor_iof = valor_solicitado * iof
        self._logger.info(f"O resultado do 'valor_iof' é {valor_iof}")
        self._logger.info("Retornando o valor da variável principal.")
        return valor_solicitado + valor_iof + tarifa_cadastrada

    def calcula_cet(self, dados: CetRequestCalculateDto) -> CetResponseCalculateDto:
        self._logger.info(
            "Iniciando o cálculo do CET com "
            f"valor_solicitado={dados['valor_solicitado']}, "
            f"taxa_juros_mensal={dados['taxa_juros_mensal']}, "
            f"prazo={dados['prazo']}, "
            f"iof={dados['iof']} e "
            f"tarifa_cadastrada={dados['tarifa_cadastrada']}"
        )

        self._logger.info("Realizando o cálculo da variável 'principal'")
        principal = self.calcula_principal(
            valor_solicitado=dados["valor_solicitado"],
            iof=dados["iof"],
            tarifa_cadastrada=dados["tarifa_cadastrada"]
        )
        self._logger.info(f"O resultado obtido da variável 'principal' é {principal}")
        self._logger.info("Realizando cálculo do PMT:")
        pmt = self.calcula_pmt(
            principal=principal,
            taxa_mensal=dados["taxa_juros_mensal"],
            prazo=dados["prazo"]
        )
        self._logger.info(f"O resultado obtido da variável 'pmt' é {pmt}")

        valor_total_pago = pmt * dados["prazo"]
        self._logger.info(f"O resultado obtido da variável 'valor_total_pago' é {valor_total_pago}")

        self._logger.info("Instanciando o 'CetRateSolver' para encontrar a taxa 'r' do CET.")
        rate_solver = CetRateSolver(
            pmt=pmt,
            valor_solicitado=dados["valor_solicitado"],
            prazo=dados["prazo"]
        )

        try:
            rate_resultado = rate_solver.resolver(chute_inicial=dados["taxa_juros_mensal"])
        except ValueError:
            self._logger.error("Falha ao resolver a taxa 'r' do CET, o cálculo será interrompido.")
            raise

        self._logger.info(
            f"O solver retornou r={rate_resultado['r']} em {rate_resultado['iteracoes']} iterações "
            f"(fallbacks={rate_resultado['usos_fallback']}, erro_final={rate_resultado['erro_final']})"
        )

        cet_mensal = rate_resultado["r"]
        self._logger.info("Convertendo o CET mensal em CET anual: (1 + cet_mensal)¹² - 1")
        cet_anual = (1 + cet_mensal) ** 12 - 1
        self._logger.info(f"O resultado obtido é cet_mensal={cet_mensal} e cet_anual={cet_anual}")

        resultado_final: CetResponseCalculateDto = {
            "cet_anual": cet_anual,
            "cet_mensal": cet_mensal,
            "pmt": pmt,
            "principal_financiado": principal,
            "valor_total_pago": valor_total_pago
        }

        self._logger.info("Cálculo do CET finalizado, retornando o resultado final.")
        return resultado_final
