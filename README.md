# 🍬 Sugar Wagon — Streamlit App

A full-stack candy sales analytics & prediction dashboard built with Streamlit.

## Pages
| Page | Description |
|------|-------------|
| 📂 Data Upload | Upload all 4 CSVs (Sales, Products, Factories, Targets). Auto-merges and previews schema. |
| 📊 Analysis | KPI cards, monthly trend, regional & division breakdown, target achievement, correlation heatmap, top products & profitability. |
| 🔮 Predictions | Train Random Forest or Linear Regression, evaluate with R²/MAE/RMSE/MAPE, visualise actual vs predicted, feature importance, and predict a single order. |

## Required CSV files
- `Candy_Sales.csv`
- `Candy_Products.csv`
- `Candy_Factories.csv`
- `Candy_Targets.csv`

## Local setup

```bash
# 1. Clone / copy this folder
cd sugar_wagon_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

## Deploy on Streamlit Community Cloud (free)

1. Push this folder to a **GitHub repository** (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo and set:
   - **Main file path:** `app.py`
4. Click **Deploy** — your app will be live in ~2 minutes.
5. Share the URL with anyone; they can upload their own CSVs directly in the browser.

> **Tip:** If you want the CSVs pre-loaded (no upload step), add them to the repo and load them with `pd.read_csv("Candy_Sales.csv")` at startup.

## Folder structure
```
sugar_wagon_app/
├── app.py           ← main Streamlit application
├── requirements.txt ← Python dependencies
└── README.md        ← this file
```
