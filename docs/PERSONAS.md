# Personas: Casos de Uso do CET

Duas personas que exercitam o cálculo do CET por ângulos diferentes, cada uma com contexto,
entradas, saídas esperadas e a derivação passo a passo de cada número.

Todos os valores desta página foram conferidos rodando o `CetService` do projeto, e são os
que a suíte de testes assere. Se o cálculo mudar, os testes de `tests/e2e/test_personas.py`
acusam a divergência.

---

## Índice

1. [Visão geral](#1-visão-geral)
2. [De onde vêm o IOF e a tarifa](#2-de-onde-vêm-o-iof-e-a-tarifa)
   - [2.1 Mapeamento na tabela de alíquotas](#21-mapeamento-na-tabela-de-alíquotas)
   - [2.2 Como o IOF de crédito é calculado](#22-como-o-iof-de-crédito-é-calculado)
   - [2.3 A tarifa proporcional](#23-a-tarifa-proporcional)
3. [Fórmulas do CET](#3-fórmulas-do-cet)
4. [Persona 1 — Compra urgente por escassez](#4-persona-1--compra-urgente-por-escassez)
5. [Persona 2 — Aposentada indecisa sobre o valor do empréstimo](#5-persona-2--aposentada-indecisa-sobre-o-valor-do-empréstimo)
6. [Histórico: o que mudou e por quê](#6-histórico-o-que-mudou-e-por-quê)
7. [Como isso vira teste](#7-como-isso-vira-teste)

---

## 1. Visão geral

| | Persona 1 | Persona 2 |
|---|---|---|
| **Perfil** | Compra urgente por escassez | Aposentada indecisa sobre o valor |
| **Modalidade** | Rotativo do cartão de crédito | Empréstimo consignado |
| **Valor solicitado** | R$ 800,00 | R$ 10.000,00 e R$ 15.000,00 |
| **Taxa contratada** | 8% ao mês | 1,8% ao mês |
| **Prazo** | 6 meses | 36 meses |
| **IOF** | 2,3924% | 4,4607% |
| **Tarifa de cadastro** | R$ 12,00 | R$ 150,00 e R$ 225,00 |
| **CET mensal** | 9,27% | 2,16% |
| **CET anual** | 189,83% | 29,23% |
| **A pergunta que responde** | "O que eu vou pagar de verdade?" | "Quanto devo pedir?" |

As duas entradas que não são escolha arbitrária — IOF e tarifa — estão derivadas na seção 2.

---

## 2. De onde vêm o IOF e a tarifa

### 2.1 Mapeamento na tabela de alíquotas

O IOF de cada persona segue a alíquota da sua modalidade de crédito na tabela oficial de
alíquotas. As linhas relevantes:

| Operação | Alíquota IOF |
|---|---|
| Compras internacionais no cartão de crédito | 3,38% |
| **Rotativo do cartão de crédito** | **0,38% + 0,01118% ao dia** |
| Cheque especial | 0,38% + 0,01118% ao dia |
| Crédito pessoal | 0,38% + 0,01118% ao dia |
| **Empréstimo consignado** | **0,38% + 0,01118% ao dia** |
| Financiamento aquisição de imóveis não residenciais | 0,38% + 0,01118% ao dia |
| Seguro de vida e acidentes pessoais | 0,38% |
| Seguro de bens | 7,38% |
| Envio de recursos do exterior para o Brasil | 0,38% |
| Envio de recursos do Brasil para o exterior | 1,1% (mesma titularidade) ou 0,38% (titularidades diferentes) |
| Compra de moeda estrangeira | 1,1% |

A tabela classifica por **tipo de operação**, não por perfil de cliente, então o critério de
mapeamento foi a natureza do crédito descrita em cada persona, cruzada com a taxa de juros
que ela já pratica:

**Persona 1 — Compra urgente por escassez.** Valor baixo (R$ 800), prazo curto (6 meses) e
**8% ao mês**. Essa taxa é característica do rotativo do cartão de crédito — nenhuma
modalidade consignada ou de crédito pessoal com garantia opera nesse patamar. O contexto
reforça: compra por impulso sob pressão de tempo é a situação típica de quem parcela no
cartão e rola a fatura.

> **Rotativo do cartão de crédito → 0,38% + 0,01118% ao dia**

**Persona 2 — Aposentada.** Renda fixa previdenciária, prazo longo (36 meses) e **1,8% ao
mês**. Taxa baixa e prazo longo sobre benefício do INSS é a definição de crédito consignado,
que é justamente barato por ser descontado na folha.

> **Empréstimo consignado → 0,38% + 0,01118% ao dia**

As duas modalidades têm a mesma regra de alíquota, mas **prazos diferentes produzem IOF
diferente**, porque o componente diário depende do prazo da operação. É daí que sai a
diferença entre 2,3924% e 4,4607%.

#### Por que não uma alíquota fixa da tabela

A tabela tem valores fixos de uma linha só — 3,38% (compras internacionais), 7,38% (seguro
de bens), 1,1% (câmbio). Nenhum deles se aplica: são operações de cartão internacional,
seguro e câmbio, não empréstimo parcelado com tarifa de cadastro. Usar 3,38% para a
Persona 1 daria um número "da tabela", mas descreveria uma operação que não é a dela.

### 2.2 Como o IOF de crédito é calculado

As operações de crédito da tabela têm alíquota composta por duas parcelas:

```
IOF_total = IOF_adicional + (IOF_diário × dias_da_operação)

IOF_adicional = 0,38%          (cobrança única, independente do prazo)
IOF_diário    = 0,01118% ao dia
```

#### O teto de 365 dias

O componente diário **não corre indefinidamente**: a legislação do IOF limita a base de
cálculo a 365 dias. Sem esse teto, a Persona 2 (1.080 dias) teria 0,01118% × 1080 = 12,07%
de IOF diário, o que não corresponde a nenhuma operação real.

```
dias_cobrados = min(prazo_em_dias, 365)
```

> Esse teto não está na tabela de alíquotas — ela só informa o percentual. Ele vem da regra
> geral do imposto e foi aplicado aqui porque sem ele o número perde sentido econômico.

#### Simplificação assumida

Na cobrança real, o IOF diário incide sobre **cada parcela de amortização do principal**,
multiplicada pelos dias até o respectivo vencimento — o que dá um valor menor do que aplicar
a alíquota cheia sobre o total. O sistema modela `iof` como um **percentual único aplicado
sobre o valor solicitado** (`CetRequestCalculateDto.iof`), então não há onde representar a
cobrança parcela a parcela.

Adotamos a aproximação pelo prazo total da operação. Ela **superestima** ligeiramente o IOF,
o que é o lado seguro para um cálculo de CET: o custo informado ao cliente nunca fica abaixo
do real. Mudar isso exigiria alterar o DTO e o service.

#### Cálculo por persona

Mês comercial de 30 dias.

**Persona 1 — 6 meses:**

```
dias          = 6 × 30 = 180
dias_cobrados = min(180, 365) = 180
IOF_diário    = 0,01118% × 180 = 2,0124%
IOF_total     = 0,38% + 2,0124% = 2,3924%          →  0,023924
```

**Persona 2 (A e B) — 36 meses:**

```
dias          = 36 × 30 = 1.080
dias_cobrados = min(1.080, 365) = 365              ← teto aplicado
IOF_diário    = 0,01118% × 365 = 4,0807%
IOF_total     = 0,38% + 4,0807% = 4,4607%          →  0,044607
```

O IOF do consignado é quase o dobro do rotativo **apesar de o consignado ser o crédito mais
barato**. Isso não é contradição: o IOF diário remunera o tempo de exposição, e a aposentada
fica 3 anos devendo enquanto a Persona 1 fica 6 meses.

### 2.3 A tarifa proporcional

A tarifa de cadastro é uma proporção única do valor solicitado:

```
Tarifa = ValorSolicitado × 1,5%
```

Os 1,5% saem da própria Persona 2, cenário A, onde R$ 150,00 sobre R$ 10.000,00 já eram
exatamente essa proporção. Aplicando aos três cenários:

| Persona | Valor solicitado | Tarifa |
|---|---|---|
| 1 | R$ 800,00 | R$ 12,00 |
| 2A | R$ 10.000,00 | R$ 150,00 |
| 2B | R$ 15.000,00 | R$ 225,00 |

> Os 1,5% são derivados do próprio conjunto de dados, **não de uma referência de mercado**.
> Nenhuma tabela de TAC real foi consultada para validá-los.

#### A consequência que precisa ficar registrada

**Nenhum custo da operação é fixo**: o IOF é proporcional ao valor solicitado por construção,
e a tarifa também. O principal financiado é, portanto, um múltiplo constante do valor pedido:

```
Principal = V + (V × IOF) + (V × 1,5%)
          = V × (1 + IOF + 0,015)
```

Como o PMT é linear no principal, ele também vira múltiplo de `V`. E na equação do CET,

```
 n     PMT
 Σ   ───────── = V
k=1  (1 + r)ᵏ
```

`V` aparece dos dois lados e **se cancela**. O CET resultante não depende do valor
solicitado — só da taxa contratada, do prazo e das proporções de IOF e tarifa.

É por isso que os cenários A e B da Persona 2 têm exatamente o mesmo CET.

---

## 3. Fórmulas do CET

As quatro etapas que o `CetService` executa, na ordem.

### 3.1 Principal financiado

O IOF e a tarifa não são pagos à parte: entram no valor financiado.

```
Principal = ValorSolicitado + (ValorSolicitado × IOF) + Tarifa
```

Note que o IOF incide **só sobre o valor solicitado**, não sobre a tarifa.

### 3.2 PMT — Tabela Price

Parcela fixa que amortiza o principal em `n` períodos à taxa contratada `i`:

```
              i × (1 + i)ⁿ
PMT = P × ─────────────────
              (1 + i)ⁿ − 1
```

### 3.3 Valor total pago

```
Total = PMT × n
```

### 3.4 CET mensal

O CET é a taxa `r` que iguala o **valor efetivamente recebido pelo cliente** (o valor
solicitado, sem IOF nem tarifa) ao valor presente das parcelas que ele vai pagar:

```
        n     PMT
f(r) =  Σ  ─────────  −  ValorSolicitado  =  0
       k=1  (1 + r)ᵏ
```

É aqui que o custo aparece: o cliente paga parcelas calculadas sobre `Principal`, mas só
recebeu `ValorSolicitado`. A diferença — IOF e tarifa — vira taxa.

A equação não tem solução fechada. O `CetRateSolver` resolve por **Newton-Raphson**,

```
                f(rₖ)
rₖ₊₁ = rₖ − ───────────
               f′(rₖ)
```

com queda para **bissecção** no intervalo `[0, 10]` sempre que o passo de Newton produz um
candidato inválido. Tolerância: `|f(r)| < 1e-7`.

### 3.5 CET anual

Capitalização composta do mensal:

```
CET_anual = (1 + CET_mensal)¹² − 1
```

---

## 4. Persona 1 — Compra urgente por escassez

**Contexto:** pessoa que deseja adquirir um item de valor baixo, mas sob pressão de tempo
(ex: última unidade, promoção com prazo curto). A urgência reduz o tempo disponível para
comparar ofertas, tornando essa persona mais suscetível a aceitar condições piores sem
perceber.

**Modalidade:** rotativo do cartão de crédito — a taxa de 8% ao mês é característica dessa
linha, e parcelar no cartão é a saída típica de quem compra por impulso.

**Insight do CET:** ela decide olhando "8% ao mês" e paga **9,27%**. O CET expõe os quase 16%
de custo adicional que a pressa não deixa conferir. Repare que o maior custo acessório aqui
não é a tarifa (R$ 12,00), e sim o **IOF** (R$ 19,14) — o imposto de uma linha cara e de
curto prazo pesa mais que o preço do contrato.

### Entradas

| Parâmetro | Valor |
|---|---|
| Valor Solicitado | R$ 800,00 |
| Taxa de Juros | 8% ao mês |
| Prazo | 6 meses |
| IOF | 2,3924% — 0,38% + 0,01118% ao dia × 180 dias |
| Tarifa de Cadastro | R$ 12,00 — 1,5% do valor solicitado |

### Saídas esperadas

| Resultado | Valor |
|---|---|
| Principal Financiado | R$ 831,14 |
| PMT (parcela mensal) | R$ 179,79 |
| Valor Total Pago | R$ 1.078,73 |
| CET Mensal | 9,27% |
| CET Anual | 189,83% |

### Passo a passo

#### Passo 1 — Principal financiado

```
IOF em reais    = 800,00 × 0,023924 = 19,1392
Tarifa em reais = 800,00 × 0,015    = 12,00
Principal       = 800,00 + 19,1392 + 12,00
                = 831,1392
```

**Principal = R$ 831,14**

#### Passo 2 — PMT

```
(1 + 0,08)⁶ = 1,586874322944

        0,08 × 1,586874322944       0,12694994583552
fator = ───────────────────── = ──────────────────── = 0,2163153862290098
          1,586874322944 − 1       0,586874322944

PMT = 831,1392 × 0,2163153862290098 = 179,7881970580702393
```

**PMT = R$ 179,79**

#### Passo 3 — Valor total pago

```
Total = 179,7881970580702393 × 6 = 1.078,729182348421436
```

**Total = R$ 1.078,73**

#### Passo 4 — CET mensal

Buscar `r` tal que a soma das 6 parcelas de R$ 179,79 descontadas devolva os R$ 800 que a
cliente efetivamente recebeu:

```
 6    179,7881970580702393
 Σ   ──────────────────────  = 800,00
k=1        (1 + r)ᵏ
```

Newton-Raphson partindo do chute `r₀ = 0,08` (a taxa contratada) converge em 4 iterações,
sem nenhuma queda para bissecção:

```
r = 0,09272690729579978635521677383
```

Conferência: substituindo esse `r`, a soma dá **800,0000000006188** — dentro da tolerância.

**CET mensal = 9,2727% → 9,27%**

#### Passo 5 — CET anual

```
CET_anual = (1 + 0,0927269072957997863)¹² − 1
          = 1,898275377412642746
```

**CET anual = 189,8275% → 189,83%**

### Leitura

A cliente pede R$ 800,00 e devolve R$ 1.078,73 — **R$ 278,73 de custo, 34,8% do valor
pedido, em 6 meses**.

Como todo custo é proporcional, o CET dela seria os mesmos 9,27% pedindo R$ 800 ou
R$ 80.000: o tamanho do empréstimo não entra na conta. O que a define é a distância entre o
número que a fez decidir e o que ela vai pagar:

```
taxa contratada  = 8,00% a.m.
CET              = 9,27% a.m.     →  15,9% acima do anunciado
```

A urgência não muda a conta; muda o tempo disponível para conferi-la.

---

## 5. Persona 2 — Aposentada indecisa sobre o valor do empréstimo

**Contexto:** pessoa aposentada, sem pressa na decisão, mas insegura sobre quanto pedir para
reformar a casa — está avaliando entre R$ 10.000,00 e R$ 15.000,00, com prazo mais longo por
se tratar de renda fixa.

**Modalidade:** empréstimo consignado — taxa baixa e prazo longo sobre benefício
previdenciário. Note que o consignado é o crédito mais barato em juros das duas personas, mas
paga o **IOF maior**: o componente diário do imposto remunera tempo de exposição, e ela fica
3 anos devendo.

**Insight do CET:** como IOF e tarifa são ambos proporcionais ao valor solicitado, o CET é
**exatamente o mesmo** nos dois cenários — 29,23% ao ano, pedindo R$ 10.000 ou R$ 15.000. A
dúvida dela não se resolve pelo CET: ele não distingue as opções. Resolve-se pela **parcela**,
que cresce na mesma proporção do valor (R$ 402,48 contra R$ 603,72). O CET responde "qual
oferta é melhor", não "quanto devo pedir".

### 5.1 Cenário A — R$ 10.000,00

#### Entradas

| Parâmetro | Valor |
|---|---|
| Valor Solicitado | R$ 10.000,00 |
| Taxa de Juros | 1,8% ao mês |
| Prazo | 36 meses |
| IOF | 4,4607% — 0,38% + 0,01118% ao dia × 365 dias (teto) |
| Tarifa de Cadastro | R$ 150,00 — 1,5% do valor solicitado |

#### Saídas esperadas

| Resultado | Valor |
|---|---|
| Principal Financiado | R$ 10.596,07 |
| PMT (parcela mensal) | R$ 402,48 |
| Valor Total Pago | R$ 14.489,26 |
| CET Mensal | 2,16% |
| CET Anual | 29,23% |

#### Passo a passo

**Passo 1 — Principal financiado**

```
IOF em reais    = 10.000,00 × 0,044607 = 446,07
Tarifa em reais = 10.000,00 × 0,015    = 150,00
Principal       = 10.000,00 + 446,07 + 150,00
                = 10.596,07
```

**Passo 2 — PMT**

```
(1 + 0,018)³⁶ = 1,900728155743806362667104178

        0,018 × 1,900728155743806362
fator = ──────────────────────────── = 0,03798383184228975136
          1,900728155743806362 − 1

PMT = 10.596,07 × 0,03798383184228975136 = 402,4793410691311657
```

**Passo 3 — Valor total pago**

```
Total = 402,4793410691311657 × 36 = 14.489,25627848872196
```

**Passo 4 — CET mensal**

```
 36    402,4793410691311657
 Σ    ──────────────────────  = 10.000,00
k=1         (1 + r)ᵏ
```

Chute inicial `r₀ = 0,018`, convergência em 4 iterações sem fallback:

```
r = 0,02159987048441704357694040418
```

Conferência: a soma descontada devolve **10.000,000000000000000000999** — praticamente exato.

**CET mensal = 2,1600% → 2,16%**

**Passo 5 — CET anual**

```
CET_anual = (1 + 0,0215998704844170435)¹² − 1
          = 0,292319657271635223
```

**CET anual = 29,2320% → 29,23%**

### 5.2 Cenário B — R$ 15.000,00

Mesmas condições do cenário A, mudando só o valor solicitado — e, com ele, a tarifa, que
acompanha o valor.

#### Entradas

| Parâmetro | Valor |
|---|---|
| Valor Solicitado | R$ 15.000,00 |
| Taxa de Juros | 1,8% ao mês |
| Prazo | 36 meses |
| IOF | 4,4607% — 0,38% + 0,01118% ao dia × 365 dias (teto) |
| Tarifa de Cadastro | R$ 225,00 — 1,5% do valor solicitado |

#### Saídas esperadas

| Resultado | Valor |
|---|---|
| Principal Financiado | R$ 15.894,11 |
| PMT (parcela mensal) | R$ 603,72 |
| Valor Total Pago | R$ 21.733,88 |
| CET Mensal | 2,16% |
| CET Anual | 29,23% |

#### Passo a passo

**Passo 1 — Principal financiado**

```
IOF em reais    = 15.000,00 × 0,044607 = 669,105
Tarifa em reais = 15.000,00 × 0,015    = 225,00
Principal       = 15.000,00 + 669,105 + 225,00
                = 15.894,105
```

Confirmando o que a seção 2.3 previu: `15.894,105 / 15.000 = 1,059607`, e no cenário A
`10.596,07 / 10.000 = 1,059607`. O principal é o mesmo múltiplo do valor solicitado nos dois.

**Passo 2 — PMT**

O fator Price é o mesmo do cenário A (mesma taxa, mesmo prazo):

```
PMT = 15.894,105 × 0,03798383184228975136 = 603,7190116036967486
```

Também aqui a proporção se mantém: `603,7190… / 402,4793… = 1,5`, exatamente a razão entre
R$ 15.000 e R$ 10.000.

**Passo 3 — Valor total pago**

```
Total = 603,7190116036967486 × 36 = 21.733,88441773308295
```

**Passo 4 — CET mensal**

```
 36    603,7190116036967486
 Σ    ──────────────────────  = 15.000,00
k=1         (1 + r)ᵏ
```

Newton-Raphson converge em 5 iterações, sem fallback:

```
r = 0,02159987048441704357694040420
```

Conferência: soma descontada = **15.000,0000000000000000015** — dentro da tolerância de 1e-7.

**CET mensal = 2,1600% → 2,16%**

**Passo 5 — CET anual**

```
CET_anual = (1 + 0,0215998704844170435)¹² − 1
          = 0,292319657271635223
```

**CET anual = 29,2320% → 29,23%**

### 5.3 Comparação A vs B

| | R$ 10.000 | R$ 15.000 |
|---|---|---|
| CET Anual | 29,23% | 29,23% |
| PMT | R$ 402,48 | R$ 603,72 |

O CET **empata**, e não por arredondamento: a diferença entre os dois `r` é de `2E-29`, ruído
do `Decimal`. Com todo custo proporcional ao valor solicitado, principal e parcela crescem
juntos e a taxa que iguala os dois lados da equação é a mesma. Pedir R$ 5.000,00 a mais não
encarece nem barateia o crédito em termos percentuais — só aumenta a parcela em 50%.

> Se a tarifa fosse um **valor fixo** em vez de proporcional, o resultado seria outro: ela se
> diluiria no valor maior e o Cenário B ficaria com CET menor que o A. É a tarifa fixa, e nada
> mais, que faz o valor solicitado influenciar o CET.

---

## 6. Histórico: o que mudou e por quê

As personas passaram por duas revisões de parâmetros. O registro importa porque a segunda
**mudou o que elas demonstram**, não só os números.

### 6.1 IOF: de 0,38% genérico para a alíquota da modalidade

O IOF era 0,38% em todas as personas — o componente adicional da alíquota, sem o componente
diário. Passou a seguir a operação de crédito de cada uma (seção 2.2): 2,3924% no rotativo
de 6 meses, 4,4607% no consignado de 36 meses.

Essa alteração **não afetou nenhum insight**. O IOF é proporcional ao valor solicitado, então
incidiu igualmente em todos os cenários e preservou todas as comparações.

### 6.2 Tarifa: de R$ 150,00 fixos para 1,5% do valor

A tarifa era R$ 150,00 para todas as personas, independente do valor solicitado. Isso não se
sustentava nos extremos: R$ 150,00 sobre os R$ 800,00 da Persona 1 são **18,75% do valor
pedido** — nenhuma instituição cobra isso.

Esta alteração **reescreveu os dois insights**, e não por efeito colateral: pela álgebra da
seção 2.3. Os insights originais eram, ambos, afirmações sobre o comportamento de um custo
fixo. Removido o único custo fixo da operação, eles perderam o objeto.

| | Antes | Depois |
|---|---|---|
| **Persona 1** | A tarifa fixa domina o empréstimo pequeno | O custo real supera a taxa anunciada |
| **Persona 2** | Pedir mais reduz o CET percentual | O CET não distingue os dois valores |

**Persona 1.** O insight era o peso desproporcional de uma tarifa fixa num empréstimo
pequeno. Com a tarifa em 1,5%, o CET dela é o mesmo em qualquer montante — o tamanho saiu da
conta. O que sobra é a diferença entre os 8% contratados e os 9,27% pagos. Um detalhe
secundário ganhou relevância: com a tarifa em R$ 12,00, o **IOF (R$ 19,14) passou a ser o
maior custo acessório**, invertendo a relação anterior.

**Persona 2.** O insight era a diluição da tarifa fixa no valor maior. Sem custo fixo, a
inversão não enfraqueceu: **zerou**.

| | R$ 10.000 | R$ 15.000 | Diferença |
|---|---|---|---|
| CET anual, tarifa fixa (versão original) | 25,56% | 25,11% | 0,45 p.p. |
| CET anual, tarifa fixa + IOF novo | 29,23% | 28,78% | 0,45 p.p. |
| **CET anual, tarifa proporcional** | **29,23%** | **29,23%** | **0,00 p.p.** |

O insight novo é menos vistoso que o original, mas responde uma dúvida real e é mais
generalizável: o CET serve para **comparar ofertas**, não para dimensionar o quanto pedir.

### 6.3 Efeito no contraste entre as personas

A Persona 1 tem CET **4,3× maior** que a Persona 2 (9,27% contra 2,16% ao mês). Antes eram
6,8×, e a queda tem uma leitura: parte daquela distância era artefato da tarifa de R$ 150,00
aplicada a um empréstimo de R$ 800,00. O que sobrou é diferença real de produto — 8% a.m. de
rotativo contra 1,8% a.m. de consignado.

Com o valor solicitado fora da equação, o que encarece o crédito fica visível sem ruído:
**a taxa contratada e o prazo**.

---

## 7. Como isso vira teste

Os cenários acima estão em `tests/e2e/test_personas.py`, sob os marcadores `e2e` e `persona`:

```powershell
.venv\Scripts\python.exe -m pytest -m persona
```

As tabelas de **saídas esperadas** viram assert direto, comparadas no arredondamento de 2
casas deste documento (fixtures `assert_reais` e `assert_percentual`). Os **insights** viram
asserts de relação, sem valor cravado — é o que permite que continuem válidos quando um
parâmetro muda.

As entradas ficam em fixtures no `conftest.py`, construídas a partir de
`CetRequestCalculateDtoStub` por override parcial. O default do stub é o **cenário A da
Persona 2**, e as demais saem dele trocando só o que difere.

Alíquota e tarifa entram como **valor já resolvido**, não como cálculo:

```python
Decimal("0.0239240")   # IOF — Persona 1, rotativo, 6 meses
Decimal("0.0446070")   # IOF — Persona 2, consignado, 36 meses (teto de 365 dias)

Decimal("12")          # tarifa — 1,5% de R$ 800
Decimal("150")         # tarifa — 1,5% de R$ 10.000
Decimal("225")         # tarifa — 1,5% de R$ 15.000
```

A derivação de cada um está nas seções 2.2 e 2.3, e vai repetida como comentário ao lado de
cada literal. Reproduzir a fórmula em código de teste seria recalcular no teste o que o teste
deveria estar verificando — o valor esperado precisa ser uma constante conferida à mão, não
uma expressão que pode errar junto com a implementação.

Dois testes generalizam o insight da Persona 2 para além dos cenários dela:

- `test_o_cet_independe_do_valor_para_qualquer_montante` — verifica a igualdade do CET para
  R$ 2.000, R$ 50.000 e R$ 120.000;
- `test_a_decisao_se_resolve_pela_parcela` — verifica que a razão entre as parcelas é
  exatamente a razão entre os valores pedidos (1,5).

E um registra o que a mudança da tarifa desfez: `test_so_uma_tarifa_fixa_faria_o_valor_importar`
cobra que, **se** a tarifa voltasse a ser um valor fixo, o cenário B voltaria a ter CET menor
que o A — provando que a tarifa fixa, e nada mais, era a causa do efeito original.
