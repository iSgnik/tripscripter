/* =========================================================================
   TripScripter — tela de acesso (RQ002)

   Confere o preenchimento no navegador, para dar resposta imediata, e envia
   e-mail e senha à API (POST /api/auth/login/). Quem decide se a senha está
   certa é o servidor: a validação daqui serve à experiência, não à segurança.
   ========================================================================= */

(function () {
  "use strict";

  /* Quem já tem sessão vai direto para as viagens. */
  if (API.token()) {
    window.location.replace("viagens.html");
    return;
  }

  var form = document.getElementById("formAcesso");
  var aviso = document.getElementById("aviso");
  var botao = document.getElementById("btnEntrar");
  var senha = document.getElementById("senha");

  function mostrarAviso(texto, informativo) {
    aviso.textContent = texto;
    aviso.classList.toggle("aviso--info", Boolean(informativo));
    aviso.classList.add("esta-visivel");
  }

  function limparAviso() {
    aviso.textContent = "";
    aviso.classList.remove("esta-visivel", "aviso--info");
  }

  var params = new URLSearchParams(window.location.search);
  if (params.get("sessao") === "expirada") mostrarAviso("Sua sessão expirou. Entre novamente.", true);

  document.getElementById("olhoSenha").addEventListener("click", function () {
    var mostrando = senha.type === "text";
    senha.type = mostrando ? "password" : "text";
    this.setAttribute("aria-label", mostrando ? "Mostrar senha" : "Ocultar senha");
  });

  /* Recuperação de senha exige envio de e-mail, que o sistema ainda não faz.
     O link fica no lugar previsto pelo protótipo, mas avisa em vez de fingir. */
  document.getElementById("esqueci").addEventListener("click", function (evento) {
    evento.preventDefault();
    mostrarAviso("A recuperação de senha ainda não está disponível nesta versão.", true);
  });

  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    limparAviso();

    var email = document.getElementById("email").value.trim();
    var valor = senha.value;

    if (!email || !valor) {
      mostrarAviso("Preencha o e-mail e a senha para entrar.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      mostrarAviso("Esse e-mail não parece válido. Confira o endereço.");
      return;
    }

    botao.disabled = true;
    botao.textContent = "Entrando…";

    API.post("/auth/login/", { email: email, senha: valor })
      .then(function (resposta) {
        API.iniciarSessao(resposta, document.getElementById("lembrar").checked);
        window.location.href = "viagens.html";
      })
      .catch(function (erro) {
        mostrarAviso(erro.message);
        botao.disabled = false;
        botao.textContent = "Entrar";
      });
  });

  form.addEventListener("input", function () {
    if (!aviso.classList.contains("aviso--info")) limparAviso();
  });
})();
