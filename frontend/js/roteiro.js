/* =========================================================================
   TripScripter — tela de roteiro (RQ004, RQ005, RQ007 e RQ008)

   A viagem vem do parâmetro ?id= da URL (roteiro.html?id=3) e é lida da API
   (GET /api/viagens/3/). Cada alteração é gravada no banco na hora:

     incluir local        POST   /api/dias/<id>/atividades/
     mudar a ordem        POST   /api/dias/<id>/reordenar/
     remover atividade    DELETE /api/atividades/<id>/
     notas pessoais       POST   /api/atividades/<id>/notas/, PATCH e DELETE /api/notas/<id>/
     gerar o roteiro      POST   /api/viagens/<id>/gerar-roteiro/

   Depois de cada alteração a viagem é lida de novo, para que a tela mostre
   sempre o que está gravado, e não uma cópia que pode ter divergido.
   ========================================================================= */

(function () {
  "use strict";

  if (!API.exigirLogin()) return;
  API.prepararBarra();

  var e = Trip.escapar;
  var idViagem = new URLSearchParams(window.location.search).get("id");
  if (!idViagem) { window.location.replace("viagens.html"); return; }

  var trilha = document.getElementById("trilha");
  var abasDias = document.getElementById("abasDias");
  var avisos = document.getElementById("avisos");
  var btnIncluir = document.getElementById("btnIncluir");
  var btnRegerar = document.getElementById("btnRegerar");
  var formIncluir = document.getElementById("formIncluir");

  var viagem = null;
  var diaAtivo = 0;
  var editando = null;   /* "nova:<id_atividade>" ou "nota:<id_nota>" */

  document.getElementById("linkMapa").href = "mapa.html?id=" + encodeURIComponent(idViagem);

  document.getElementById("novaCategoria").innerHTML =
    '<option value="">Sem categoria</option>' +
    Trip.CATEGORIAS.map(function (c) { return "<option>" + e(c) + "</option>"; }).join("");

  /* ----------------------------------------------------------------------
     Ícones
     ---------------------------------------------------------------------- */

  function icone(caminho) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + caminho + "</svg>";
  }

  var SUBIR = icone('<path d="M18 15l-6-6-6 6"></path>');
  var DESCER = icone('<path d="M6 9l6 6 6-6"></path>');
  var LAPIS = icone('<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"></path>');
  var LIXEIRA = icone('<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"></path>');

  /* ----------------------------------------------------------------------
     Carregamento
     ---------------------------------------------------------------------- */

  function totalDeAtividades() {
    return viagem.dias.reduce(function (soma, dia) { return soma + dia.atividades.length; }, 0);
  }

  function carregar() {
    return API.get("/viagens/" + encodeURIComponent(idViagem) + "/").then(function (dados) {
      viagem = dados;
      if (diaAtivo >= viagem.dias.length) diaAtivo = 0;
      desenharTudo();
    });
  }

  function falhar(erro) {
    avisos.innerHTML = "";
    var caixa = document.createElement("div");
    caixa.style.marginBottom = "22px";
    API.mostrarFalha(caixa, erro, "A alteração não foi gravada");
    avisos.appendChild(caixa);
  }

  /* ----------------------------------------------------------------------
     Desenho
     ---------------------------------------------------------------------- */

  function desenharTudo() {
    document.title = "Roteiro de " + Trip.cidadeDe(viagem.destino) + " — TripScripter";
    document.getElementById("destinoTitulo").textContent = viagem.destino;
    document.getElementById("resumoViagem").textContent =
      Trip.periodo(viagem.data_inicio, viagem.data_fim) + " · " + Trip.dias(viagem.duracao) +
      (viagem.estilo_viagem ? " · ritmo " + viagem.estilo_viagem.toLowerCase() : "");

    var temAtividades = totalDeAtividades() > 0;
    btnIncluir.hidden = !temAtividades;
    btnRegerar.hidden = !temAtividades;
    if (!temAtividades) formIncluir.hidden = true;

    desenharAbas();
    if (temAtividades) desenharDia(); else desenharRoteiroVazio();
  }

  function desenharAbas() {
    abasDias.hidden = totalDeAtividades() === 0;
    abasDias.innerHTML = viagem.dias.map(function (dia, indice) {
      return '<button class="dia-aba" role="tab" data-dia="' + indice + '" aria-selected="' +
             (indice === diaAtivo) + '">Dia ' + dia.ordem + " · " + e(Trip.diaCurto(dia.data)) + "</button>";
    }).join("");
  }

  function modoVazio(ligado) { trilha.setAttribute("data-vazio", ligado ? "true" : "false"); }

  function desenharRoteiroVazio() {
    modoVazio(true);
    trilha.innerHTML =
      '<div class="vazio-acao">' +
        icone('<path d="M12 3l1.9 5.8H20l-4.9 3.6 1.9 5.8-5-3.6-5 3.6 1.9-5.8L4 8.8h6.1z"></path>') +
        "<h2>Roteiro ainda não gerado</h2>" +
        "<p>A inteligência artificial monta as atividades de cada um dos " + viagem.dias.length +
        " dias a partir dos seus interesses. Depois, você pode reordenar, remover e incluir locais.</p>" +
        '<button class="botao botao--primario" type="button" data-gerar>Gerar roteiro com IA</button>' +
      "</div>";
  }

  function desenharNotas(atividade) {
    return atividade.notas.map(function (nota) {
      if (editando === "nota:" + nota.id_nota) return editorDeNota(nota.texto, "nota:" + nota.id_nota);
      return '<div class="parada__nota">' +
        '<span><strong>Sua nota</strong><span class="parada__nota-texto">' + e(nota.texto) + "</span></span>" +
        '<span class="parada__nota-acoes">' +
          '<button type="button" class="botao-icone botao-icone--pequeno" data-acao="editar-nota" data-nota="' + nota.id_nota + '" aria-label="Editar nota">' + LAPIS + "</button>" +
          '<button type="button" class="botao-icone botao-icone--pequeno botao-icone--perigo" data-acao="apagar-nota" data-nota="' + nota.id_nota + '" aria-label="Apagar nota">' + LIXEIRA + "</button>" +
        "</span></div>";
    }).join("");
  }

  function editorDeNota(texto, chave) {
    return '<div class="nota-editor" data-editor="' + chave + '">' +
      '<label class="campo__rotulo" for="editor-' + chave + '">Nota pessoal</label>' +
      '<textarea id="editor-' + chave + '" maxlength="2000" placeholder="Observações, dicas ou lembretes…">' + e(texto) + "</textarea>" +
      '<div class="nota-editor__acoes">' +
        '<button type="button" class="botao botao--primario" data-acao="salvar-nota" data-chave="' + chave + '">Salvar nota</button>' +
        '<button type="button" class="botao botao--fantasma" data-acao="cancelar-nota">Cancelar</button>' +
      "</div></div>";
  }

  function desenharDia() {
    modoVazio(false);
    var atividades = viagem.dias[diaAtivo].atividades;

    if (!atividades.length) {
      modoVazio(true);
      trilha.innerHTML = '<p class="vazio">Nenhuma atividade neste dia. Use “Adicionar local” para montar o seu.</p>';
      return;
    }

    trilha.innerHTML = atividades.map(function (a, indice) {
      var local = a.local;
      var meta = [];
      if (Trip.custo(a.custo_estimado)) {
        meta.push(a.custo_estimado == 0
          ? "<span>Gratuito</span>"
          : '<span>Custo estimado ' + e(Trip.custo(a.custo_estimado)) + ' <span class="custo__moeda">(moeda local)</span></span>');
      }
      if (local.horario_funcionamento) meta.push("<span>" + e(local.horario_funcionamento) + "</span>");
      if (local.endereco) meta.push("<span>" + e(local.endereco) + "</span>");

      var editorNovo = editando === "nova:" + a.id_atividade ? editorDeNota("", "nova:" + a.id_atividade) : "";

      return "" +
        '<article class="parada" data-atividade="' + a.id_atividade + '">' +
          '<span class="parada__hora">' + (e(Trip.hora(a.hora_sugerida)) || "—") + "</span>" +
          '<div class="parada__cartao">' +
            '<div class="parada__topo">' +
              '<h2 class="parada__nome">' + e(local.nome) + "</h2>" +
              '<span class="parada__etiquetas">' + Trip.etiquetaDaCategoria(local.categoria) + "</span>" +
            "</div>" +
            (meta.length ? '<div class="parada__meta">' + meta.join("") + "</div>" : "") +
            desenharNotas(a) +
            editorNovo +
            '<div class="parada__acoes">' +
              '<button class="botao botao--fantasma" data-acao="nova-nota">Adicionar nota</button>' +
              '<button class="botao botao--fantasma" data-acao="remover">Remover do roteiro</button>' +
              '<span class="parada__mover">' +
                '<button type="button" class="botao-icone" data-acao="subir" aria-label="Mover para cima"' + (indice === 0 ? " disabled" : "") + ">" + SUBIR + "</button>" +
                '<button type="button" class="botao-icone" data-acao="descer" aria-label="Mover para baixo"' + (indice === atividades.length - 1 ? " disabled" : "") + ">" + DESCER + "</button>" +
              "</span>" +
            "</div>" +
          "</div>" +
        "</article>";
    }).join("");

    var aberto = trilha.querySelector(".nota-editor textarea");
    if (aberto) aberto.focus();
  }

  /* ----------------------------------------------------------------------
     Operações
     ---------------------------------------------------------------------- */

  /* Marca o cartão como ocupado durante a chamada, para evitar clique duplo. */
  function executar(cartao, operacao) {
    if (cartao) cartao.setAttribute("data-ocupada", "true");
    avisos.innerHTML = "";
    return operacao().then(carregar).catch(function (erro) {
      falhar(erro);
      return carregar();
    });
  }

  function idsDoDia() {
    return viagem.dias[diaAtivo].atividades.map(function (a) { return a.id_atividade; });
  }

  function reordenar(ids) {
    return API.post("/dias/" + viagem.dias[diaAtivo].id_dia + "/reordenar/", { ordem: ids });
  }

  trilha.addEventListener("click", function (evento) {
    if (evento.target.closest("[data-gerar]")) { gerar(false); return; }

    var botao = evento.target.closest("button[data-acao]");
    if (!botao) return;
    var cartao = botao.closest(".parada");
    var idAtividade = cartao ? Number(cartao.dataset.atividade) : null;
    var acao = botao.dataset.acao;

    if (acao === "nova-nota") { editando = "nova:" + idAtividade; desenharDia(); return; }
    if (acao === "editar-nota") { editando = "nota:" + botao.dataset.nota; desenharDia(); return; }
    if (acao === "cancelar-nota") { editando = null; desenharDia(); return; }

    if (acao === "salvar-nota") {
      var texto = trilha.querySelector('[data-editor="' + botao.dataset.chave + '"] textarea').value.trim();
      if (!texto) { trilha.querySelector(".nota-editor textarea").focus(); return; }
      var partes = botao.dataset.chave.split(":");
      editando = null;
      executar(cartao, function () {
        return partes[0] === "nova"
          ? API.post("/atividades/" + partes[1] + "/notas/", { texto: texto })
          : API.patch("/notas/" + partes[1] + "/", { texto: texto });
      });
      return;
    }

    if (acao === "apagar-nota") {
      if (!window.confirm("Apagar esta nota?")) return;
      executar(cartao, function () { return API.remover("/notas/" + botao.dataset.nota + "/"); });
      return;
    }

    if (acao === "remover") {
      var nome = cartao.querySelector(".parada__nome").textContent;
      if (!window.confirm("Remover “" + nome + "” do roteiro? As notas dessa atividade também serão apagadas.")) return;
      executar(cartao, function () { return API.remover("/atividades/" + idAtividade + "/"); });
      return;
    }

    if (acao === "subir" || acao === "descer") {
      var ids = idsDoDia();
      var de = ids.indexOf(idAtividade);
      var para = acao === "subir" ? de - 1 : de + 1;
      ids.splice(para, 0, ids.splice(de, 1)[0]);
      executar(cartao, function () { return reordenar(ids); });
    }
  });

  /* ----------------------------------------------------------------------
     Troca de dia
     ---------------------------------------------------------------------- */

  abasDias.addEventListener("click", function (evento) {
    var aba = evento.target.closest(".dia-aba");
    if (!aba) return;
    diaAtivo = Number(aba.dataset.dia);
    editando = null;
    desenharAbas();
    desenharDia();
  });

  /* ----------------------------------------------------------------------
     Inclusão manual de local (RQ007)
     ---------------------------------------------------------------------- */

  btnIncluir.addEventListener("click", function () {
    formIncluir.hidden = !formIncluir.hidden;
    btnIncluir.textContent = formIncluir.hidden ? "Adicionar local" : "Fechar";
    if (!formIncluir.hidden) document.getElementById("novoLocal").focus();
  });

  formIncluir.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var campoNome = document.getElementById("novoLocal");
    var nome = campoNome.value.trim();
    if (!nome) { campoNome.focus(); return; }

    var hora = document.getElementById("novaHora").value || null;
    var categoria = document.getElementById("novaCategoria").value || null;
    var dia = viagem.dias[diaAtivo];

    executar(null, function () {
      return API.post("/dias/" + dia.id_dia + "/atividades/", {
        local: { nome: nome, categoria: categoria },
        hora_sugerida: hora
      }).then(function (nova) {
        /* A API inclui ao final do dia; aqui a atividade vai para a posição
           do horário informado, para o dia continuar em ordem cronológica. */
        var todas = dia.atividades.concat([nova]);
        todas.sort(function (a, b) {
          if (!a.hora_sugerida) return 1;
          if (!b.hora_sugerida) return -1;
          return a.hora_sugerida.localeCompare(b.hora_sugerida);
        });
        return reordenar(todas.map(function (a) { return a.id_atividade; }));
      });
    }).then(function () {
      campoNome.value = "";
      formIncluir.hidden = true;
      btnIncluir.textContent = "Adicionar local";
    });
  });

  /* ----------------------------------------------------------------------
     Geração pela IA (RQ004)
     ---------------------------------------------------------------------- */

  function gerar(substituir) {
    avisos.innerHTML = "";
    modoVazio(true);
    trilha.innerHTML = '<p class="carregando">Gerando o roteiro com inteligência artificial. Isso leva alguns segundos…</p>';
    btnRegerar.disabled = true;

    API.post("/viagens/" + encodeURIComponent(idViagem) + "/gerar-roteiro/", { substituir: substituir })
      .then(function (resposta) {
        viagem = resposta.viagem;
        diaAtivo = 0;
        desenharTudo();
        if (resposta.geracao.aviso) {
          avisos.innerHTML =
            '<div class="demonstrativo" role="note"><span><strong>Sugestões pré-definidas</strong>' +
            e(resposta.geracao.aviso) + "</span></div>";
        }
      })
      .catch(function (erro) {
        falhar(erro);
        desenharTudo();
      })
      .then(function () { btnRegerar.disabled = false; });
  }

  btnRegerar.addEventListener("click", function () {
    if (!window.confirm("Gerar um novo roteiro apaga as atividades e as notas atuais desta viagem. Continuar?")) return;
    gerar(true);
  });

  /* ----------------------------------------------------------------------
     Início
     ---------------------------------------------------------------------- */

  carregar().catch(function (erro) {
    document.getElementById("destinoTitulo").textContent = "Roteiro";
    modoVazio(true);
    API.mostrarFalha(trilha, erro, erro.status === 404 ? "Viagem não encontrada" : "Não foi possível carregar o roteiro");
  });
})();
