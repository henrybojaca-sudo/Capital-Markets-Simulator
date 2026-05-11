"""
BVC tickers available for trading + USD/COP + COLCAP benchmark
"""

TRADEABLE_ASSETS = {
    # Acciones colombianas - símbolos corregidos para Yahoo Finance
    "ECOPETROL.CL":   {"name": "Ecopetrol",              "sector": "Energía",     "yahoo_symbol": "EC"},
    "CIBEST.CL":      {"name": "Cibest",                 "sector": "Financiero",  "yahoo_symbol": "CIBEST.BO"},
    "PFCIBEST.CL":    {"name": "PF Cibest",              "sector": "Financiero",  "yahoo_symbol": "PFCIBEST.BO"},
    "BVC.CL":         {"name": "Bolsa de Valores",       "sector": "Financiero",  "yahoo_symbol": "BVC.BO"},
    "GRUPOSURA.CL":   {"name": "Grupo Sura",             "sector": "Holding",     "yahoo_symbol": "GRUPOSURA.BO"},
    "PFGRUPSURA.CL":  {"name": "PF Grupo Sura",          "sector": "Holding",     "yahoo_symbol": "PFGRUPSURA.BO"},
    "ISA.CL":         {"name": "Interconexión Eléctrica","sector": "Utilities",   "yahoo_symbol": "ISA.BO"},
    "GEB.CL":         {"name": "Grupo Energía Bogotá",   "sector": "Utilities",   "yahoo_symbol": "GEB.BO"},
    "CELSIA.CL":      {"name": "Celsia",                 "sector": "Utilities",   "yahoo_symbol": "CELSIA.BO"},
    "GRUPOARGOS.CL":  {"name": "Grupo Argos",            "sector": "Holding",     "yahoo_symbol": "GRUPOARGOS.BO"},
    "PFGRUPOARG.CL":  {"name": "PF Grupo Argos",         "sector": "Holding",     "yahoo_symbol": "PFGRUPOARG.BO"},
    "CEMARGOS.CL":    {"name": "Cementos Argos",         "sector": "Materiales",  "yahoo_symbol": "CEMARGOS.BO"},
    "PFCEMARGOS.CL":  {"name": "PF Cementos Argos",      "sector": "Materiales",  "yahoo_symbol": "PFCEMARGOS.BO"},
    "PFAVAL.CL":      {"name": "PF Aval",                "sector": "Financiero",  "yahoo_symbol": "PFAVAL.BO"},
    "PFDAVVNDA.CL":   {"name": "PF Davivienda",          "sector": "Financiero",  "yahoo_symbol": "PFDAVVNDA.BO"},
    "CORFICOLCF.CL":  {"name": "Corficolombiana",        "sector": "Financiero",  "yahoo_symbol": "CORFICOLCF.BO"},
    "MINEROS.CL":     {"name": "Mineros",                "sector": "Minería",     "yahoo_symbol": "MINEROS.BO"},
    "NUTRESA.CL":     {"name": "Nutresa",                "sector": "Consumo",     "yahoo_symbol": "NUTRESA.BO"},
    "TERPEL.CL":      {"name": "Terpel",                 "sector": "Energía",     "yahoo_symbol": "TERPEL.BO"},
    "PROMIGAS.CL":    {"name": "Promigas",               "sector": "Utilities",   "yahoo_symbol": "PROMIGAS.BO"},
    "USDCOP=X":       {"name": "USD/COP",                "sector": "Divisas",     "yahoo_symbol": "USDCOP=X"},
}

BENCHMARK_TICKER = "^COLCAP"
BENCHMARK_NAME = "COLCAP"
INITIAL_CAPITAL = 100_000_000  # 100 millones COP
