"""
Calcula RS-Ratio y RS-Momentum (Relative Rotation Graph) para los sectores
del mercado USA frente a SPY, y escribe el resultado en data.json.

No opera, no manda señales, no toca IBKR. Solo calcula y escribe un JSON.
Pensado para ejecutarse via cron (GitHub Actions) cada 30 min en horario NYSE.
"""

import json
import sys
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

# --- Configuración ---

BENCHMARK = "SPY"

SECTORS = {
    "XLK":  "Tecnología",
    "XLF":  "Financiero",
    "XLV":  "Salud",
    "XLY":  "Consumo discrecional",
    "XLP":  "Consumo básico",
    "XLE":  "Energía",
    "XLI":  "Industrial",
    "XLB":  "Materiales",
    "XLU":  "Utilities",
    "XLC":  "Comunicación",
    "SMH":  "Semiconductores",
    "ITA":  "Aeroespacial y Defensa",
}

ZSCORE_WINDOW = 12   # periodos para la normalización rolling
MOMENTUM_SMOOTH = 3  # suavizado del ROC antes de z-scorearlo
TAIL_LENGTH = 8       # cuántos puntos de la cola se guardan
HISTORY_PERIOD = "6mo"  # histórico a descargar (necesita cubrir la ventana + margen)

OUTPUT_PATH = "data.json"


def quadrant(x: float, y: float) -> str:
    if x >= 0 and y >= 0:
        return "Liderando"
    if x < 0 and y >= 0:
        return "Mejorando"
    if x >= 0 and y < 0:
        return "Debilitando"
    return "Rezagando"


def main() -> None:
    tickers = list(SECTORS.keys()) + [BENCHMARK]

    raw = yf.download(
        tickers,
        period=HISTORY_PERIOD,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        print("ERROR: yfinance no devolvió datos.", file=sys.stderr)
        sys.exit(1)

    close = raw["Close"]

    if BENCHMARK not in close.columns:
        print(f"ERROR: no se descargó el benchmark {BENCHMARK}.", file=sys.stderr)
        sys.exit(1)

    spy = close[BENCHMARK]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark": BENCHMARK,
        "params": {
            "zscore_window": ZSCORE_WINDOW,
            "tail_length": TAIL_LENGTH,
        },
        "sectors": {},
    }

    for ticker, full_name in SECTORS.items():
        if ticker not in close.columns:
            print(f"AVISO: {ticker} no disponible, se omite.", file=sys.stderr)
            continue

        sector_close = close[ticker]

        # Serie de fuerza relativa: sector vs benchmark
        rs = sector_close / spy

        # RS-Ratio: z-score de la fuerza relativa sobre ventana rolling
        rs_mean = rs.rolling(ZSCORE_WINDOW).mean()
        rs_std = rs.rolling(ZSCORE_WINDOW).std()
        z_ratio = (rs - rs_mean) / rs_std

        # RS-Momentum: ROC de RS suavizado, z-scoreado sobre la misma ventana.
        # No se deriva directamente el z_ratio para no amplificar ruido.
        roc = rs.pct_change(periods=1)
        roc_smooth = roc.rolling(MOMENTUM_SMOOTH).mean()
        roc_mean = roc_smooth.rolling(ZSCORE_WINDOW).mean()
        roc_std = roc_smooth.rolling(ZSCORE_WINDOW).std()
        z_momentum = (roc_smooth - roc_mean) / roc_std

        combined = pd.DataFrame({"x": z_ratio, "y": z_momentum}).dropna()

        if combined.empty:
            print(f"AVISO: {ticker} sin datos suficientes tras el cálculo, se omite.", file=sys.stderr)
            continue

        tail = combined.tail(TAIL_LENGTH)
        tail_points = [[round(row.x, 3), round(row.y, 3)] for row in tail.itertuples()]

        last_x, last_y = tail_points[-1]

        result["sectors"][ticker] = {
            "full_name": full_name,
            "tail": tail_points,
            "quadrant": quadrant(last_x, last_y),
        }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(result['sectors'])} sectores escritos en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
