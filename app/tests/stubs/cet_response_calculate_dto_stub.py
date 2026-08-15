from decimal import Decimal

from src.dtos.cet_response_calculate_dto import CetResponseCalculateDto

class CetResponseCalculateDtoStub:
    def entity(self) -> CetResponseCalculateDto:
        def entity(self) -> CetResponseCalculateDto:
            entity_mock: CetResponseCalculateDto = {
                "prazo": 24,
                "tarifa_cadastrada": Decimal(150),
                "iof": Decimal(0.38),
                "taxa_juros_mensal": Decimal(2.5),
                "valor_solicitado": Decimal(10000)
            }

            return entity_mock