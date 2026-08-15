from decimal import Decimal

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto

class CetRequestCalculateDtoStub:
    def entity(self) -> CetRequestCalculateDto:
        entity_mock: CetRequestCalculateDto = {
            "prazo": 24,
            "tarifa_cadastrada": Decimal(150),
            "iof": Decimal(0.38),
            "taxa_juros_mensal": Decimal(2.5),
            "valor_solicitado": Decimal(10000)
        }

        return entity_mock