from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto

class UserInputValidator:

    def validate(self, dados: CetRequestCalculateDto) -> None:
        if dados["valor_solicitado"] <= 0:
            raise ValueError("Valor solicitado deve ser positivo.")
        if dados["taxa_juros_mensal"] < 0:
            raise ValueError("Taxa de juros não pode ser negativa.")
        if dados["prazo"] <= 0:
            raise ValueError("Prazo deve ser maior que zero.")
        if dados["iof"] < 0 or dados["tarifa_cadastrada"] < 0:
            raise ValueError("IOF e tarifa não podem ser negativos.")

        return None