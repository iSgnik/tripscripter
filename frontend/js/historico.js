/* =========================================================================
   TripScripter — histórico de viagens (RQ011)

   Lista as viagens já concluídas (GET /api/viagens/historico/), agrupadas
   por ano, com resumo em números e busca por destino ou interesse. A busca
   ignora acentos e diferenças de maiúsculas, de modo que "Sao Paulo"
   encontra "São Paulo".

   "Usar como modelo" cria uma nova viagem com o mesmo roteiro, a partir da
   data escolhida (POST /api/viagens/<id>/reaproveitar/). As notas pessoais
   não são copiadas, porque se referem à experiência da viagem original.
   ========================================================================= */

(function () {
  "use strict";

  if (!API.exigirLogin()) return;
  API.prepararBarra();

  var e = Trip.escapar;
  var listaAnos = document.getElementById("listaAnos");
  var busca = document.getElementById("busca");
  var viagens = [];

  /* ----------------------------------------------------------------------
     Resumo em números
     ---------------------------------------------------------------------- */

  function preencherResumo() {
    var paises = {};
    var dias = 0;
    viagens.forEach(function (viagem) {
      paises[Trip.semAcento(Trip.paisDe(viagem.destino))] = true;
      dias += viagem.duracao;
    });
    document.getElementById("totalViagens").textContent = viagens.length;
    document.getElementById("totalPaises").textContent = Object.keys(paises).length;
    document.getElementById("totalDias").textContent = dias;
  }

  /* ----------------------------------------------------------------------
     Busca sem acentos e sem distinção de maiúsculas
     ---------------------------------------------------------------------- */

  function filtrar(termo) {
    var alvo = Trip.semAcento(termo);
    if (!alvo) return viagens;
    return viagens.filter(function (viagem) {
      if (Trip.semAcento(viagem.destino).indexOf(alvo) !== -1) return true;
      return viagem.categorias.some(function (c) { return Trip.semAcento(c).indexOf(alvo) !== -1; });
    });
  }

  /* ----------------------------------------------------------------------
     Desenho da lista
     ---------------------------------------------------------------------- */

  var ICONE_CALENDARIO =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">' +
    '<rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 11h18"></path></svg>';
  var ICONE_RELOGIO =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">' +
    '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></svg>';

  function cartao(viagem) {
    var atividades = viagem.total_atividades === 1 ? "1 atividade" : viagem.total_atividades + " atividades";
    return "" +
      '<li class="viagem">' +
        Trip.capa(viagem, Trip.situacao(viagem)) +
        '<div class="viagem__corpo">' +
          '<h3 class="viagem__destino">' + e(viagem.destino) + "</h3>" +
          '<span class="viagem__dado">' + ICONE_CALENDARIO + e(Trip.periodo(viagem.data_inicio, viagem.data_fim)) + "</span>" +
          '<span class="viagem__dado">' + ICONE_RELOGIO + e(Trip.dias(viagem.duracao) + " · " + atividades) + "</span>" +
          (viagem.categorias.length
            ? '<div class="viagem__interesses">' + viagem.categorias.map(Trip.etiquetaDaCategoria).join("") + "</div>"
            : "") +
          '<div class="viagem__acoes">' +
            '<a class="botao botao--claro" href="roteiro.html?id=' + viagem.id_viagem + '">Ver roteiro</a>' +
            '<button type="button" class="botao botao--fantasma" data-modelo="' + viagem.id_viagem + '" ' +
              'title="Criar uma viagem com este roteiro"' + (viagem.total_atividades ? "" : " disabled") + ">Usar como modelo</button>" +
          "</div>" +
        "</div>" +
      "</li>";
  }

  function desenhar(lista) {
    if (!viagens.length) {
      listaAnos.innerHTML = '<p class="vazio-busca">Nenhuma viagem concluída ainda. Elas aparecem aqui depois da data de retorno.</p>';
      return;
    }
    if (!lista.length) {
      listaAnos.innerHTML = '<p class="vazio-busca">Nenhuma viagem encontrada para essa busca.</p>';
      return;
    }

    var anos = [];
    lista.forEach(function (viagem) {
      var ano = Trip.anoDe(viagem.data_fim);
      if (anos.indexOf(ano) === -1) anos.push(ano);
    });
    anos.sort(function (a, b) { return b - a; });

    listaAnos.innerHTML = anos.map(function (ano) {
      var cartoes = lista
        .filter(function (viagem) { return Trip.anoDe(viagem.data_fim) === ano; })
        .map(cartao)
        .join("");
      return '<section class="ano"><div class="ano__titulo"><h2>' + ano + '</h2></div><ul class="viagens">' + cartoes + "</ul></section>";
    }).join("");
  }

  /* ----------------------------------------------------------------------
     Usar como modelo (RQ011)
     ---------------------------------------------------------------------- */

  var dialogo = document.getElementById("dialogoModelo");
  var campoData = document.getElementById("novaIda");
  var erroModelo = document.getElementById("erroModelo");
  var confirmar = document.getElementById("confirmarModelo");
  var modelo = null;

  listaAnos.addEventListener("click", function (evento) {
    var botao = evento.target.closest("[data-modelo]");
    if (!botao) return;
    modelo = viagens.filter(function (v) { return v.id_viagem === Number(botao.dataset.modelo); })[0];
    document.getElementById("textoModelo").textContent =
      "Uma nova viagem para " + modelo.destino + " será criada com o mesmo roteiro de " +
      Trip.dias(modelo.duracao) + ", a partir da data escolhida. As notas pessoais não são copiadas.";
    campoData.min = Trip.hojeISO();
    campoData.value = "";
    erroModelo.classList.remove("esta-visivel");
    dialogo.showModal();
    campoData.focus();
  });

  document.getElementById("cancelarModelo").addEventListener("click", function () { dialogo.close(); });

  document.getElementById("formModelo").addEventListener("submit", function (evento) {
    evento.preventDefault();
    if (!campoData.value) { campoData.focus(); return; }
    confirmar.disabled = true;
    API.post("/viagens/" + modelo.id_viagem + "/reaproveitar/", { data_inicio: campoData.value })
      .then(function (nova) { window.location.href = "roteiro.html?id=" + nova.id_viagem; })
      .catch(function (erro) {
        erroModelo.textContent = erro.message;
        erroModelo.classList.add("esta-visivel");
        confirmar.disabled = false;
      });
  });

  /* ----------------------------------------------------------------------
     Início
     ---------------------------------------------------------------------- */

  busca.addEventListener("input", function () { desenhar(filtrar(busca.value)); });

  API.get("/viagens/historico/")
    .then(function (dados) {
      viagens = dados;
      preencherResumo();
      desenhar(viagens);
    })
    .catch(function (erro) {
      API.mostrarFalha(listaAnos, erro, "Não foi possível carregar o histórico");
    });
})();
