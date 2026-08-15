from app.src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from app.src.utils.logger import Logger

class UserInputValidator:

    def __init__(self):
        self._logger = Logger(self.__class__)

    def validate(self, dados: CetRequestCalculateDto) -> None:
        self._logger.info("Validando os dados informados pelo usuário.")

        if dados["valor_solicitado"] <= 0:
            self._logger.error(f"Valor solicitado inválido: {dados['valor_solicitado']}")
            raise ValueError("Valor solicitado deve ser positivo.")
        if dados["taxa_juros_mensal"] < 0:
            self._logger.error(f"Taxa de juros mensal inválida: {dados['taxa_juros_mensal']}")
            raise ValueError("Taxa de juros não pode ser negativa.")
        if dados["prazo"] <= 0:
            self._logger.error(f"Prazo inválido: {dados['prazo']}")
            raise ValueError("Prazo deve ser maior que zero.")
        if dados["iof"] < 0 or dados["tarifa_cadastrada"] < 0:
            self._logger.error(f"IOF ou tarifa inválidos: iof={dados['iof']}, tarifa_cadastrada={dados['tarifa_cadastrada']}")
            raise ValueError("IOF e tarifa não podem ser negativos.")

        self._logger.info("Dados validados com sucesso.")
        return None
