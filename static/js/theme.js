/**
 * Alterna entre tema claro e escuro e memoriza a escolha do usuário
 * (guardada no navegador, não em cookie, pois é só preferência visual).
 */
(function () {
  const STORAGE_KEY = 'sigha-theme';
  const root = document.documentElement;

  function aplicarTema(tema) {
    root.setAttribute('data-bs-theme', tema);
    const icone = document.getElementById('icone-tema');
    if (icone) {
      icone.className = tema === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
  }

  const salvo = localStorage.getItem(STORAGE_KEY)
    || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  aplicarTema(salvo);

  document.addEventListener('DOMContentLoaded', function () {
    const botao = document.getElementById('botao-tema');
    if (botao) {
      botao.addEventListener('click', function () {
        const atual = root.getAttribute('data-bs-theme');
        const novo = atual === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, novo);
        aplicarTema(novo);
      });
    }

    const botaoMenu = document.getElementById('botao-menu-mobile');
    const sidebar = document.querySelector('.sigha-sidebar');
    if (botaoMenu && sidebar) {
      botaoMenu.addEventListener('click', function () {
        sidebar.classList.toggle('show');
      });
    }
  });
})();
