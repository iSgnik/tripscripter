/* =========================================================================
   TripScripter — cadastro de conta (RQ001)

   A validação feita aqui serve à experiência do usuário, não à segurança:
   qualquer pessoa pode contorná-la no navegador. Por isso as regras que
   importam são repetidas no servidor (POST /api/auth/cadastro/), que é onde
   elas de fato valem. O tamanho mínimo da senha, 8 caracteres, é o mesmo
   nos dois lados.
   ========================================================================= */

(function () {
  "use strict";

  if (API.token()) {
    window.location.replace("viagens.html");
    return;
  }

  var TAMANHO_MINIMO = 8;

  var form = document.getElementById("formCadastro");
  var nome = document.getElementById("nome");
  var email = document.getElementById("email");
  var senha = document.getElementById("senha");
  var confirma = document.getElementById("confirma");
  var termos = document.getElementById("termos");
  var btnCriar = document.getElementById("btnCriar");
  var aviso = document.getElementById("aviso");

  var forca = document.getElementById("forca");
  var forcaDica = document.getElementById("forcaDica");
  var forcaRotulo = document.getElementById("forcaRotulo");

  var conferencia = document.getElementById("conferencia");
  var conferenciaTexto = document.getElementById("conferenciaTexto");
  var conferenciaIcone = document.getElementById("conferenciaIcone");

  var CHECK = '<path d="M20 6L9 17l-5-5"></path>';
  var XIS = '<path d="M18 6L6 18M6 6l12 12"></path>';

  /* ----------------------------------------------------------------------
     Força da senha
     ---------------------------------------------------------------------- */

  function medirForca(valor) {
    if (!valor) return { nivel: 0, rotulo: "", dica: "" };

    var tipos = 0;
    if (/[a-z]/.test(valor)) tipos++;
    if (/[A-Z]/.test(valor)) tipos++;
    if (/\d/.test(valor)) tipos++;
    if (/[^a-zA-Z0-9]/.test(valor)) tipos++;

    if (valor.length < TAMANHO_MINIMO) {
      return { nivel: 1, rotulo: "Fraca", dica: "Use ao menos " + TAMANHO_MINIMO + " caracteres" };
    }
    if (tipos < 2) {
      return { nivel: 1, rotulo: "Fraca", dica: "Misture letras maiúsculas e minúsculas" };
    }
    if (tipos < 3) {
      return { nivel: 2, rotulo: "Média", dica: "Acrescente números ou símbolos" };
    }
    return { nivel: 3, rotulo: "Forte", dica: "Ótima senha" };
  }

  function atualizarForca() {
    var medida = medirForca(senha.value);
    forca.hidden = medida.nivel === 0;
    forca.setAttribute("data-nivel", String(medida.nivel));
    forcaRotulo.textContent = medida.rotulo;
    forcaDica.textContent = medida.dica;
  }

  /* ----------------------------------------------------------------------
     Conferência das duas senhas
     ---------------------------------------------------------------------- */

  function senhasConferem() {
    return confirma.value.length > 0 && senha.value === confirma.value;
  }

  function atualizarConferencia() {
    if (confirma.value.length === 0) {
      conferencia.classList.remove("esta-visivel");
      return;
    }

    var confere = senhasConferem();
    conferencia.classList.add("esta-visivel");
    conferencia.setAttribute("data-confere", confere ? "true" : "false");
    conferenciaIcone.innerHTML = confere ? CHECK : XIS;
    conferenciaTexto.textContent = confere
      ? "As senhas conferem"
      : "As senhas estão diferentes";
  }

  /* ----------------------------------------------------------------------
     Habilitação do botão
     ---------------------------------------------------------------------- */

  function tudoPreenchido() {
    return nome.value.trim() !== "" &&
           email.value.trim() !== "" &&
           senha.value !== "" &&
           senhasConferem() &&
           termos.checked;
  }

  function atualizarBotao() {
    btnCriar.disabled = !tudoPreenchido();
  }

  /* ----------------------------------------------------------------------
     Mostrar e ocultar senha
     ---------------------------------------------------------------------- */

  function ligarOlho(idBotao, campo) {
    var botao = document.getElementById(idBotao);
    botao.addEventListener("click", function () {
      var visivel = campo.type === "text";
      campo.type = visivel ? "password" : "text";
      botao.setAttribute("aria-pressed", visivel ? "false" : "true");
      botao.setAttribute("aria-label", visivel ? "Mostrar senha" : "Ocultar senha");
      campo.focus();
    });
  }

  ligarOlho("olhoSenha", senha);
  ligarOlho("olhoConfirma", confirma);

  /* ----------------------------------------------------------------------
     Validação no envio
     ---------------------------------------------------------------------- */

  function erro(idCampo, idErro, visivel) {
    document.getElementById(idCampo).classList.toggle("campo--invalido", visivel);
    document.getElementById(idErro).classList.toggle("esta-visivel", visivel);
  }

  function mostrarAviso(texto) {
    aviso.textContent = texto;
    aviso.classList.add("esta-visivel");
  }

  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    aviso.classList.remove("esta-visivel");

    var ok = true;
    var primeiroInvalido = null;

    var nomeRuim = nome.value.trim().split(/\s+/).length < 2;
    erro("campoNome", "erroNome", nomeRuim);
    if (nomeRuim) { ok = false; primeiroInvalido = primeiroInvalido || nome; }

    var emailRuim = !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim());
    erro("campoEmail", "erroEmail", emailRuim);
    if (emailRuim) { ok = false; primeiroInvalido = primeiroInvalido || email; }

    var senhaRuim = senha.value.length < TAMANHO_MINIMO;
    erro("campoSenha", "erroSenha", senhaRuim);
    if (senhaRuim) { ok = false; primeiroInvalido = primeiroInvalido || senha; }

    if (!senhasConferem()) {
      ok = false;
      primeiroInvalido = primeiroInvalido || confirma;
      atualizarConferencia();
    }

    if (!termos.checked) {
      ok = false;
      mostrarAviso("É preciso aceitar os termos de uso para criar a conta.");
    }

    if (!ok) {
      if (primeiroInvalido) primeiroInvalido.focus();
      return;
    }

    btnCriar.disabled = true;
    btnCriar.textContent = "Criando conta…";

    API.post("/auth/cadastro/", { nome: nome.value.trim(), email: email.value.trim(), senha: senha.value })
      .then(function (resposta) {
        /* O cadastro já devolve o token: a pessoa entra direto. */
        API.iniciarSessao(resposta, false);
        window.location.href = "viagens.html";
      })
      .catch(function (falha) {
        mostrarAviso(falha.message);
        btnCriar.textContent = "Criar conta";
        atualizarBotao();
      });
  });

  /* ----------------------------------------------------------------------
     Reações a cada digitação
     ---------------------------------------------------------------------- */

  senha.addEventListener("input", function () {
    atualizarForca();
    atualizarConferencia();
    atualizarBotao();
    if (senha.value.length >= TAMANHO_MINIMO) erro("campoSenha", "erroSenha", false);
  });

  confirma.addEventListener("input", function () {
    atualizarConferencia();
    atualizarBotao();
  });

  nome.addEventListener("input", function () {
    atualizarBotao();
    if (nome.value.trim().split(/\s+/).length >= 2) erro("campoNome", "erroNome", false);
  });

  email.addEventListener("input", function () {
    atualizarBotao();
    if (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim())) {
      erro("campoEmail", "erroEmail", false);
    }
  });

  termos.addEventListener("change", function () {
    atualizarBotao();
    if (termos.checked) aviso.classList.remove("esta-visivel");
  });

  atualizarBotao();
})();
