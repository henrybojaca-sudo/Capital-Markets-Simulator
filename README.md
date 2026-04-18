# 📈 Capital Markets Simulator

Simulador de inversión en bolsa para estudiantes de Maestría en Finanzas — Mercados de Capitales.

## 🎯 Descripción

Aplicación de Streamlit donde grupos de estudiantes compiten invirtiendo 100 millones de COP virtuales en acciones de la Bolsa de Valores de Colombia (BVC) y el par USD/COP. Cada día deben rebalancear sus portafolios manteniéndose **100% invertidos** (sin efectivo en caja).

## ⚙️ Características

- **Registro de grupos** con nickname, capitán y contraseña
- **Trading diario** de 20 acciones BVC + USD/COP
- **Precios en tiempo real** vía Yahoo Finance
- **Benchmark COLCAP** (ICOLCAP.CL ETF) para comparar rendimiento
- **Leaderboard** (solo visible para el profesor)
- **Reporte automático** por email cada noche a las 11:30 PM
- **Historial completo** de operaciones por grupo

## 🏗️ Arquitectura

```
app.py                          ← App principal (estudiantes)
pages/
  1_👨‍🏫_Profesor.py            ← Panel admin del profesor
tickers.py                      ← Lista de activos tradeables
data_loader.py                  ← Fetch de precios (yfinance)
portfolio.py                    ← Cálculos de valor y métricas
storage.py                      ← Persistencia JSON
email_sender.py                 ← Envío de correos SMTP
scheduler.py                    ← Script cron (GitHub Actions)
.github/workflows/
  daily_report.yml              ← Cron 11:30 PM Colombia
```

## 🚀 Deployment en Streamlit Cloud

### 1. Sube a GitHub

```bash
cd capital_markets_simulator
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/henrybojaca-sudo/Capital-Markets-Simulator.git
git push -u origin main
```

### 2. Deploy en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. "New app" → conecta el repo `Capital-Markets-Simulator`
3. Main file: `app.py`
4. Deploy

### 3. Configurar secrets

En Streamlit Cloud → **Settings → Secrets**, pega:

```toml
admin_password = "tu_contraseña_admin"
professor_email = "henry.bojaca@gmail.com"

[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "tu@gmail.com"
sender_password = "app_password_16_caracteres"
```

**Para `sender_password`:** Genera una **App Password** de Gmail desde [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requiere 2FA activo).

## 📧 Email Automático Diario (11:30 PM)

El script `scheduler.py` corre vía **GitHub Actions** todos los días a las 11:30 PM Colombia.

### Configurar secrets en GitHub

Ve al repo en GitHub → **Settings → Secrets and variables → Actions → New repository secret**

Añade:
- `SMTP_SERVER` = `smtp.gmail.com`
- `SMTP_PORT` = `587`
- `SENDER_EMAIL` = tu email
- `SENDER_PASSWORD` = app password de Gmail
- `PROFESSOR_EMAIL` = `henry.bojaca@gmail.com`

El workflow se ejecuta automáticamente o puedes dispararlo manualmente desde **Actions → Daily Portfolio Report → Run workflow**.

## 🎮 Uso

### Estudiantes
1. Abren la app, pestaña **Registrar Grupo**
2. Eligen número, nickname, capitán, contraseña
3. Inician sesión y van a **Operar**
4. Cada día deben comprar y vender para mantenerse 100% invertidos

### Profesor
1. Sidebar → **👨‍🏫 Profesor**
2. Ingresa contraseña admin
3. Ve leaderboard, detalle por grupo, historial, y envía reportes manuales

## 📋 Reglas del juego

- **Capital inicial:** 100,000,000 COP
- **Duración:** 5 días (lunes a viernes)
- **Activos:** 20 acciones BVC + USD/COP
- **Regla de oro:** Siempre 100% invertido al cierre del día
- **Rebalanceo:** Mínimo 1 movimiento por día
- **Ganador:** Mayor **Total Return %** al final del período

## 🧪 Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📊 Tickers disponibles

| Ticker | Empresa | Sector |
|--------|---------|--------|
| ECOPETROL.CL | Ecopetrol | Energía |
| CIBEST.CL | Cibest | Financiero |
| BVC.CL | Bolsa de Valores | Financiero |
| GRUPOSURA.CL | Grupo Sura | Holding |
| ISA.CL | Interconexión Eléctrica | Utilities |
| GEB.CL | Grupo Energía Bogotá | Utilities |
| (y 14 más...) |

## 📝 Licencia

Proyecto educativo — Universidad del Norte / Maestría en Finanzas.
