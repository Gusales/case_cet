# Entrevista Técnica: Cálculo de Custo Efetivo Total (CET)

## Objetivo

Você deve implementar a lógica central para calcular o Custo Efetivo Total (CET) anualizado e o valor da parcela mensal para um empréstimo pessoal simples. Esta tarefa avalia sua capacidade de lidar com cálculos financeiros, conversão de taxas, tratamento de erros, escolha de tipos de dados adequados (evitando problemas de ponto flutuante em moedas) e princípios fundamentais de engenharia de software.

## O Desafio

Implemente uma função ou módulo que calcule o valor da parcela mensal (usando a Tabela Price) e o valor total a ser pago ao final do empréstimo. A lógica deve contemplar o valor principal solicitado pelo cliente, a inclusão de impostos fixos (IOF) e tarifas operacionais no saldo devedor, e a aplicação da taxa de juros composta ao longo do prazo contratado.

A lógica deve aceitar os seguintes parâmetros:

| Parâmetro | Descrição | Unidade |
|---|---|---|
| Valor Solicitado | O valor principal que o cliente deseja tomar emprestado. | Reais (R$) |
| Taxa de Juros | Taxa de juros mensal aplicável ao perfil do cliente. | Porcentagem (%) |
| Prazo | Número de meses para o pagamento do empréstimo. | Meses |
| IOF Fixo | Imposto sobre Operações Financeiras fixo, calculado sobre o valor solicitado pelo cliente. | Porcentagem (%) |
| Tarifa de Cadastro | Custo operacional fixo embutido no financiamento. | Reais (R$) |

### Fórmula da Parcela (Tabela Price):

```
PMT = P × [ ( i × (1 + i)ⁿ ) / ( (1 + i)ⁿ - 1 ) ]
```

Onde:

- **PMT** = Valor da parcela mensal.
- **P** = Principal (Valor Solicitado + Impostos + Tarifas).
- **i** = Taxa de juros mensal em formato decimal (ex: 2,5% = 0,025).
- **n** = Prazo total do financiamento em meses.

### CET Anualizado Simplificado:

O CET mensal é a taxa **r** que faz o valor presente das parcelas igualar o valor que o cliente efetivamente recebe (o valor solicitado, sem IOF e tarifa, esses custos já estão embutidos nas parcelas):

```
Valor Solicitado = PMT₁/(1+r)¹ + PMT₂/(1+r)² + ... + PMTₙ/(1+r)ⁿ
```

Como essa equação não tem solução direta, **r** deve ser encontrado por um método numérico à sua escolha. O CET anual é então:

```
CET anual = (1 + r)¹² - 1
```

## Entradas para Teste

A implementação deve ser testável com os seguintes valores iniciais:

| Parâmetro | Valor |
|---|---|
| Valor Solicitado | R$ 10.000,00 |
| Taxa de Juros | 2,5% ao mês |
| Prazo | 24 meses |
| IOF Fixo | 0,38% |
| Tarifa de Cadastro | R$ 150,00 |

## FAQs

- A interface de usuário (UX) para executar o código fica a seu critério. Um script simples de linha de comando (CLI) é o mais comum, mas precisamos ser capazes de executar e testar também é perfeitamente aceitável.
- A linguagem de programação é de sua escolha. Você deve aproveitar esta oportunidade para demonstrar suas melhores habilidades e domínio técnico na ferramenta em que se sente mais confortável.
- O uso de ferramentas de Inteligência Artificial é encorajado. Contudo, espera-se que você compreenda integralmente, saiba justificar e seja capaz de modificar qualquer trecho de código gerado.