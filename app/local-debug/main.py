from decimal import Decimal

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from src.services.cet_service import CetService
from src.utils.logger import Logger
from src.validators.user_input_validator import UserInputValidator

logger = Logger()


def main():
    logger.info("[local-debug] - Aplicação iniciada, aguardando os dados do usuário.")
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

        logger.info("[local-debug] - Cálculo concluído com sucesso.")
        logger.info(resultado)
    except ValueError as e:
        logger.error(f"[local-debug] - Erro de validação: {e}")

if __name__ == '__main__':
    main()
