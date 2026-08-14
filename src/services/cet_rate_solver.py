from decimal import Decimal, InvalidOperation

class CetRateSolver:
    """
    Encapsula a busca da taxa r tal que:

        f(r) = Σ PMT/(1+r)^k - ValorSolicitado = 0   (k = 1..n)

    Estratégia: Newton-Raphson como método principal, validando cada
    candidato produzido; quando o candidato não é válido, um passo de
    Bissecção é usado no lugar, aproveitando o intervalo [baixo, alto]
    já reduzido até aquele ponto (não reinicia a busca do zero).
    """

    def __init__(
            self,
            pmt: Decimal,
            valor_solicitado: Decimal,
            prazo: int,
            tolerancia: Decimal = Decimal("0.0000001"),
            max_iteracoes: int = 100,
    ):
        self.pmt = pmt
        self.valor_solicitado = valor_solicitado
        self.prazo = prazo
        self.tolerancia = tolerancia
        self.max_iteracoes = max_iteracoes

    def f(self, r: Decimal) -> Decimal:
        """f(r) = Σ PMT/(1+r)^k - ValorSolicitado, para k=1..n"""
        total = Decimal(0)
        for k in range(1, self.prazo + 1):
            total += self.pmt / ((1 + r) ** k)
        return total - self.valor_solicitado

    def f_linha(self, r: Decimal) -> Decimal:
        """f'(r) = Σ -k * PMT / (1+r)^(k+1), para k=1..n"""
        total = Decimal(0)
        for k in range(1, self.prazo + 1):
            total += Decimal(-k) * self.pmt / ((1 + r) ** (k + 1))
        return total

    def _candidato_valido(self, r_candidato, baixo: Decimal, alto: Decimal) -> bool:
        """
        Verifica se o candidato do Newton-Raphson pode ser aceito:
        - deve estar numa região onde 1+r > 0 (denominador válido)
        - deve permanecer dentro do intervalo conhecido da raiz
        """
        if r_candidato is None:
            return False
        if r_candidato <= Decimal("-1"):
            return False
        if r_candidato <= baixo or r_candidato >= alto:
            return False
        return True

    def resolver(self, chute_inicial: Decimal) -> dict:
        """
        Executa a busca e retorna um dicionário com o r encontrado e
        metadados da execução (iterações, quantas vezes o fallback
        foi usado, erro final).
        """
        baixo = Decimal("0")
        alto = Decimal("10")  # 1000% a.m. -> limite bem folgado

        if self.f(baixo) <= 0:
            raise ValueError("Não há raiz no intervalo esperado (f(0) <= 0).")
        if self.f(alto) >= 0:
            raise ValueError("Intervalo de busca insuficiente (f(alto) >= 0).")

        r_atual = chute_inicial
        iteracoes_realizadas = 0
        usos_fallback = 0

        for iteracao in range(1, self.max_iteracoes + 1):
            iteracoes_realizadas = iteracao
            valor_f = self.f(r_atual)

            if abs(valor_f) < self.tolerancia:
                break

            if valor_f > 0:
                baixo = r_atual
            else:
                alto = r_atual

            candidato = None
            try:
                derivada = self.f_linha(r_atual)
                if derivada != 0:
                    candidato = r_atual - (valor_f / derivada)
            except (InvalidOperation, ZeroDivisionError):
                candidato = None

            if self._candidato_valido(candidato, baixo, alto):
                r_atual = candidato
            else:
                usos_fallback += 1
                r_atual = (baixo + alto) / 2

        return {
            "r": r_atual,
            "iteracoes": iteracoes_realizadas,
            "usos_fallback": usos_fallback,
            "erro_final": abs(self.f(r_atual)),
        }

