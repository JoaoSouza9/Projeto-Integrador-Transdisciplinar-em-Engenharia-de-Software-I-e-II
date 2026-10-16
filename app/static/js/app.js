// Melhorias de usabilidade (o sistema continua funcional sem JavaScript).
document.addEventListener("DOMContentLoaded", function () {
  // Confirmação antes de ações destrutivas
  document.querySelectorAll("form[data-confirmar]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!window.confirm(f.dataset.confirmar)) e.preventDefault();
    });
  });

  // Máscara de CEP
  var cep = document.getElementById("cep");
  if (cep) {
    cep.addEventListener("input", function () {
      var v = cep.value.replace(/\D/g, "").slice(0, 8);
      cep.value = v.length > 5 ? v.slice(0, 5) + "-" + v.slice(5) : v;
    });
  }

  // Mostra/oculta o endereço novo no checkout
  var novo = document.getElementById("novo-endereco");
  if (novo) {
    var radios = document.querySelectorAll("input[name=endereco_id]");
    var atualizar = function () {
      var sel = document.querySelector("input[name=endereco_id]:checked");
      novo.hidden = !(sel && sel.value === "novo");
    };
    radios.forEach(function (r) { r.addEventListener("change", atualizar); });
    atualizar();
  }

  // Campos de cartão só aparecem quando a forma for cartão
  var dados = document.getElementById("dados-cartao");
  if (dados) {
    var formas = document.querySelectorAll("input[name=forma]");
    var mostrar = function () {
      var sel = document.querySelector("input[name=forma]:checked");
      dados.hidden = !(sel && sel.value === "CARTAO");
    };
    formas.forEach(function (r) { r.addEventListener("change", mostrar); });
    mostrar();
  }
});
