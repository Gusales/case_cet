// ---------------------------------------------------------------------------
// Endpoint da Cloud Function. Trocar aqui para apontar para outro ambiente
// (ex.: emulador local ou a URL direta do Cloud Functions).
// ---------------------------------------------------------------------------
const API_URL = "https://us-central1-lambda-bedrock-analytics.cloudfunctions.net/calcula_cet";

// Histórico das simulações — vive só em memória, some ao recarregar a página.
const historico = [];

const CAMPOS = [
  "valor_solicitado",
  "taxa_juros_mensal",
  "prazo",
  "iof",
  "tarifa_cadastrada"
];

const formulario = document.getElementById("formulario");
const btnCalcular = document.getElementById("btn-calcular");
const btnHistorico = document.getElementById("btn-historico");
const btnLimpar = document.getElementById("btn-limpar");
const contador = document.getElementById("contador");
const erro = document.getElementById("erro");
const modalResultado = document.getElementById("modal-resultado");
const modalHistorico = document.getElementById("modal-historico");
const listaHistorico = document.getElementById("lista-historico");

document.getElementById("endpoint").textContent = API_URL;

// ---------------------------------------------------------------------------
// Formatação
//
// A API devolve os valores como string para não perder a precisão do Decimal.
// Aqui só arredondamos para exibição — o valor cheio fica guardado no histórico.
// ---------------------------------------------------------------------------

const emReais = (valor) =>
  Number(valor).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });

const emPercentual = (fracao) =>
  `${(Number(fracao) * 100).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}%`;

// ---------------------------------------------------------------------------
// Requisição
// ---------------------------------------------------------------------------

function lerFormulario() {
  const dados = {};

  for (const campo of CAMPOS) {
    dados[campo] = Number(formulario.elements[campo].value);
  }

  return dados;
}

async function calcularCet(dados) {
  const resposta = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  });

  const corpo = await resposta.json().catch(() => null);

  if (!resposta.ok) {
    // A função devolve {"message": "..."} nos erros 4xx e 5xx.
    throw new Error(corpo?.message || `A requisição falhou (HTTP ${resposta.status}).`);
  }

  return corpo.data;
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  if (!formulario.reportValidity()) return;

  const entrada = lerFormulario();

  erro.hidden = true;
  btnCalcular.disabled = true;
  btnCalcular.textContent = "Calculando...";

  try {
    const resultado = await calcularCet(entrada);

    historico.unshift({
      entrada,
      resultado,
      hora: new Date().toLocaleTimeString("pt-BR")
    });

    atualizarContador();
    mostrarResultado(entrada, resultado);
  } catch (falha) {
    erro.textContent = falha.message;
    erro.hidden = false;
  } finally {
    btnCalcular.disabled = false;
    btnCalcular.textContent = "Calcular CET";
  }
});

// ---------------------------------------------------------------------------
// Modal de resultado
// ---------------------------------------------------------------------------

function mostrarResultado(entrada, resultado) {
  document.getElementById("r-cet-mensal").textContent = emPercentual(resultado.cet_mensal);
  document.getElementById("r-cet-anual").textContent = emPercentual(resultado.cet_anual);
  document.getElementById("r-pmt").textContent = emReais(resultado.pmt);
  document.getElementById("r-principal").textContent = emReais(resultado.principal_financiado);
  document.getElementById("r-total").textContent = emReais(resultado.valor_total_pago);

  const custo = Number(resultado.valor_total_pago) - entrada.valor_solicitado;
  document.getElementById("r-custo").textContent = emReais(custo);

  const cetMensal = Number(resultado.cet_mensal) * 100;
  const acima = ((cetMensal / entrada.taxa_juros_mensal - 1) * 100).toFixed(1);

  document.getElementById("r-nota").textContent =
    `A taxa contratada é de ${entrada.taxa_juros_mensal}% ao mês, mas o custo efetivo ` +
    `é de ${cetMensal.toFixed(2)}% — ${acima}% acima. A diferença é o IOF e a tarifa, ` +
    `que entram no valor financiado mas não no que você recebe.`;

  modalResultado.showModal();
}

// ---------------------------------------------------------------------------
// Modal de histórico
// ---------------------------------------------------------------------------

function atualizarContador() {
  contador.textContent = historico.length;
}

function renderizarHistorico() {
  if (historico.length === 0) {
    listaHistorico.innerHTML =
      '<p class="vazio">Nenhuma simulação ainda.<br>Os cálculos aparecem aqui depois de calculados.</p>';
    return;
  }

  listaHistorico.innerHTML = historico
    .map((registro, indice) => {
      const { entrada, resultado, hora } = registro;

      return `
        <article class="item">
          <div class="item-topo">
            <span class="item-titulo">#${historico.length - indice} · ${emReais(entrada.valor_solicitado)}</span>
            <span class="item-hora">${hora}</span>
          </div>
          <p class="item-entrada">
            ${entrada.taxa_juros_mensal}% a.m. · ${entrada.prazo} meses ·
            IOF ${entrada.iof}% · tarifa ${emReais(entrada.tarifa_cadastrada)}
          </p>
          <div class="item-saida">
            <span class="etiqueta destaque-cet">CET ${emPercentual(resultado.cet_mensal)} a.m.</span>
            <span class="etiqueta destaque-cet">CET ${emPercentual(resultado.cet_anual)} a.a.</span>
            <span class="etiqueta">PMT ${emReais(resultado.pmt)}</span>
            <span class="etiqueta">Total ${emReais(resultado.valor_total_pago)}</span>
          </div>
        </article>
      `;
    })
    .join("");
}

btnHistorico.addEventListener("click", () => {
  renderizarHistorico();
  modalHistorico.showModal();
});

btnLimpar.addEventListener("click", () => {
  historico.length = 0;
  atualizarContador();
  renderizarHistorico();
});

// ---------------------------------------------------------------------------
// Fechamento dos modais
// ---------------------------------------------------------------------------

for (const botao of document.querySelectorAll("[data-fechar]")) {
  botao.addEventListener("click", () => {
    document.getElementById(botao.dataset.fechar).close();
  });
}

// Clique no backdrop fecha o modal.
for (const modal of [modalResultado, modalHistorico]) {
  modal.addEventListener("click", (evento) => {
    if (evento.target === modal) modal.close();
  });
}

atualizarContador();
