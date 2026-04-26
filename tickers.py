"""
BVC tickers available for trading + USD/COP + COLCAP benchmark
"""

# Tickers tradeables (Yahoo Finance format)
TRADEABLE_ASSETS = {
    "ECOPETROL.CL":   {"name": "Ecopetrol",              "sector": "Energía"},
    "CIBEST.CL":      {"name": "Cibest",                 "sector": "Financiero"},
    "PFCIBEST.CL":    {"name": "PF Cibest",              "sector": "Financiero"},
    "BVC.CL":         {"name": "Bolsa de Valores",       "sector": "Financiero"},
    "GRUPOSURA.CL":   {"name": "Grupo Sura",             "sector": "Holding"},
    "PFGRUPSURA.CL":  {"name": "PF Grupo Sura",          "sector": "Holding"},
    "ISA.CL":         {"name": "Interconexión Eléctrica","sector": "Utilities"},
    "GEB.CL":         {"name": "Grupo Energía Bogotá",   "sector": "Utilities"},
    "CELSIA.CL":      {"name": "Celsia",                 "sector": "Utilities"},
    "GRUPOARGOS.CL":  {"name": "Grupo Argos",            "sector": "Holding"},
    "PFGRUPOARG.CL":  {"name": "PF Grupo Argos",         "sector": "Holding"},
    "CEMARGOS.CL":    {"name": "Cementos Argos",         "sector": "Materiales"},
    "PFCEMARGOS.CL":  {"name": "PF Cementos Argos",      "sector": "Materiales"},
    "PFAVAL.CL":      {"name": "PF Aval",                "sector": "Financiero"},
    "PFDAVVNDA.CL":   {"name": "PF Davivienda",          "sector": "Financiero"},
    "CORFICOLCF.CL":  {"name": "Corficolombiana",        "sector": "Financiero"},
    "MINEROS.CL":     {"name": "Mineros",                "sector": "Minería"},
    "NUTRESA.CL":     {"name": "Nutresa",                "sector": "Consumo"},
    "TERPEL.CL":      {"name": "Terpel",                 "sector": "Energía"},
    "PROMIGAS.CL":    {"name": "Promigas",               "sector": "Utilities"},
    "USDCOP=X":       {"name": "USD/COP",                "sector": "Divisas"},
}

# Benchmark (not tradeable)
BENCHMARK_TICKER = "^737809-COP-STRD"
BENCHMARK_NAME = "MSCI COLCAP"

INITIAL_CAPITAL = 100_000_000  # 100 millones COP
