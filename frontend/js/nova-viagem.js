/* =========================================================================
   TripScripter — assistente de nova viagem (RQ003 e RQ004)

   Fluxo em três passos, com validação por passo: o usuário só avança
   quando os campos daquele passo estão preenchidos corretamente. Os dados
   informados permanecem ao navegar entre os passos.

   Ao confirmar, a página cria a viagem (POST /api/viagens/) e pede a
   geração do roteiro (POST /api/viagens/<id>/gerar-roteiro/). As etapas
   exibidas avançam enquanto a API trabalha; o resultado só aparece quando
   a resposta chega.

   O campo de destino sugere cidades pelo Photon, serviço gratuito baseado
   no OpenStreetMap, sem chave de API. Sem internet, o campo continua
   aceitando o texto digitado.
   ========================================================================= */

(function () {
  "use strict";

  if (!API.exigirLogin()) return;
  API.prepararBarra();

  var TOTAL_PASSOS = 3;
  var DURACAO_MAXIMA = 30;   /* mesmo limite de backend/dominio/regras.py */

  var ROTULOS = {
    1: "Passo 1 de 3 · Destino e período",
    2: "Passo 2 de 3 · Preferências",
    3: "Passo 3 de 3 · Revisão"
  };

  var form = document.getElementById("formViagem");
  var destino = document.getElementById("destino");
  var ida = document.getElementById("ida");
  var volta = document.getElementById("volta");
  var ritmo = document.getElementById("ritmo");
  var duracao = document.getElementById("duracao");

  var preenchido = document.getElementById("progressoPreenchido");
  var rotulo = document.getElementById("progressoRotulo");
  var porcento = document.getElementById("progressoPorcento");

  var painelGerando = document.getElementById("painelGerando");
  var painelPronto = document.getElementById("painelPronto");
  var resumoPronto = document.getElementById("resumoPronto");
  var linkRoteiro = document.getElementById("linkRoteiro");
  var etapas = document.querySelectorAll("#etapas li");

  var passoAtual = 1;

  /* ----------------------------------------------------------------------
     Datas
     ---------------------------------------------------------------------- */

  var hoje = new Date().toISOString().split("T")[0];
  ida.min = hoje;
  volta.min = hoje;

  function contarDias() {
    if (!ida.value || !volta.value) return 0;
    var dias = Math.round((new Date(volta.value) - new Date(ida.value)) / 86400000) + 1;
    return dias > 0 ? dias : 0;
  }

  function formatarData(iso) {
    if (!iso) return "";
    var p = iso.split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }

  function mostrarDuracao() {
    if (ida.value) volta.min = ida.value;
    var dias = contarDias();
    duracao.textContent = dias > 0
      ? (dias === 1 ? "1 dia de viagem" : dias + " dias de viagem")
      : "";
  }

  ida.addEventListener("change", mostrarDuracao);
  volta.addEventListener("change", mostrarDuracao);

  /* ----------------------------------------------------------------------
     Validação por passo
     ---------------------------------------------------------------------- */

  function erro(id, visivel) {
    document.getElementById(id).classList.toggle("esta-visivel", visivel);
  }

  function interesses() {
    var marcados = document.querySelectorAll("input[name='pref']:checked");
    return Array.prototype.map.call(marcados, function (c) { return c.value; });
  }

  function validarPasso(numero) {
    var ok = true;

    if (numero === 1) {
      var semDestino = destino.value.trim() === "";
      erro("erroDestino", semDestino);
      document.getElementById("campoDestino").classList.toggle("campo--invalido", semDestino);
      if (semDestino) { ok = false; destino.focus(); }

      var datasRuins = contarDias() === 0 || contarDias() > DURACAO_MAXIMA;
      erro("erroDatas", datasRuins);
      if (datasRuins) { if (ok) ida.focus(); ok = false; }
    }

    if (numero === 2) {
      var semPref = interesses().length === 0;
      erro("erroPref", semPref);
      if (semPref) ok = false;
    }

    return ok;
  }

  /* Limpa o aviso assim que o usuário corrige o campo. */

  destino.addEventListener("input", function () {
    if (destino.value.trim() !== "") {
      erro("erroDestino", false);
      document.getElementById("campoDestino").classList.remove("campo--invalido");
    }
  });

  form.addEventListener("change", function (evento) {
    if (evento.target.name === "pref" && interesses().length > 0) erro("erroPref", false);
    if (evento.target === ida || evento.target === volta) {
      if (contarDias() > 0 && contarDias() <= DURACAO_MAXIMA) erro("erroDatas", false);
    }
  });

  /* ----------------------------------------------------------------------
     Navegação entre os passos
     ---------------------------------------------------------------------- */

  function irPara(numero) {
    document.querySelectorAll(".passo").forEach(function (secao) {
      secao.setAttribute("data-ativo", secao.dataset.passo === String(numero) ? "true" : "false");
    });

    passoAtual = numero;

    var pct = Math.round((numero / TOTAL_PASSOS) * 100);
    preenchido.style.width = pct + "%";
    porcento.textContent = pct + "%";
    rotulo.textContent = ROTULOS[numero];

    if (numero === 3) preencherRevisao();

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  form.addEventListener("click", function (evento) {
    var botao = evento.target.closest("button[data-ir]");
    if (!botao) return;

    var destinoPasso = Number(botao.dataset.ir);

    /* Voltar nunca valida; avançar valida o passo atual. */
    if (destinoPasso > passoAtual && !validarPasso(passoAtual)) return;

    irPara(destinoPasso);
  });

  /* ----------------------------------------------------------------------
     Revisão
     ---------------------------------------------------------------------- */

  function listar(itens) {
    if (itens.length === 0) return "—";
    if (itens.length === 1) return itens[0];
    return itens.slice(0, -1).join(", ") + " e " + itens[itens.length - 1];
  }

  function preencherRevisao() {
    var dias = contarDias();

    document.getElementById("revDestino").textContent = destino.value.trim() || "—";
    document.getElementById("revPeriodo").textContent =
      ida.value && volta.value ? formatarData(ida.value) + " a " + formatarData(volta.value) : "—";
    document.getElementById("revDuracao").textContent =
      dias > 0 ? (dias === 1 ? "1 dia" : dias + " dias") : "—";
    document.getElementById("revInteresses").textContent = listar(interesses());
    document.getElementById("revRitmo").textContent = ritmo.value;
  }

  /* ----------------------------------------------------------------------
     Sugestões de destino (Photon / OpenStreetMap)
     ---------------------------------------------------------------------- */

  var sugestoes = document.getElementById("sugestoes");
  var resultados = [];
  var selecionada = -1;
  var espera = null;
  var pedidoAtual = null;

  var TIPOS = { city: "Cidade", town: "Cidade", village: "Vila", country: "País",
                state: "Estado", county: "Região", island: "Ilha" };

  function rotuloDoLugar(lugar) {
    var p = lugar.properties;
    var partes = [p.name];
    if (p.state && p.state !== p.name && p.osm_value !== "country") partes.push(p.state);
    if (p.country && p.country !== p.name) partes.push(p.country);
    return partes.filter(Boolean).join(", ");
  }

  function fecharSugestoes() {
    sugestoes.hidden = true;
    destino.setAttribute("aria-expanded", "false");
    selecionada = -1;
  }

  function desenharSugestoes() {
    if (!resultados.length) { fecharSugestoes(); return; }
    sugestoes.innerHTML = resultados.map(function (lugar, i) {
      var tipo = TIPOS[lugar.properties.osm_value] || "Local";
      return '<li role="presentation"><button type="button" class="sugestao" role="option" data-i="' + i + '"' +
        ' aria-selected="' + (i === selecionada) + '">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">' +
        '<path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>' +
        '<span class="sugestao__nome">' + Trip.escapar(rotuloDoLugar(lugar)) + "</span>" +
        '<span class="sugestao__tipo">' + tipo + "</span></button></li>";
    }).join("");
    sugestoes.hidden = false;
    destino.setAttribute("aria-expanded", "true");
  }

  function buscarSugestoes(texto) {
    if (pedidoAtual) pedidoAtual.abort();
    if (texto.length < 2) { resultados = []; fecharSugestoes(); return; }
    pedidoAtual = new AbortController();
    fetch("https://photon.komoot.io/api/?limit=6&lang=pt&layer=city&layer=country&layer=state&q=" + encodeURIComponent(texto),
          { signal: pedidoAtual.signal })
      .then(function (r) { return r.json(); })
      .then(function (dados) {
        resultados = (dados.features || []).filter(function (f) { return f.properties.name; });
        selecionada = -1;
        desenharSugestoes();
      })
      .catch(function () { /* sem internet ou pedido cancelado: segue com o texto digitado */ });
  }

  function escolher(i) {
    destino.value = rotuloDoLugar(resultados[i]);
    destino.dispatchEvent(new Event("input"));
    resultados = [];
    fecharSugestoes();
  }

  destino.addEventListener("input", function (evento) {
    if (!evento.isTrusted) return;
    clearTimeout(espera);
    espera = setTimeout(function () { buscarSugestoes(destino.value.trim()); }, 300);
  });

  destino.addEventListener("keydown", function (evento) {
    if (sugestoes.hidden) return;
    if (evento.key === "ArrowDown" || evento.key === "ArrowUp") {
      evento.preventDefault();
      var passo = evento.key === "ArrowDown" ? 1 : -1;
      selecionada = (selecionada + passo + resultados.length) % resultados.length;
      desenharSugestoes();
    } else if (evento.key === "Enter" && selecionada >= 0) {
      evento.preventDefault();
      escolher(selecionada);
    } else if (evento.key === "Escape") {
      fecharSugestoes();
    }
  });

  /* mousedown, e não click: o click viria depois do blur, com a lista já fechada. */
  sugestoes.addEventListener("mousedown", function (evento) {
    var botao = evento.target.closest(".sugestao");
    if (!botao) return;
    evento.preventDefault();
    escolher(Number(botao.dataset.i));
  });

  destino.addEventListener("blur", function () { setTimeout(fecharSugestoes, 120); });

  /* ----------------------------------------------------------------------
     Geração do roteiro pela API (RQ004)
     ---------------------------------------------------------------------- */

  var falhaGeracao = document.getElementById("falhaGeracao");
  var acoesFalha = document.getElementById("acoesFalha");
  var avisoReserva = document.getElementById("avisoReserva");
  var idViagem = null;   /* criada uma vez; tentar de novo reaproveita a mesma */

  function mostrarPainel(painel) {
    form.hidden = true;
    document.getElementById("progresso").hidden = true;
    painelGerando.setAttribute("data-ativo", painel === "gerando" ? "true" : "false");
    painelPronto.setAttribute("data-ativo", painel === "pronto" ? "true" : "false");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* As etapas avançam no ritmo de uma resposta típica e param na última,
     que só se completa quando a API responder. */
  function animarEtapas() {
    etapas.forEach(function (etapa) { etapa.setAttribute("data-feito", "false"); });
    var i = 0;
    return setInterval(function () {
      if (i < etapas.length - 1) etapas[i++].setAttribute("data-feito", "true");
    }, 1100);
  }

  function criarViagem() {
    if (idViagem) return Promise.resolve(idViagem);
    var corpo = {
      destino: destino.value.trim(),
      data_inicio: ida.value,
      data_fim: volta.value,
      estilo_viagem: ritmo.value,
      /* O assistente só marca os interesses; o nível fica no máximo. Os
         níveis podem ser ajustados depois, no Perfil de viajante. */
      preferencias: interesses().map(function (c) { return { categoria: c, nivel_interesse: 5 }; })
    };
    return API.post("/viagens/", corpo).then(function (viagem) {
      idViagem = viagem.id_viagem;
      return idViagem;
    });
  }

  function gerarRoteiro(substituir) {
    mostrarPainel("gerando");
    falhaGeracao.hidden = true;
    acoesFalha.hidden = true;
    var animacao = animarEtapas();

    criarViagem()
      .then(function (id) { return API.post("/viagens/" + id + "/gerar-roteiro/", { substituir: Boolean(substituir) }); })
      .then(function (resposta) {
        clearInterval(animacao);
        etapas.forEach(function (etapa) { etapa.setAttribute("data-feito", "true"); });
        setTimeout(function () { concluir(resposta); }, 450);
      })
      .catch(function (erro) {
        clearInterval(animacao);
        API.mostrarFalha(falhaGeracao, erro, "Não foi possível gerar o roteiro");
        falhaGeracao.hidden = false;
        acoesFalha.hidden = false;
        /* Se a viagem chegou a ser criada, dá para abri-la e gerar depois. */
        var link = document.getElementById("linkRoteiroVazio");
        link.hidden = !idViagem;
        if (idViagem) link.href = "roteiro.html?id=" + idViagem;
      });
  }

  function concluir(resposta) {
    var geracao = resposta.geracao;
    var viagem = resposta.viagem;
    var tempo = geracao.tempo_em_ms < 1000
      ? "menos de 1 segundo"
      : (geracao.tempo_em_ms / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " segundos";

    resumoPronto.textContent =
      geracao.total_de_atividades + " atividades em " + Trip.cidadeDe(viagem.destino) + ", distribuídas em " +
      Trip.dias(viagem.duracao) + ", com foco em " + Trip.listar(interesses()).toLowerCase() +
      ". Gerado por " + geracao.provedor + " em " + tempo + ".";

    avisoReserva.hidden = !geracao.aviso;
    document.getElementById("avisoReservaTexto").textContent = geracao.aviso || "";

    linkRoteiro.href = "roteiro.html?id=" + viagem.id_viagem;
    mostrarPainel("pronto");
  }

  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    if (!validarPasso(1)) { irPara(1); return; }
    if (!validarPasso(2)) { irPara(2); return; }
    document.getElementById("btnGerar").disabled = true;
    gerarRoteiro(false);
  });

  document.getElementById("btnTentarDeNovo").addEventListener("click", function () {
    gerarRoteiro(false);
  });

  /* Gera de novo para a mesma viagem, substituindo o roteiro anterior. */
  document.getElementById("btnRefazer").addEventListener("click", function () {
    gerarRoteiro(true);
  });

  irPara(1);
})();
