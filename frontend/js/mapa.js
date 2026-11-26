/* =========================================================================
   TripScripter — visualização do roteiro em mapa (RQ006)

   Usa Leaflet com blocos do OpenStreetMap. A escolha por OpenStreetMap em
   vez de um provedor pago atende à restrição de recursos financeiros
   registrada na Declaração de Escopo: não exige chave de API nem cadastro
   de cartão. A atribuição ao OpenStreetMap é exigida pela licença dos
   dados e aparece no canto do mapa.

   A viagem vem de ?id= na URL e é lida da API (GET /api/viagens/<id>/).
   Cada marcador tem o número da ordem de visita e a cor da categoria do
   local. Locais sem coordenada (incluídos à mão, ainda sem geocodificação)
   aparecem na lista, marcados como "sem localização", mas não no mapa.
   ========================================================================= */

(function () {
  "use strict";

  if (!API.exigirLogin()) return;
  API.prepararBarra();

  var e = Trip.escapar;
  var idViagem = new URLSearchParams(window.location.search).get("id");
  if (!idViagem) { window.location.replace("viagens.html"); return; }

  var abasDias = document.getElementById("abasDias");
  var listaParadas = document.getElementById("paradasMapa");
  var viagem = null;
  var diaAtivo = 0;

  document.getElementById("linkLista").href = "roteiro.html?id=" + encodeURIComponent(idViagem);

  /* ----------------------------------------------------------------------
     Mapa
     ---------------------------------------------------------------------- */

  var mapa = L.map("mapa", { zoomControl: true, scrollWheelZoom: false });

  /* Os blocos vêm da CARTO, que redistribui dados do OpenStreetMap. Os
     servidores do próprio OpenStreetMap recusam requisições de páginas
     abertas diretamente do disco (protocolo file://), por não conseguirem
     identificar a aplicação; a CARTO atende essas requisições. A atribuição
     às duas fontes é exigida pelas respectivas licenças. */
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; colaboradores do <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19
}).addTo(mapa);

  mapa.setView([20, 0], 2);

  var camadas = [];
  var marcadores = {};

  function temCoordenada(atividade) {
    return atividade.local.latitude !== null && atividade.local.longitude !== null;
  }

  function ponto(atividade) {
    return [Number(atividade.local.latitude), Number(atividade.local.longitude)];
  }

  function iconeNumerado(numero, cor) {
    return L.divIcon({
      html: '<span class="marcador-numero" style="background:' + cor + '">' + numero + "</span>",
      className: "",
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -18]
    });
  }

  function descricao(a) {
    var partes = [];
    if (a.hora_sugerida) partes.push("<span>" + e(Trip.hora(a.hora_sugerida)) + "</span>");
    var custo = Trip.custo(a.custo_estimado);
    if (custo) partes.push("<span>" + (custo === "Gratuito" ? custo : "Custo " + e(custo) + " (moeda local)") + "</span>");
    return partes.join("");
  }

  function limparMapa() {
    camadas.forEach(function (camada) { mapa.removeLayer(camada); });
    camadas = [];
    marcadores = {};
  }

  function desenharMapa() {
    limparMapa();
    var atividades = viagem.dias[diaAtivo].atividades;
    var localizadas = atividades.filter(temCoordenada);

    if (!localizadas.length) {
      mapa.setView([20, 0], 2);
      return;
    }

    var pontos = localizadas.map(ponto);

    if (pontos.length > 1) {
      camadas.push(L.polyline(pontos, { color: "#0e7c70", weight: 3, opacity: 0.85, dashArray: "8 6" }).addTo(mapa));
    }

    atividades.forEach(function (a, indice) {
      if (!temCoordenada(a)) return;
      var marcador = L.marker(ponto(a), {
        icon: iconeNumerado(indice + 1, Trip.corDaCategoria(a.local.categoria)),
        title: a.local.nome
      }).addTo(mapa);

      marcador.bindPopup(
        "<strong>" + e(a.local.nome) + "</strong>" +
        '<div class="popup-meta">' + descricao(a) + "</div>" +
        (a.local.categoria ? '<div style="margin-top:8px">' + Trip.etiquetaDaCategoria(a.local.categoria) + "</div>" : "")
      );
      marcador.on("click", function () { destacar(a.id_atividade); });

      camadas.push(marcador);
      marcadores[a.id_atividade] = marcador;
    });

    mapa.fitBounds(L.latLngBounds(pontos), { padding: [45, 45], maxZoom: 14 });
  }

  /* ----------------------------------------------------------------------
     Lista lateral, sincronizada com o mapa
     ---------------------------------------------------------------------- */

  function desenharLista() {
    var atividades = viagem.dias[diaAtivo].atividades;

    if (!atividades.length) {
      listaParadas.innerHTML = '<li class="vazio">Nenhuma atividade neste dia.</li>';
      return;
    }

    listaParadas.innerHTML = atividades.map(function (a, indice) {
      var semCoordenada = !temCoordenada(a);
      var meta = [Trip.hora(a.hora_sugerida), a.local.categoria, semCoordenada ? "sem localização" : ""]
        .filter(Boolean).join(" · ");
      return "" +
        "<li>" +
          '<button type="button" class="parada-mapa" data-atividade="' + a.id_atividade + '"' +
                  (semCoordenada ? " disabled" : "") + ">" +
            '<span class="parada-mapa__numero" style="background:' + Trip.corDaCategoria(a.local.categoria) + '">' + (indice + 1) + "</span>" +
            '<span class="parada-mapa__texto">' +
              '<span class="parada-mapa__nome">' + e(a.local.nome) + "</span>" +
              '<span class="parada-mapa__meta">' + e(meta) + "</span>" +
            "</span>" +
          "</button>" +
        "</li>";
    }).join("");
  }

  function destacar(idAtividade) {
    listaParadas.querySelectorAll(".parada-mapa").forEach(function (botao) {
      botao.setAttribute("aria-current", Number(botao.dataset.atividade) === idAtividade ? "true" : "false");
    });
  }

  listaParadas.addEventListener("click", function (evento) {
    var botao = evento.target.closest(".parada-mapa");
    if (!botao || botao.disabled) return;
    var id = Number(botao.dataset.atividade);
    var marcador = marcadores[id];
    if (!marcador) return;
    mapa.setView(marcador.getLatLng(), 15, { animate: true });
    marcador.openPopup();
    destacar(id);
  });

  /* ----------------------------------------------------------------------
     Abas de dia
     ---------------------------------------------------------------------- */

  function desenharAbas() {
    abasDias.innerHTML = viagem.dias.map(function (dia, indice) {
      return '<button class="dia-aba" role="tab" data-dia="' + indice + '" aria-selected="' +
             (indice === diaAtivo) + '">Dia ' + dia.ordem + " · " + e(Trip.diaCurto(dia.data)) + "</button>";
    }).join("");
  }

  abasDias.addEventListener("click", function (evento) {
    var aba = evento.target.closest(".dia-aba");
    if (!aba) return;
    diaAtivo = Number(aba.dataset.dia);
    desenharAbas();
    desenharMapa();
    desenharLista();
  });

  /* ----------------------------------------------------------------------
     Início
     ---------------------------------------------------------------------- */

  API.get("/viagens/" + encodeURIComponent(idViagem) + "/")
    .then(function (dados) {
      viagem = dados;
      document.title = "Mapa de " + Trip.cidadeDe(viagem.destino) + " — TripScripter";
      document.getElementById("destinoTitulo").textContent = viagem.destino;
      document.getElementById("resumoViagem").textContent =
        Trip.periodo(viagem.data_inicio, viagem.data_fim) + " · " + Trip.dias(viagem.duracao);
      desenharAbas();
      desenharMapa();
      desenharLista();
    })
    .catch(function (erro) {
      document.getElementById("destinoTitulo").textContent = "Mapa";
      API.mostrarFalha(listaParadas, erro, "Não foi possível carregar o roteiro");
    });
})();
