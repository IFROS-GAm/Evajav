// Fondo de constelación: puntos que se mueven y se unen con una línea cuando están
// cerca. Sin librerías ni CDN, ~1 KB. Se dibuja detrás de todo y no recibe clics.
(() => {
  const lienzo = document.getElementById("red");
  if (!lienzo) return;

  const ctx = lienzo.getContext("2d");
  const quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DISTANCIA = 150;   // hasta dónde se unen dos puntos
  const DENSIDAD = 8500;   // un punto por cada N píxeles de pantalla
  let puntos = [];
  let animacion = null;

  const medir = () => {
    const escala = Math.min(devicePixelRatio || 1, 2);
    lienzo.width = innerWidth * escala;
    lienzo.height = innerHeight * escala;
    ctx.setTransform(escala, 0, 0, escala, 0, 0);

    const cuantos = Math.min(160, Math.round((innerWidth * innerHeight) / DENSIDAD));
    puntos = Array.from({ length: cuantos }, () => ({
      x: Math.random() * innerWidth,
      y: Math.random() * innerHeight,
      dx: (Math.random() - 0.5) * 0.35,
      dy: (Math.random() - 0.5) * 0.35,
    }));
  };

  const dibujar = () => {
    ctx.clearRect(0, 0, innerWidth, innerHeight);

    for (let i = 0; i < puntos.length; i++) {
      const a = puntos[i];
      if (!quieto) {
        a.x += a.dx;
        a.y += a.dy;
        if (a.x < 0 || a.x > innerWidth) a.dx *= -1;
        if (a.y < 0 || a.y > innerHeight) a.dy *= -1;
      }
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
      ctx.fillStyle = "rgba(147, 197, 253, 0.9)";
      ctx.beginPath();
      ctx.arc(a.x, a.y, 1.6, 0, Math.PI * 2);
      ctx.fill();
    }

    animacion = quieto ? null : requestAnimationFrame(dibujar);
  };

  const arrancar = () => {
    cancelAnimationFrame(animacion);
    dibujar();
  };

  medir();
  arrancar();
  addEventListener("resize", () => { medir(); arrancar(); });
  // Con la pestaña oculta no hay nada que dibujar: se libera la CPU.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) cancelAnimationFrame(animacion);
    else arrancar();
  });
})();
