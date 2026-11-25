/* =========================================================================
   TripScripter — funções compartilhadas pelas telas

   Formatação de datas e valores, fotos de destino e categorias. Não acessa
   a API: isso fica em js/api.js.

   Ordem de carregamento em todas as páginas:
     js/comum.js  →  js/api.js  →  script da própria página
   ========================================================================= */

var Trip = (function () {
  "use strict";

  /* ----------------------------------------------------------------------
     Texto
     ---------------------------------------------------------------------- */

  /* Todo texto vindo da API passa por aqui antes de entrar no HTML, para
     que um nome de local com "<script>" apareça como texto, e não rode. */
  function escapar(texto) {
    var caixa = document.createElement("div");
    caixa.textContent = texto == null ? "" : String(texto);
    return caixa.innerHTML;
  }

  /* "São Paulo" → "sao paulo": usada em buscas e comparações. */
  function semAcento(texto) {
    return String(texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  }

  function cidadeDe(destino) { return String(destino || "").split(",")[0].trim(); }

  function paisDe(destino) {
    var partes = String(destino || "").split(",");
    return partes.length > 1 ? partes[partes.length - 1].trim() : partes[0].trim();
  }

  function listar(itens) {
    if (!itens.length) return "";
    if (itens.length === 1) return itens[0];
    return itens.slice(0, -1).join(", ") + " e " + itens[itens.length - 1];
  }

  /* ----------------------------------------------------------------------
     Datas — a API usa o formato ISO (2027-05-15)
     ---------------------------------------------------------------------- */

  var MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
               "agosto", "setembro", "outubro", "novembro", "dezembro"];

  /* Lê a data como dia do calendário, sem fuso horário: new Date("2027-05-15")
     seria meia-noite em UTC, que em Brasília ainda é o dia 14. */
  function lerData(iso) {
    var p = String(iso).split("-");
    return new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
  }

  function hojeISO() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  /* "15 mai" */
  function diaCurto(iso) {
    var d = lerData(iso);
    return d.getDate() + " " + MESES[d.getMonth()].slice(0, 3);
  }

  /* "15 a 17 de maio de 2027", "30 de maio a 2 de junho de 2027" */
  function periodo(inicio, fim) {
    var a = lerData(inicio), b = lerData(fim);
    if (a.getFullYear() !== b.getFullYear()) {
      return a.getDate() + " de " + MESES[a.getMonth()] + " de " + a.getFullYear() +
             " a " + b.getDate() + " de " + MESES[b.getMonth()] + " de " + b.getFullYear();
    }
    if (a.getMonth() !== b.getMonth()) {
      return a.getDate() + " de " + MESES[a.getMonth()] + " a " +
             b.getDate() + " de " + MESES[b.getMonth()] + " de " + b.getFullYear();
    }
    if (a.getDate() === b.getDate()) return a.getDate() + " de " + MESES[a.getMonth()] + " de " + a.getFullYear();
    return a.getDate() + " a " + b.getDate() + " de " + MESES[a.getMonth()] + " de " + a.getFullYear();
  }

  function anoDe(iso) { return Number(String(iso).slice(0, 4)); }

  function dias(n) { return n === 1 ? "1 dia" : n + " dias"; }

  /* "09:00:00" → "09:00" */
  function hora(valor) { return valor ? String(valor).slice(0, 5) : ""; }

  /* A API não informa a moeda: o custo está na moeda local do destino. */
  function custo(valor) {
    if (valor === null || valor === undefined || valor === "") return "";
    var numero = Number(valor);
    if (numero === 0) return "Gratuito";
    return numero.toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  }

  /* ----------------------------------------------------------------------
     Situação da viagem, para a etiqueta do cartão
     ---------------------------------------------------------------------- */

  function situacao(viagem) {
    var hoje = hojeISO();
    if (viagem.data_fim < hoje) return { rotulo: "Concluída", classe: "etiqueta--concluida" };
    if (viagem.data_inicio <= hoje) return { rotulo: "Em andamento", classe: "etiqueta--andamento" };
    if (!viagem.total_atividades) return { rotulo: "Planejando", classe: "etiqueta--planejando" };
    return { rotulo: "Próxima viagem", classe: "" };
  }

  /* ----------------------------------------------------------------------
     Fotos de destino (Unsplash)

     Só destinos com foto própria recebem imagem. Para os demais, o cartão
     mantém o degradê com o ícone: mostrar a foto de outra cidade seria
     enganoso. Se a foto não carregar (sem internet), o degradê também fica.
     ========================================================================= */

  var FOTOS = {
    paris: "photo-1502602898657-3e91760cbb34",
    toquio: "photo-1540959733332-eab4deabeeaf",
    tokyo: "photo-1540959733332-eab4deabeeaf",
    lisboa: "photo-1555881400-74d7acaacd8b",
    "buenos aires": "photo-1589909202802-8f4aadce1849",
    "nova york": "photo-1496442226666-8d4d0e62e6e9",
    "nova iorque": "photo-1496442226666-8d4d0e62e6e9",
    "new york": "photo-1496442226666-8d4d0e62e6e9",
    barcelona: "photo-1539635278303-d4002c07eae3"
  };

  function fotoDoDestino(destino) {
    var codigo = FOTOS[semAcento(cidadeDe(destino))];
    return codigo ? "https://images.unsplash.com/" + codigo + "?w=600&q=80&fit=crop" : null;
  }

  var ICONE_PINO =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>';

  /* Capa do cartão de viagem. A classe .viagem__capa (seção 3 do CSS) já
     desenha o degradê com o ícone; a foto, quando há, cobre os dois. Se a
     foto falhar, o elemento img é removido e o degradê reaparece. */
  function capa(viagem, selo) {
    var foto = fotoDoDestino(viagem.destino);
    var etiqueta = selo
      ? '<span class="etiqueta viagem__selo ' + selo.classe + '">' + escapar(selo.rotulo) + "</span>"
      : "";
    var imagem = foto
      ? '<img src="' + foto + '" alt="" loading="lazy" onerror="this.remove()">'
      : "";
    return '<div class="viagem__capa viagem__capa--foto">' + ICONE_PINO + imagem + etiqueta + "</div>";
  }

  /* ----------------------------------------------------------------------
     Categorias — mesmas cores da seção 13 de css/estilo.css
     ---------------------------------------------------------------------- */

  var CORES = {
    "Cultura": "#3a5a9b",
    "Gastronomia": "#0b6d62",
    "Arte": "#6b4f9e",
    "Natureza": "#3d7a46",
    "História": "#4f5b6a",
    "Compras": "#236b88",
    "Vida noturna": "#2f3e73",
    "Praia": "#177d92"
  };

  var CATEGORIAS = Object.keys(CORES);

  function corDaCategoria(categoria) { return CORES[categoria] || "#0e7c70"; }

  function etiquetaDaCategoria(categoria) {
    if (!categoria) return "";
    var classe = "categoria--" + semAcento(categoria).replace(/\s+/g, "-");
    return '<span class="categoria ' + classe + '">' + escapar(categoria) + "</span>";
  }

  return {
    escapar: escapar,
    semAcento: semAcento,
    cidadeDe: cidadeDe,
    paisDe: paisDe,
    listar: listar,
    hojeISO: hojeISO,
    diaCurto: diaCurto,
    periodo: periodo,
    anoDe: anoDe,
    dias: dias,
    hora: hora,
    custo: custo,
    situacao: situacao,
    fotoDoDestino: fotoDoDestino,
    capa: capa,
    CATEGORIAS: CATEGORIAS,
    corDaCategoria: corDaCategoria,
    etiquetaDaCategoria: etiquetaDaCategoria
  };
})();
