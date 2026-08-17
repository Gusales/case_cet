from decimal import Decimal, InvalidOperation

from src.dtos.cet_request_calculate_dto import CetRequestCalculateDto
from src.utils.logger import Logger

class HttpRequestValidator:
    """
    Converte o corpo JSON da requisição em `CetRequestCalculateDto`.

    Cuida só do transporte: presença dos campos, tipo e conversão de unidade.
    As regras de negócio (valor positivo, prazo maior que zero, etc.) ficam com
    o `UserInputValidator`, que roda depois.

    Assim como na CLI, `taxa_juros_mensal` e `iof` chegam em **percentual** e
    são convertidos para fração.
    """

    CAMPOS_OBRIGATORIOS = (
        "valor_solicitado",
        "taxa_juros_mensal",
        "prazo",
        "iof",
        "tarifa_cadastrada"
    )

    CAMPOS_PERCENTUAIS = ("taxa_juros_mensal", "iof")

    def __init__(self, body: dict | None):
        self._logger = Logger(self.__class__)
        self._body = body

    def validate(self) -> CetRequestCalculateDto:
        self._logger.info("Validando o corpo da requisição.")

        if self._body is None:
            self._logger.error("Corpo da requisição ausente ou não é um JSON válido.")
            raise ValueError("O corpo da requisição deve ser um JSON válido.")

        if not isinstance(self._body, dict):
            self._logger.error(f"Corpo da requisição não é um objeto JSON: {type(self._body).__name__}")
            raise ValueError("O corpo da requisição deve ser um objeto JSON.")

        ausentes = [campo for campo in self.CAMPOS_OBRIGATORIOS if campo not in self._body]
        if ausentes:
            self._logger.error(f"Campos obrigatórios ausentes: {ausentes}")
            raise ValueError(f"Campos obrigatórios ausentes: {', '.join(ausentes)}.")

        dados: CetRequestCalculateDto = {
            "valor_solicitado": self._para_decimal("valor_solicitado"),
            "taxa_juros_mensal": self._para_decimal("taxa_juros_mensal") / 100,
            "prazo": self._para_inteiro("prazo"),
            "iof": self._para_decimal("iof") / 100,
            "tarifa_cadastrada": self._para_decimal("tarifa_cadastrada")
        }

        self._logger.info("Corpo da requisição validado com sucesso.")
        return dados

    def _para_decimal(self, campo: str) -> Decimal:
        valor = self._body[campo]

        if isinstance(valor, float):
            # float já chega ao JSON com erro binário embutido; str() recupera
            # a representação decimal mais curta que o reproduz.
            valor = str(valor)

        try:
            return Decimal(valor)
        except (InvalidOperation, TypeError, ValueError):
            self._logger.error(f"Campo '{campo}' não é um número válido: {valor!r}")
            raise ValueError(f"Campo '{campo}' deve ser um número. Recebido: {valor!r}.")

    def _para_inteiro(self, campo: str) -> int:
        valor = self._body[campo]

        if isinstance(valor, bool):
            self._logger.error(f"Campo '{campo}' recebeu um booleano.")
            raise ValueError(f"Campo '{campo}' deve ser um número inteiro. Recebido: {valor!r}.")

        try:
            inteiro = int(valor)
        except (TypeError, ValueError):
            self._logger.error(f"Campo '{campo}' não é um inteiro válido: {valor!r}")
            raise ValueError(f"Campo '{campo}' deve ser um número inteiro. Recebido: {valor!r}.")

        if inteiro != Decimal(str(valor)):
            self._logger.error(f"Campo '{campo}' tem parte fracionária: {valor!r}")
            raise ValueError(f"Campo '{campo}' deve ser um número inteiro. Recebido: {valor!r}.")

        return inteiro
