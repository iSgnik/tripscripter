/* =========================================================================
   TripScripter — acesso à API REST e sessão do usuário

   Todas as telas falam com o back-end por aqui. O endereço da API é
   http://127.0.0.1:8000/api, onde o "python manage.py runserver" a publica.
   Para apontar para outro endereço, rode no console do navegador:
       localStorage.setItem("tripscripter.api", "http://outro-endereco/api")

   Sessão: o login devolve um token, guardado no navegador e enviado em toda
   requisição no cabeçalho Authorization. Com "Manter conectado", o token
   fica no localStorage e sobrevive ao fechamento do navegador; sem a opção,
   fica no sessionStorage e some ao fechar a aba.

   Depende de js/comum.js, carregado antes.
   ========================================================================= */

var API = (function () {
  "use strict";

  var CHAVE_TOKEN = "tripscripter.token";
  var CHAVE_USUARIO = "tripscripter.usuario";

  /* O navegador pode bloquear o armazenamento (modo anônimo restrito, por
     exemplo). Nesse caso a sessão simplesmente não persiste. */
  function ler(armazenamento, chave) {
    try { return armazenamento.getItem(chave); } catch (e) { return null; }
  }

  function gravar(armazenamento, chave, valor) {
    try { armazenamento.setItem(chave, valor); } catch (e) { /* sem armazenamento */ }
  }

  function apagar(chave) {
    try { localStorage.removeItem(chave); sessionStorage.removeItem(chave); } catch (e) { /* idem */ }
  }

  var BASE = ler(localStorage, "tripscripter.api") || "http://127.0.0.1:8000/api";

  /* ----------------------------------------------------------------------
     Sessão
     ---------------------------------------------------------------------- */

  function token() {
    return ler(sessionStorage, CHAVE_TOKEN) || ler(localStorage, CHAVE_TOKEN);
  }

  function usuario() {
    var texto = ler(sessionStorage, CHAVE_USUARIO) || ler(localStorage, CHAVE_USUARIO);
    try { return texto ? JSON.parse(texto) : null; } catch (e) { return null; }
  }

  function iniciarSessao(resposta, manterConectado) {
    encerrarSessao();
    var destino = manterConectado ? localStorage : sessionStorage;
    gravar(destino, CHAVE_TOKEN, resposta.token);
    gravar(destino, CHAVE_USUARIO, JSON.stringify(resposta.usuario));
  }

  function encerrarSessao() {
    apagar(CHAVE_TOKEN);
    apagar(CHAVE_USUARIO);
  }

  /* Usada no topo das telas internas: sem sessão, volta ao login. */
  function exigirLogin() {
    if (!token()) {
      window.location.replace("index.html");
      return false;
    }
    return true;
  }

  /* ----------------------------------------------------------------------
     Requisições
     ---------------------------------------------------------------------- */

  function ErroDaAPI(status, mensagem, detalhes) {
    this.name = "ErroDaAPI";
    this.status = status;
    this.message = mensagem;
    this.detalhes = detalhes || null;
  }
  ErroDaAPI.prototype = Object.create(Error.prototype);

  /* A API responde {"erro": "...", "detalhes": {campo: ["mensagem"]}}.
     Quando há detalhes, a primeira mensagem de campo é a mais útil. */
  function mensagemDe(dados, status) {
    if (dados && dados.detalhes) {
      var primeiro = Object.keys(dados.detalhes)[0];
      var valor = dados.detalhes[primeiro];
      while (valor && typeof valor === "object") valor = Array.isArray(valor) ? valor[0] : valor[Object.keys(valor)[0]];
      if (valor) return String(valor);
    }
    if (dados && dados.erro) return dados.erro;
    return "O servidor respondeu com erro (" + status + ").";
  }

  function requisitar(metodo, caminho, corpo) {
    var cabecalhos = { "Accept": "application/json" };
    if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
    var t = token();
    if (t) cabecalhos["Authorization"] = "Bearer " + t;

    return fetch(BASE + caminho, {
      method: metodo,
      headers: cabecalhos,
      body: corpo === undefined ? undefined : JSON.stringify(corpo)
    }).catch(function () {
      throw new ErroDaAPI(0,
        "Não foi possível falar com o servidor. Confira se o back-end está rodando " +
        "(python manage.py runserver, na pasta backend).");
    }).then(function (resposta) {
      if (resposta.status === 204) return null;
      return resposta.json().catch(function () { return null; }).then(function (dados) {
        /* Token expirado ou inválido numa tela interna: volta ao login. */
        if (resposta.status === 401 && t && caminho.indexOf("/auth/") !== 0) {
          encerrarSessao();
          window.location.replace("index.html?sessao=expirada");
        }
        if (!resposta.ok) throw new ErroDaAPI(resposta.status, mensagemDe(dados, resposta.status), dados && dados.detalhes);
        return dados;
      });
    });
  }

  /* ----------------------------------------------------------------------
     Elementos comuns das telas internas
     ---------------------------------------------------------------------- */

  /* Preenche a barra lateral com o nome do usuário e liga o botão de sair. */
  function prepararBarra() {
    var u = usuario();
    var nome = document.querySelector(".barra__nome");
    var papel = document.querySelector(".barra__papel");
    if (u && nome) nome.textContent = u.nome;
    if (u && papel) papel.textContent = u.email;

    document.querySelectorAll("[data-sair]").forEach(function (botao) {
      botao.addEventListener("click", function () {
        encerrarSessao();
        window.location.href = "index.html";
      });
    });
  }

  /* Mostra uma falha no lugar do conteúdo, com a mensagem da API. */
  function mostrarFalha(elemento, erro, titulo) {
    elemento.innerHTML =
      '<div class="falha" role="alert"><strong>' + Trip.escapar(titulo || "Algo deu errado") + "</strong>" +
      Trip.escapar(erro && erro.message ? erro.message : String(erro)) + "</div>";
  }

  return {
    get: function (caminho) { return requisitar("GET", caminho); },
    post: function (caminho, corpo) { return requisitar("POST", caminho, corpo === undefined ? {} : corpo); },
    put: function (caminho, corpo) { return requisitar("PUT", caminho, corpo); },
    patch: function (caminho, corpo) { return requisitar("PATCH", caminho, corpo); },
    remover: function (caminho) { return requisitar("DELETE", caminho); },
    token: token,
    usuario: usuario,
    iniciarSessao: iniciarSessao,
    encerrarSessao: encerrarSessao,
    exigirLogin: exigirLogin,
    prepararBarra: prepararBarra,
    mostrarFalha: mostrarFalha
  };
})();
