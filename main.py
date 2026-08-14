from decimal import Decimal

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from src.services.cet_service import CetService
from src.validators.user_input_validator import UserInputValidator


def main():
    cet_service = CetService()
    try:
        dados: CetRequestCalculateDto = {
            "valor_solicitado": Decimal(input("Valor solicitado: ")),
            "taxa_juros_mensal": Decimal(input("Taxa de juros mensal (%): ")) / 100,
            "prazo": int(input("Prazo (meses): ")),
            "iof": Decimal(input("IOF (%): ")) / 100,
            "tarifa_cadastrada": Decimal(input("Tarifa cadastrada (R$): ")),
        }

        UserInputValidator().validate(dados)

        resultado = cet_service.calcula_cet(dados)

        print(resultado)
    except ValueError as e:
        print(f"Erro de validação: {e}")

if __name__ == '__main__':
    main()