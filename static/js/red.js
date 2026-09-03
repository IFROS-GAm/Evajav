// Fondo de constelación animado: puntos que flotan y se unen con una línea cuando
// están cerca, más chispas que viajan por esas líneas. Sin librerías ni CDN.
// Se dibuja detrás de todo, no recibe clics y no depende del puntero.
(() => {
  const lienzo = document.getElementById("red");
  if (!lienzo) return;

  const ctx = lienzo.getContext("2d");
  // Con "menos movimiento" activado en el sistema el fondo NO se congela: se mueve
  // algo más lento. Quedarse quieto se leía como un fallo, y en Windows esa opción
  // viene apagada con mucha frecuencia.
  const suave = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const VELOCIDAD = suave ? 0.5 : 0.75;
  const DISTANCIA = 155;      // hasta dónde se unen dos puntos
  const DENSIDAD = 8500;      // un punto por cada N píxeles de pantalla
  const CHISPAS = suave ? 2 : 4;
  let puntos = [];
  let chispas = [];
  let ultimoDibujo = 0;

  const medir = () => {
    const escala = Math.min(devicePixelRatio || 1, 2);
    lienzo.width = innerWidth * escala;
    lienzo.height = innerHeight * escala;
    // Una unidad de dibujo = un píxel CSS, en cualquier pantalla.
    ctx.setTransform(escala, 0, 0, escala, 0, 0);

    const cuantos = Math.min(160, Math.round((innerWidth * innerHeight) / DENSIDAD));
    puntos = Array.from({ length: cuantos }, () => ({
      x: Math.random() * innerWidth,
      y: Math.random() * innerHeight,
      dx: (Math.random() - 0.5) * VELOCIDAD,
      dy: (Math.random() - 0.5) * VELOCIDAD,
      // Cada punto late a su propio ritmo para que el brillo no sea uniforme.
      fase: Math.random() * Math.PI * 2,
    }));
    chispas = [];
  };

  // Una chispa recorre el tramo entre dos puntos vecinos y desaparece al llegar.
  const nacerChispa = () => {
    const a = Math.floor(Math.random() * puntos.length);
    const cerca = [];
    for (let b = 0; b < puntos.length; b++) {
      if (b !== a && Math.hypot(puntos[a].x - puntos[b].x, puntos[a].y - puntos[b].y) < DISTANCIA) {
        cerca.push(b);
      }
    }
    if (!cerca.length) return;
    chispas.push({
      desde: a,
      hasta: cerca[Math.floor(Math.random() * cerca.length)],
      avance: 0,
      paso: 0.006 + Math.random() * 0.008,
    });
  };

  const dibujar = () => {
    const ahora = performance.now();
    ultimoDibujo = ahora;
    const t = ahora / 1000;
    ctx.clearRect(0, 0, innerWidth, innerHeight);

    for (let i = 0; i < puntos.length; i++) {
      const a = puntos[i];
      a.x += a.dx;
      a.y += a.dy;
      if (a.x < 0 || a.x > innerWidth) a.dx *= -1;
      if (a.y < 0 || a.y > innerHeight) a.dy *= -1;

      for (let j = i + 1; j < puntos.length; j++) {
        const b = puntos[j];
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (dist < DISTANCIA) {
          ctx.strokeStyle = `rgba(96, 165, 250, ${0.45 * (1 - dist / DISTANCIA)})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }

      const latido = 0.75 + 0.25 * Math.sin(t * (suave ? 1.1 : 1.6) + a.fase);
      ctx.fillStyle = `rgba(147, 197, 253, ${0.85 * latido})`;
      ctx.beginPath();
      ctx.arc(a.x, a.y, 1.5 + latido * 0.8, 0, Math.PI * 2);
      ctx.fill();
    }

    if (chispas.length < CHISPAS && Math.random() < 0.03) nacerChispa();

    chispas = chispas.filter((chispa) => {
      const a = puntos[chispa.desde];
      const b = puntos[chispa.hasta];
      if (!a || !b) return false;
      chispa.avance += chispa.paso;
      if (chispa.avance >= 1) return false;

      const x = a.x + (b.x - a.x) * chispa.avance;
      const y = a.y + (b.y - a.y) * chispa.avance;
      // Estela corta detrás de la chispa
      const cola = Math.max(0, chispa.avance - 0.12);
      ctx.strokeStyle = "rgba(34, 211, 238, 0.55)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(a.x + (b.x - a.x) * cola, a.y + (b.y - a.y) * cola);
      ctx.lineTo(x, y);
      ctx.stroke();

      const brillo = ctx.createRadialGradient(x, y, 0, x, y, 6);
      brillo.addColorStop(0, "rgba(165, 243, 252, 0.95)");
      brillo.addColorStop(1, "rgba(34, 211, 238, 0)");
      ctx.fillStyle = brillo;
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fill();
      return true;
    });
  };

  const bucle = () => {
    dibujar();
    requestAnimationFrame(bucle);
  };

  medir();
  requestAnimationFrame(bucle);

  // Respaldo: algunos navegadores incrustados (el panel de vista previa del editor,
  // por ejemplo) pintan la página pero la reportan como oculta, y ahí
  // requestAnimationFrame nunca se ejecuta: el fondo quedaría dibujado una sola vez.
  // Este temporizador solo actúa si hace rato que no se pinta un fotograma, y el
  // propio navegador lo frena cuando la pestaña está de verdad en segundo plano.
  setInterval(() => {
    if (performance.now() - ultimoDibujo > 150) dibujar();
  }, 40);

  addEventListener("resize", medir);
})();
