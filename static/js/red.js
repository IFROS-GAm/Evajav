// Fondo de constelación animado: puntos que flotan, se unen entre sí y reaccionan al
// cursor. Sin librerías ni CDN. Se dibuja detrás de todo y no recibe clics.
(() => {
  const lienzo = document.getElementById("red");
  if (!lienzo) return;

  const ctx = lienzo.getContext("2d");
  // Con "menos movimiento" activado en el sistema el fondo NO se congela: se mueve
  // algo más lento y deja de reaccionar al cursor. Quedarse quieto se leía como un
  // fallo, y en Windows esa opción viene apagada con mucha frecuencia.
  const suave = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const VELOCIDAD = suave ? 0.5 : 0.75;
  const DISTANCIA = 155;   // hasta dónde se unen dos puntos
  const RATON = 220;       // radio de influencia del cursor
  const DENSIDAD = 8500;   // un punto por cada N píxeles de pantalla
  let puntos = [];
  let raton = { x: -9999, y: -9999 };
  let ultimoDibujo = 0;

  const medir = () => {
    const escala = Math.min(devicePixelRatio || 1, 2);
    lienzo.width = innerWidth * escala;
    lienzo.height = innerHeight * escala;
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

      // El cursor empuja suavemente los puntos cercanos.
      const dCursor = Math.hypot(a.x - raton.x, a.y - raton.y);
      if (!suave && dCursor < RATON) {
        const fuerza = (1 - dCursor / RATON) * 0.6;
        a.x += ((a.x - raton.x) / (dCursor || 1)) * fuerza;
        a.y += ((a.y - raton.y) / (dCursor || 1)) * fuerza;
      }

      // Líneas entre puntos vecinos
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

      // Línea hacia el cursor: hace evidente que el fondo está vivo
      if (dCursor < RATON) {
        ctx.strokeStyle = `rgba(34, 211, 238, ${0.5 * (1 - dCursor / RATON)})`;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(raton.x, raton.y);
        ctx.stroke();
      }

      const latido = 0.75 + 0.25 * Math.sin(t * (suave ? 1.1 : 1.6) + a.fase);
      ctx.fillStyle = `rgba(147, 197, 253, ${0.85 * latido})`;
      ctx.beginPath();
      ctx.arc(a.x, a.y, 1.5 + latido * 0.8, 0, Math.PI * 2);
      ctx.fill();
    }
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
  addEventListener("pointermove", (e) => { raton = { x: e.clientX, y: e.clientY }; }, { passive: true });
  addEventListener("pointerleave", () => { raton = { x: -9999, y: -9999 }; });
})();
