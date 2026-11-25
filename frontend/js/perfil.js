/* =========================================================================
   TripScripter — perfil de viajante

   Três blocos:
   - dados da conta (GET /api/usuario/);
   - interesses, com nível de 1 a 5 por categoria (GET e PUT /api/preferencias/).
     São os mesmos níveis que o gerador de roteiro envia à IA;
   - resumo e lugares das viagens concluídas, lidos do histórico.

   A lista de desejos do protótipo não foi implementada: o banco de dados
   não tem onde guardá-la, e acrescentá-la exige uma tabela nova no modelo.
   ========================================================================= */

(function () {
  "use strict";

  if (!API.exigirLogin()) return;
  API.prepararBarra();

  var e = Trip.escapar;
  var MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

  /* ----------------------------------------------------------------------
     Conta
     ---------------------------------------------------------------------- */

  function iniciais(nome) {
    var partes = String(nome).trim().split(/\s+/);
    return (partes[0][0] + (partes.length > 1 ? partes[partes.length - 1][0] : "")).toUpperCase();
  }

  API.get("/usuario/")
    .then(function (u) {
      document.getElementById("iniciais").textContent = iniciais(u.nome);
      document.getElementById("perfilNome").textContent = u.nome;
      document.getElementById("perfilEmail").textContent = u.email;
      var desde = new Date(u.data_cadastro);
      document.getElementById("perfilDesde").textContent =
        "Viajante desde " + MESES[desde.getMonth()] + " de " + desde.getFullYear();
    })
    .catch(function (erro) { API.mostrarFalha(document.getElementById("conta"), erro, "Não foi possível carregar a conta"); });

  /* ----------------------------------------------------------------------
     Interesses
     ---------------------------------------------------------------------- */

  var lista = document.getElementById("listaPreferencias");
  var status = document.getElementById("statusPreferencias");
  var niveis = {};   /* categoria → 0 (não) a 5 */

  function desenharPreferencias() {
    lista.innerHTML = Trip.CATEGORIAS.map(function (categoria) {
      var atual = niveis[categoria] || 0;
      var botoes = [0, 1, 2, 3, 4, 5].map(function (n) {
        return '<button type="button" class="nivel' + (n === 0 ? " nivel--nenhum" : "") + '" data-categoria="' + e(categoria) +
               '" data-nivel="' + n + '" aria-pressed="' + (atual === n) + '" aria-label="' + e(categoria) + ": " +
               (n === 0 ? "sem interesse" : "nível " + n) + '">' + (n === 0 ? "Não" : n) + "</button>";
      }).join("");
      return '<li class="preferencia">' + Trip.etiquetaDaCategoria(categoria) +
             '<span class="niveis" role="group" aria-label="Interesse em ' + e(categoria) + '">' + botoes + "</span></li>";
    }).join("");
  }

  lista.addEventListener("click", function (evento) {
    var botao = evento.target.closest(".nivel");
    if (!botao) return;
    niveis[botao.dataset.categoria] = Number(botao.dataset.nivel);
    status.textContent = "";
    desenharPreferencias();
  });

  document.getElementById("formPreferencias").addEventListener("submit", function (evento) {
    evento.preventDefault();
    var preferencias = Trip.CATEGORIAS
      .filter(function (c) { return niveis[c] > 0; })
      .map(function (c) { return { categoria: c, nivel_interesse: niveis[c] }; });

    var botao = document.getElementById("btnSalvar");
    botao.disabled = true;
    status.textContent = "Salvando…";
    API.put("/preferencias/", { preferencias: preferencias })
      .then(function () { status.textContent = "Interesses salvos."; })
      .catch(function (erro) { status.textContent = erro.message; })
      .then(function () { botao.disabled = false; });
  });

  API.get("/preferencias/")
    .then(function (dados) {
      dados.preferencias.forEach(function (p) { niveis[p.categoria] = p.nivel_interesse; });
      desenharPreferencias();
    })
    .catch(function (erro) { API.mostrarFalha(lista, erro, "Não foi possível carregar os interesses"); });

  /* ----------------------------------------------------------------------
     Viagens concluídas: resumo e lugares
     ---------------------------------------------------------------------- */

  var areaLocais = document.getElementById("locaisVisitados");

  function mesAno(iso) {
    return MESES[Number(iso.slice(5, 7)) - 1] + " " + iso.slice(0, 4);
  }

  API.get("/viagens/historico/")
    .then(function (viagens) {
      /* O resumo da lista não traz os lugares: cada viagem é lida por inteiro. */
      return Promise.all(viagens.map(function (v) { return API.get("/viagens/" + v.id_viagem + "/"); }));
    })
    .then(function (viagens) {
      var paises = {}, cidades = {}, locais = {};

      viagens.forEach(function (viagem) {
        paises[Trip.semAcento(Trip.paisDe(viagem.destino))] = true;
        cidades[Trip.semAcento(Trip.cidadeDe(viagem.destino))] = true;
        viagem.dias.forEach(function (dia) {
          dia.atividades.forEach(function (a) {
            /* O mesmo local em duas viagens conta uma vez, com a visita mais recente. */
            var anterior = locais[a.local.id_local];
            if (!anterior || anterior.quando < viagem.data_fim) {
              locais[a.local.id_local] = { local: a.local, destino: viagem.destino, quando: viagem.data_fim };
            }
          });
        });
      });

      var visitados = Object.keys(locais).map(function (id) { return locais[id]; })
        .sort(function (a, b) { return b.quando.localeCompare(a.quando) || a.local.nome.localeCompare(b.local.nome); });

      document.getElementById("totalPaises").textContent = Object.keys(paises).length;
      document.getElementById("totalCidades").textContent = Object.keys(cidades).length;
      document.getElementById("totalLocais").textContent = visitados.length;

      if (!visitados.length) {
        areaLocais.innerHTML = '<p class="vazio-busca">Os lugares aparecem aqui depois que uma viagem termina.</p>';
        return;
      }

      areaLocais.innerHTML = '<ul class="locais">' + visitados.map(function (v) {
        return '<li class="local-visitado">' +
          '<span class="local-visitado__nome">' + e(v.local.nome) + "</span>" +
          '<span class="local-visitado__onde">' + e(Trip.cidadeDe(v.destino) + " · " + mesAno(v.quando)) + "</span>" +
          (v.local.categoria ? "<span>" + Trip.etiquetaDaCategoria(v.local.categoria) + "</span>" : "") +
        "</li>";
      }).join("") + "</ul>";
    })
    .catch(function (erro) { API.mostrarFalha(areaLocais, erro, "Não foi possível carregar as viagens"); });
})();
