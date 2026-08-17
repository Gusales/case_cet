import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    """
    Serializa `Decimal` como string.

    Converter para `float` aqui desfaria o motivo de o projeto inteiro usar
    `Decimal`: 0.1 + 0.2 volta a não ser 0.3. String é lossless e o consumidor
    decide como interpretar.
    """

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)

        return super().default(o)
