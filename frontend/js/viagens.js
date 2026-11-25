/* =========================================================================
   TripScripter — lista de viagens (RQ003)

   Mostra as viagens em andamento e futuras do usuário (GET /api/viagens/).
   As já encerradas ficam na tela de histórico.
   ========================================================================= */

(function () {
  "use strict";

  if (!API.exigirLogin()) return;
  API.prepararBarra();

  var lista = document.getElementById("listaViagens");
  var resumo = document.getElementById("resumoLista");

  var ICONE_CALENDARIO =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">' +
    '<rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 11h18"></path></svg>';
  var ICONE_RELOGIO =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">' +
    '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></svg>';

  function cartao(viagem) {
    var e = Trip.escapar;
    var categorias = viagem.categorias.slice(0, 3).map(Trip.etiquetaDaCategoria).join("") +
      (viagem.categorias.length > 3 ? '<span class="interesse-etiqueta">+' + (viagem.categorias.length - 3) + "</span>" : "");
    var atividades = viagem.total_atividades
      ? viagem.total_atividades + (viagem.total_atividades === 1 ? " atividade" : " atividades")
      : "roteiro ainda não gerado";

    return "" +
      '<li class="viagem">' +
        Trip.capa(viagem, Trip.situacao(viagem)) +
        '<div class="viagem__corpo">' +
          '<h2 class="viagem__destino">' + e(viagem.destino) + "</h2>" +
          '<span class="viagem__dado">' + ICONE_CALENDARIO + e(Trip.periodo(viagem.data_inicio, viagem.data_fim)) + "</span>" +
          '<span class="viagem__dado">' + ICONE_RELOGIO + e(Trip.dias(viagem.duracao) + " · " + atividades) + "</span>" +
          (categorias ? '<div class="viagem__interesses">' + categorias + "</div>" : "") +
          '<a class="botao botao--primario" href="roteiro.html?id=' + viagem.id_viagem + '" style="margin-top:12px">' +
            (viagem.total_atividades ? "Ver roteiro" : "Gerar roteiro") +
          "</a>" +
        "</div>" +
      "</li>";
  }

  function vazio() {
    return "" +
      '<div class="vazio-acao">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          '<path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>' +
        "<h2>Nenhuma viagem planejada</h2>" +
        "<p>Comece criando sua primeira viagem: o roteiro é montado dia a dia, a partir dos seus interesses.</p>" +
        '<a class="botao botao--primario" href="nova-viagem.html">Criar primeira viagem</a>' +
      "</div>";
  }

  API.get("/viagens/")
    .then(function (viagens) {
      if (!viagens.length) {
        resumo.textContent = "Você ainda não tem viagens planejadas.";
        lista.innerHTML = vazio();
        return;
      }
      resumo.textContent = viagens.length === 1
        ? "Uma viagem planejada. Abra para ver o roteiro dia a dia."
        : viagens.length + " viagens planejadas. Abra uma para ver o roteiro dia a dia.";
      lista.innerHTML = '<ul class="viagens">' + viagens.map(cartao).join("") + "</ul>";
    })
    .catch(function (erro) {
      API.mostrarFalha(lista, erro, "Não foi possível carregar as viagens");
    });
})();
