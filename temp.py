"""
Cálculo de CET (Custo Efetivo Total) usando Newton-Raphson com
fallback para Bissecção, conforme estratégia definida em
"Estratégia de Cálculo do CET - Opção B".

Fluxo:
  1. Mantém um intervalo [baixo, alto] onde a raiz é garantidamente
     encontrada (propriedade de f ser monotonicamente decrescente).
  2. A cada iteração, tenta um passo de Newton-Raphson.
  3. Valida o candidato: precisa ser finito, estar dentro do
     intervalo conhecido, e não pode deixar 1+r inválido.
  4. Se o candidato for válido, aceita o passo e atualiza o intervalo.
  5. Se for inválido, faz um passo de Bissecção no lugar (usando o
     intervalo já reduzido até aqui).
  6. Encerra quando |f(r)| < tolerância ou o intervalo for pequeno
     o suficiente, respeitando o número máximo de iterações.
"""

from decimal import Decimal, getcontext, InvalidOperation

getcontext().prec = 28


# ---------------------------------------------------------------------------
# Principal financiado (Valor Solicitado + IOF + Tarifa de Cadastro)
# ---------------------------------------------------------------------------

def calcular_principal(
    valor_solicitado: Decimal,
    iof_fixo: Decimal,
    tarifa_cadastro: Decimal,
) -> Decimal:
    """
    Principal = ValorSolicitado + (ValorSolicitado * IOF) + TarifaCadastro

    Esse é o valor que efetivamente entra na fórmula da Tabela Price -
    o cliente recebe apenas o ValorSolicitado, mas paga parcelas
    calculadas sobre esse Principal maior (com os custos embutidos).
    """
    valor_iof = valor_solicitado * iof_fixo
    return valor_solicitado + valor_iof + tarifa_cadastro


# ---------------------------------------------------------------------------
# Tabela Price
# ---------------------------------------------------------------------------

def calcular_pmt(principal: Decimal, taxa_mensal: Decimal, prazo: int) -> Decimal:
    """PMT = P * [ i(1+i)^n / ((1+i)^n - 1) ]"""
    if taxa_mensal == 0:
        return principal / prazo
    i = taxa_mensal
    fator = (1 + i) ** prazo
    return principal * (i * fator) / (fator - 1)


# ---------------------------------------------------------------------------
# Função f(r) e derivada f'(r) usadas na busca da raiz
# ---------------------------------------------------------------------------

def f(r: Decimal, pmt: Decimal, valor_solicitado: Decimal, prazo: int) -> Decimal:
    """f(r) = Σ PMT/(1+r)^k - ValorSolicitado, para k=1..n"""
    total = Decimal(0)
    for k in range(1, prazo + 1):
        total += pmt / ((1 + r) ** k)
    return total - valor_solicitado


def f_linha(r: Decimal, pmt: Decimal, prazo: int) -> Decimal:
    """f'(r) = Σ -k * PMT / (1+r)^(k+1), para k=1..n"""
    total = Decimal(0)
    for k in range(1, prazo + 1):
        total += Decimal(-k) * pmt / ((1 + r) ** (k + 1))
    return total


# ---------------------------------------------------------------------------
# Validação do candidato produzido pelo Newton-Raphson
# ---------------------------------------------------------------------------

def candidato_valido(r_candidato: Decimal, baixo: Decimal, alto: Decimal) -> bool:
    """
    Verifica se o candidato do Newton-Raphson pode ser aceito:
    - deve estar numa região onde 1+r > 0 (denominador válido)
    - deve permanecer dentro do intervalo conhecido da raiz
    """
    if r_candidato is None:
        return False
    if r_candidato <= Decimal("-1"):
        # 1 + r <= 0 -> denominador inválido/indefinido
        return False
    if r_candidato <= baixo or r_candidato >= alto:
        # saiu do intervalo garantido -> não confiável
        return False
    return True


# ---------------------------------------------------------------------------
# Newton-Raphson "salvaguardado" com fallback para Bissecção
# ---------------------------------------------------------------------------

def encontrar_r(
    pmt: Decimal,
    valor_solicitado: Decimal,
    prazo: int,
    chute_inicial: Decimal,
    tolerancia: Decimal = Decimal("0.0000001"),
    max_iteracoes: int = 100,
) -> dict:
    """
    Encontra r tal que f(r) = 0, usando Newton-Raphson como método
    principal e Bissecção como mecanismo de segurança por iteração.

    Retorna um dicionário com o valor de r encontrado e metadados
    sobre a execução (iterações, quantas vezes o fallback foi usado).
    """
    # Intervalo inicial garantido: f(0) > 0 e f(alto) < 0 para um "alto"
    # grande o suficiente (limite de sanidade para taxa mensal).
    baixo = Decimal("0")
    alto = Decimal("10")  # 1000% a.m. -> limite bem folgado

    if f(baixo, pmt, valor_solicitado, prazo) <= 0:
        raise ValueError("Não há raiz no intervalo esperado (f(0) <= 0).")
    if f(alto, pmt, valor_solicitado, prazo) >= 0:
        raise ValueError("Intervalo de busca insuficiente (f(alto) >= 0).")

    r_atual = chute_inicial
    iteracoes_realizadas = 0
    usos_fallback = 0

    for iteracao in range(1, max_iteracoes + 1):
        iteracoes_realizadas = iteracao
        valor_f = f(r_atual, pmt, valor_solicitado, prazo)

        # Critério de parada: já convergiu o suficiente
        if abs(valor_f) < tolerancia:
            break

        # Atualiza o intervalo conhecido com base no sinal de f(r_atual)
        if valor_f > 0:
            baixo = r_atual
        else:
            alto = r_atual

        # Tenta um passo de Newton-Raphson
        candidato = None
        try:
            derivada = f_linha(r_atual, pmt, prazo)
            if derivada != 0:
                candidato = r_atual - (valor_f / derivada)
        except (InvalidOperation, ZeroDivisionError):
            candidato = None

        if candidato_valido(candidato, baixo, alto):
            r_atual = candidato
        else:
            # Fallback: passo de Bissecção usando o intervalo já reduzido
            usos_fallback += 1
            r_atual = (baixo + alto) / 2

    return {
        "r": r_atual,
        "iteracoes": iteracoes_realizadas,
        "usos_fallback": usos_fallback,
        "erro_final": abs(f(r_atual, pmt, valor_solicitado, prazo)),
    }


# ---------------------------------------------------------------------------
# Função principal do desafio
# ---------------------------------------------------------------------------

def calcular_emprestimo(
    valor_solicitado: Decimal,
    taxa_juros_mensal: Decimal,
    prazo: int,
    iof_fixo: Decimal,
    tarifa_cadastro: Decimal,
) -> dict:
    if valor_solicitado <= 0:
        raise ValueError("Valor solicitado deve ser positivo.")
    if taxa_juros_mensal < 0:
        raise ValueError("Taxa de juros não pode ser negativa.")
    if prazo <= 0:
        raise ValueError("Prazo deve ser maior que zero.")
    if iof_fixo < 0 or tarifa_cadastro < 0:
        raise ValueError("IOF e tarifa não podem ser negativos.")

    # Passo 1: Principal financiado
    principal = calcular_principal(valor_solicitado, iof_fixo, tarifa_cadastro)

    # Passo 2: PMT pela Tabela Price
    pmt = calcular_pmt(principal, taxa_juros_mensal, prazo)

    # Passo 3: CET -> encontrar r via Newton-Raphson com fallback,
    # usando a própria taxa nominal como chute inicial (como no documento)
    resultado_r = encontrar_r(
        pmt=pmt,
        valor_solicitado=valor_solicitado,
        prazo=prazo,
        chute_inicial=taxa_juros_mensal,
    )

    cet_mensal = resultado_r["r"]
    cet_anual = (1 + cet_mensal) ** 12 - 1

    return {
        "principal_financiado": principal,
        "pmt": pmt,
        "valor_total_pago": pmt * prazo,
        "cet_mensal": cet_mensal,
        "cet_anual": cet_anual,
        "iteracoes": resultado_r["iteracoes"],
        "usos_fallback": resultado_r["usos_fallback"],
        "erro_final": resultado_r["erro_final"],
    }


if __name__ == "__main__":
    resultado = calcular_emprestimo(
        valor_solicitado=Decimal("10000.00"),
        taxa_juros_mensal=Decimal("0.025"),
        prazo=24,
        iof_fixo=Decimal("0.0038"),
        tarifa_cadastro=Decimal("150.00"),
    )

    print(f"Principal financiado: R$ {resultado['principal_financiado']:.2f}")
    print(f"PMT (parcela mensal): R$ {resultado['pmt']:.2f}")
    print(f"Valor total pago:     R$ {resultado['valor_total_pago']:.2f}")
    print(f"CET mensal:           {resultado['cet_mensal']*100:.6f}%")
    print(f"CET anual:            {resultado['cet_anual']*100:.4f}%")
    print(f"Iterações usadas:     {resultado['iteracoes']}")
    print(f"Vezes que usou fallback (bissecção): {resultado['usos_fallback']}")
    print(f"Erro final |f(r)|:    {resultado['erro_final']}")