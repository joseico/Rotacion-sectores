# RRG Sectorial

## Qué hace
Calcula cada 30 min (horario NYSE) qué sectores del mercado USA están recibiendo
capital y cuáles lo están perdiendo, usando Relative Rotation Graphs (RS-Ratio /
RS-Momentum) sobre SPY como benchmark. Escribe el resultado en `data.json` y lo
sirve como página estática consultable desde el móvil.

Sectores cubiertos: XLK, XLF, XLV, XLY, XLP, XLE, XLI, XLB, XLU, XLC, SMH, ITA
(Aeroespacial y Defensa en vez de Inmobiliario).

## Despliegue (una sola vez)

1. Crea un repo nuevo en GitHub (puede ser privado) y sube estos archivos tal
   cual, manteniendo la carpeta `.github/workflows/`.
2. Ve a Settings → Pages → Source → selecciona la rama `main` y la carpeta `/`
   (root). Guarda. GitHub te da una URL tipo
   `https://tuusuario.github.io/tu-repo/`.
3. Ve a Settings → Actions → General → en "Workflow permissions" marca
   "Read and write permissions" (necesario para que el workflow pueda hacer
   commit del `data.json`).
4. Ve a la pestaña "Actions" del repo y lanza el workflow "Actualizar RRG"
   manualmente una vez (botón "Run workflow") para generar el primer
   `data.json` sin esperar al cron.
5. Abre la URL de Pages desde el móvil y añádela a la pantalla de inicio.

## Mantenimiento

- El cron se ejecuta solo, no requiere que tengas nada encendido.
- `holdings.json` es manual. Cuando la web te avise de que ha caducado (banner
  rojo, por defecto a los 90 días), revisa los top-5 de cada ETF en:
  - SPDR (XLK, XLF, XLV, XLY, XLP, XLE, XLI, XLB, XLU, XLC): ssga.com
  - ITA: ishares.com
  - SMH: vaneck.com
  Actualiza los pesos en `holdings.json` y cambia el campo `last_updated`.

## Parámetros ajustables en rrg_calculator.py

- `ZSCORE_WINDOW` (12): ventana de normalización rolling.
- `TAIL_LENGTH` (8): cuántos puntos de trayectoria se muestran.
- `HISTORY_PERIOD` ("6mo"): histórico descargado de yfinance.
