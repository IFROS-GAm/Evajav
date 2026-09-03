// Animaciones pequeñas que necesitan JavaScript. Todo lo demás va en CSS.
// Si este archivo no carga, la página se ve igual: los valores finales ya están
// escritos en el HTML y solo se anima el camino hasta ellos.
(() => {
  const quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 1. Barras de avance: crecen desde cero hasta el porcentaje que manda el servidor.
  document.querySelectorAll(".barra > span[data-ancho]").forEach((barra) => {
    const destino = barra.dataset.ancho + "%";
    if (quieto) {
      barra.style.width = destino;
      return;
    }
    barra.style.width = "0%";
    requestAnimationFrame(() => { barra.style.width = destino; });
  });

  // 2. Cifras grandes: cuentan hasta su valor. Respeta decimales y sufijos ("4.10", "12").
  const contar = (nodo) => {
    const texto = nodo.textContent.trim();
    const numero = Number(texto.replace(",", "."));
    if (!isFinite(numero) || numero === 0) return;
    const decimales = (texto.split(".")[1] || "").length;
    const duracion = 700;
    const inicio = performance.now();

    const paso = (ahora) => {
      const avance = Math.min(1, (ahora - inicio) / duracion);
      // easeOutCubic: arranca rápido y frena al final
      const suave = 1 - Math.pow(1 - avance, 3);
      nodo.textContent = (numero * suave).toFixed(decimales);
      if (avance < 1) requestAnimationFrame(paso);
      else nodo.textContent = texto;
    };
    requestAnimationFrame(paso);
  };

  if (!quieto) document.querySelectorAll(".stat").forEach(contar);

  // 3. Al enviar un formulario, el botón avisa que está trabajando: evita dobles clics
  //    en conexiones lentas (guardar un voto, importar el padrón).
  document.querySelectorAll("form").forEach((formulario) => {
    formulario.addEventListener("submit", () => {
      const boton = formulario.querySelector('button[type="submit"], button:not([type])');
      if (!boton || boton.dataset.trabajando) return;
      boton.dataset.trabajando = "1";
      boton.classList.add("cargando");
      boton.disabled = true;
      // Si la navegación falla o el navegador restaura la página, se reactiva.
      setTimeout(() => {
        boton.disabled = false;
        boton.classList.remove("cargando");
        delete boton.dataset.trabajando;
      }, 8000);
    });
  });
})();
