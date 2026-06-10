import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sugar Wagon Analytics",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a0a2e 0%, #16213e 60%, #0f3460 100%);
    }
    section[data-testid="stSidebar"] * { color: #e8d5ff !important; }
    section[data-testid="stSidebar"] .stRadio label { font-weight: 500; font-size: 15px; }

    /* ── Main background ── */
    .main { background-color: #0d0d1a; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* ── Metric cards ── */
    .metric-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 1px solid #4f46e5;
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(79,70,229,0.2);
    }
    .metric-card .label { font-size: 12px; font-weight: 600; color: #a78bfa; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card .value { font-size: 28px; font-weight: 700; color: #f0e6ff; margin-top: 4px; }
    .metric-card .delta { font-size: 13px; color: #86efac; margin-top: 4px; }

    /* ── Section headers ── */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #c4b5fd;
        border-left: 4px solid #7c3aed;
        padding-left: 12px;
        margin: 24px 0 16px 0;
    }

    /* ── Page title ── */
    .page-title {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(90deg, #a78bfa, #f472b6, #fb923c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .page-subtitle { font-size: 14px; color: #6b7280; margin-bottom: 24px; }

    /* ── Upload zone ── */
    .upload-box {
        background: linear-gradient(135deg, #0f172a, #1e1b4b);
        border: 2px dashed #4f46e5;
        border-radius: 16px;
        padding: 28px;
        text-align: center;
        margin-bottom: 16px;
    }
    .upload-box h4 { color: #a78bfa; margin-bottom: 6px; }
    .upload-box p  { color: #6b7280; font-size: 13px; }

    /* ── Insight box ── */
    .insight-box {
        background: linear-gradient(135deg, #0c1a0c, #14290a);
        border: 1px solid #16a34a;
        border-radius: 12px;
        padding: 14px 18px;
        color: #86efac;
        font-size: 13px;
        margin-top: 10px;
    }

    /* ── Warning box ── */
    .warn-box {
        background: linear-gradient(135deg, #1c0a00, #2d1500);
        border: 1px solid #ea580c;
        border-radius: 12px;
        padding: 14px 18px;
        color: #fdba74;
        font-size: 13px;
    }

    /* ── Table ── */
    .dataframe thead tr th { background: #1e1b4b !important; color: #a78bfa !important; }
    .dataframe tbody tr:nth-child(even) { background: #0f0f1f !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #1e1b4b;
        border-radius: 8px;
        color: #a78bfa;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #7c3aed, #a855f7) !important;
        color: white !important;
    }

    /* Plotly charts dark bg */
    .js-plotly-plot .plotly { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────
def _init_state():
    for key, default in {
        "sales_df": None,
        "products_df": None,
        "factories_df": None,
        "targets_df": None,
        "merged_df": None,
        "model": None,
        "scaler": None,
        "imputer": None,
        "encoders": {},
        "feature_names": [],
        "metrics": {},
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

_init_state()

# ─── Helpers ─────────────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,15,30,0.6)",
    font=dict(color="#d1d5db", family="Inter"),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="#1e1b4b", zerolinecolor="#1e1b4b"),
    yaxis=dict(gridcolor="#1e1b4b", zerolinecolor="#1e1b4b"),
)
PALETTE = px.colors.qualitative.Vivid

def fmt_dollar(v): return f"${v:,.2f}"
def fmt_int(v):    return f"{v:,}"

def merge_tables(sales, products, factories, targets):
    df = sales.merge(products, on=["Product ID", "Product Name", "Division"], how="left")
    df = df.merge(factories, on="Factory", how="left")
    df = df.merge(targets, on="Division", how="left")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"])
    df["order_year"]    = df["Order Date"].dt.year
    df["order_month"]   = df["Order Date"].dt.month
    df["order_day"]     = df["Order Date"].dt.day
    df["quarter"]       = df["Order Date"].dt.quarter
    df["Shipping_days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    return df

def card(label, value, delta=None):
    delta_html = f'<div class="delta">▲ {delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {delta_html}
    </div>"""

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍬 Sugar Wagon")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📂 Data Upload", "📊 Analysis", "🔮 Predictions"],
        index=0,
    )
    st.markdown("---")
    st.markdown(
        "<div style='font-size:12px;color:#6b7280;text-align:center;'>Sugar Wagon v1.0 · Candy Sales AI</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — DATA UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📂 Data Upload":
    st.markdown('<div class="page-title">📂 Data Upload</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Upload all four Sugar Wagon CSV files to get started.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="upload-box"><h4>🛒 Candy Sales</h4><p>Order-level transaction data</p></div>', unsafe_allow_html=True)
        sales_file = st.file_uploader("Sales CSV", type="csv", key="sales", label_visibility="collapsed")

        st.markdown('<div class="upload-box"><h4>🏭 Candy Factories</h4><p>Factory locations (lat/lon)</p></div>', unsafe_allow_html=True)
        factories_file = st.file_uploader("Factories CSV", type="csv", key="factories", label_visibility="collapsed")

    with col2:
        st.markdown('<div class="upload-box"><h4>🍫 Candy Products</h4><p>Product catalogue with prices</p></div>', unsafe_allow_html=True)
        products_file = st.file_uploader("Products CSV", type="csv", key="products", label_visibility="collapsed")

        st.markdown('<div class="upload-box"><h4>🎯 Candy Targets</h4><p>Division-level sales targets</p></div>', unsafe_allow_html=True)
        targets_file = st.file_uploader("Targets CSV", type="csv", key="targets", label_visibility="collapsed")

    all_uploaded = all([sales_file, products_file, factories_file, targets_file])

    if all_uploaded:
        try:
            st.session_state.sales_df     = pd.read_csv(sales_file)
            st.session_state.products_df  = pd.read_csv(products_file)
            st.session_state.factories_df = pd.read_csv(factories_file)
            st.session_state.targets_df   = pd.read_csv(targets_file)
            st.session_state.merged_df    = merge_tables(
                st.session_state.sales_df,
                st.session_state.products_df,
                st.session_state.factories_df,
                st.session_state.targets_df,
            )
            st.success("✅ All files loaded and merged successfully!")
        except Exception as e:
            st.error(f"❌ Error loading files: {e}")

    if st.session_state.merged_df is not None:
        df = st.session_state.merged_df
        st.markdown('<div class="section-header">📋 Data Preview</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs(["Sales", "Products", "Factories", "Targets"])
        with tab1:
            st.dataframe(st.session_state.sales_df.head(50), use_container_width=True)
            st.caption(f"{len(st.session_state.sales_df):,} rows · {len(st.session_state.sales_df.columns)} columns")
        with tab2:
            st.dataframe(st.session_state.products_df, use_container_width=True)
        with tab3:
            st.dataframe(st.session_state.factories_df, use_container_width=True)
        with tab4:
            st.dataframe(st.session_state.targets_df, use_container_width=True)

        st.markdown('<div class="section-header">🔍 Merged Dataset Schema</div>', unsafe_allow_html=True)
        schema = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.notnull().sum().values,
            "Nulls": df.isnull().sum().values,
        })
        st.dataframe(schema, use_container_width=True, hide_index=True)

    else:
        st.markdown(
            '<div class="warn-box">⚠️ Upload all four CSV files above to unlock analysis and predictions.</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Analysis":
    st.markdown('<div class="page-title">📊 Sales Analysis</div>', unsafe_allow_html=True)

    if st.session_state.merged_df is None:
        st.markdown(
            '<div class="warn-box">⚠️ No data loaded. Please upload your CSVs in the <b>Data Upload</b> tab first.</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    df = st.session_state.merged_df

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.expander("🎛️ Filters", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        years    = sorted(df["order_year"].unique())
        regions  = ["All"] + sorted(df["Region"].dropna().unique().tolist())
        divs     = ["All"] + sorted(df["Division"].dropna().unique().tolist())
        sel_years  = fc1.multiselect("Year", years, default=years)
        sel_region = fc2.selectbox("Region", regions)
        sel_div    = fc3.selectbox("Division", divs)

    mask = df["order_year"].isin(sel_years)
    if sel_region != "All": mask &= df["Region"] == sel_region
    if sel_div    != "All": mask &= df["Division"] == sel_div
    fdf = df[mask]

    if fdf.empty:
        st.warning("No data matches your filter selection.")
        st.stop()

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    total_sales   = fdf["Sales"].sum()
    total_profit  = fdf["Gross Profit"].sum()
    total_units   = fdf["Units"].sum()
    avg_order     = fdf["Sales"].mean()
    margin_pct    = (total_profit / total_sales * 100) if total_sales else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, val in [
        (c1, "Total Revenue", fmt_dollar(total_sales)),
        (c2, "Total Gross Profit", fmt_dollar(total_profit)),
        (c3, "Total Units Sold", fmt_int(total_units)),
        (c4, "Avg Order Value", fmt_dollar(avg_order)),
        (c5, "Profit Margin", f"{margin_pct:.1f}%"),
    ]:
        col.markdown(card(label, val), unsafe_allow_html=True)

    st.markdown("---")

    # ── Monthly Trend ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 Monthly Sales Trend</div>', unsafe_allow_html=True)
    monthly = fdf.groupby(["order_year", "order_month"])["Sales"].sum().reset_index()
    monthly["Period"] = pd.to_datetime(monthly.assign(day=1)[["order_year","order_month","day"]].rename(columns={"order_year":"year","order_month":"month"}))
    fig_trend = px.line(
        monthly, x="Period", y="Sales", color="order_year",
        markers=True, color_discrete_sequence=PALETTE,
        labels={"Sales": "Revenue ($)", "Period": ""},
    )
    fig_trend.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown('<div class="insight-box">💡 Q4 (Oct–Dec) consistently peaks across all years, confirming holiday-driven seasonality in confectionery.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    # ── Regional Sales ─────────────────────────────────────────────────────────
    with col_a:
        st.markdown('<div class="section-header">🗺️ Sales by Region</div>', unsafe_allow_html=True)
        reg = fdf.groupby("Region")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        fig_reg = px.bar(reg, x="Region", y="Sales", color="Region",
                         color_discrete_sequence=PALETTE,
                         labels={"Sales": "Revenue ($)"})
        fig_reg.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_reg, use_container_width=True)

    # ── Division Donut ──────────────────────────────────────────────────────────
    with col_b:
        st.markdown('<div class="section-header">🍫 Division Share</div>', unsafe_allow_html=True)
        div_s = fdf.groupby("Division")["Sales"].sum().reset_index()
        fig_div = px.pie(div_s, names="Division", values="Sales", hole=0.5,
                         color_discrete_sequence=PALETTE)
        fig_div.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_div, use_container_width=True)

    # ── Top Products ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🏆 Top 10 Products by Revenue</div>', unsafe_allow_html=True)
    top_prod = (fdf.groupby("Product Name")["Sales"].sum()
                   .sort_values(ascending=False).head(10).reset_index())
    fig_prod = px.bar(top_prod, x="Sales", y="Product Name", orientation="h",
                      color="Sales", color_continuous_scale="Purples",
                      labels={"Sales":"Revenue ($)","Product Name":""})
    fig_prod.update_layout(**CHART_LAYOUT)
    fig_prod.update_yaxes(autorange="reversed", gridcolor="#1e1b4b")
    st.plotly_chart(fig_prod, use_container_width=True)

    col_c, col_d = st.columns(2)

    # ── Target Achievement ────────────────────────────────────────────────────
    with col_c:
        st.markdown('<div class="section-header">🎯 Target Achievement</div>', unsafe_allow_html=True)
        div_tgt = (fdf.groupby("Division")
                      .agg(Total_Sales=("Sales","sum"), Target=("Target","max"))
                      .reset_index())
        div_tgt["Achievement_%"] = (div_tgt["Total_Sales"] / div_tgt["Target"] * 100).round(1)
        fig_tgt = go.Figure()
        fig_tgt.add_trace(go.Bar(name="Actual Sales", x=div_tgt["Division"], y=div_tgt["Total_Sales"],
                                 marker_color="#7c3aed"))
        fig_tgt.add_trace(go.Scatter(name="Target", x=div_tgt["Division"], y=div_tgt["Target"],
                                     mode="markers+lines", marker=dict(size=12, color="#f472b6"),
                                     line=dict(dash="dot", color="#f472b6")))
        fig_tgt.update_layout(barmode="group", **CHART_LAYOUT)
        st.plotly_chart(fig_tgt, use_container_width=True)

    # ── Shipping Mode Distribution ────────────────────────────────────────────
    with col_d:
        st.markdown('<div class="section-header">🚚 Ship Mode Distribution</div>', unsafe_allow_html=True)
        ship = fdf.groupby("Ship Mode")["Sales"].sum().reset_index()
        fig_ship = px.pie(ship, names="Ship Mode", values="Sales", hole=0.4,
                          color_discrete_sequence=PALETTE)
        fig_ship.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_ship, use_container_width=True)

    # ── Correlation Heatmap ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔗 Correlation Matrix</div>', unsafe_allow_html=True)
    num_cols = ["Sales", "Units", "Gross Profit", "Cost", "Unit Price", "Unit Cost", "Shipping_days"]
    corr = fdf[num_cols].corr().round(2)
    fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                         zmin=-1, zmax=1, aspect="auto")
    fig_corr.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_corr, use_container_width=True)

    # ── Profitability by Product ──────────────────────────────────────────────
    st.markdown('<div class="section-header">💰 Profitability by Product</div>', unsafe_allow_html=True)
    prof = fdf.groupby("Product Name")["Gross Profit"].sum().sort_values(ascending=False).reset_index()
    fig_prof = px.bar(prof, x="Product Name", y="Gross Profit",
                      color="Gross Profit", color_continuous_scale="Viridis",
                      labels={"Gross Profit":"Gross Profit ($)"})
    fig_prof.update_layout(**CHART_LAYOUT, xaxis_tickangle=-40)
    st.plotly_chart(fig_prof, use_container_width=True)

    # ── Business Insights Table ───────────────────────────────────────────────
    st.markdown('<div class="section-header">📋 Business Insights Summary</div>', unsafe_allow_html=True)
    insights = pd.DataFrame({
        "Finding": [
            "Sales growing ~27% YoY (2023–2024)",
            "Q4 (Oct–Dec) highest every year",
            "Pacific region leads in sales",
            "Chocolate = 96% of transactions",
            "Units × Unit Price drives Sales",
        ],
        "Implication": [
            "Strong growth trajectory; supply chain must scale accordingly",
            "Prioritise stock and factory capacity in Q3 for holiday demand",
            "Evaluate why Gulf lags — pricing, distribution, or market size?",
            "Model risk: poor performance on Sugar/Other goes unnoticed in aggregate R²",
            "Promotions increasing order size (bundles) will have largest revenue impact",
        ],
    })
    st.dataframe(insights, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔮 Predictions":
    st.markdown('<div class="page-title">🔮 Sales Predictions</div>', unsafe_allow_html=True)

    if st.session_state.merged_df is None:
        st.markdown(
            '<div class="warn-box">⚠️ No data loaded. Please upload your CSVs in the <b>Data Upload</b> tab first.</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    df = st.session_state.merged_df.copy()

    # ── Model Config ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚙️ Model Configuration</div>', unsafe_allow_html=True)
    mc1, mc2, mc3 = st.columns(3)
    model_choice = mc1.selectbox("Algorithm", ["Random Forest", "Linear Regression"])
    test_size    = mc2.slider("Test Split %", 10, 40, 20, step=5)
    train_btn    = mc3.button("🚀 Train Model", use_container_width=True)

    if model_choice == "Random Forest":
        rf1, rf2 = st.columns(2)
        n_est  = rf1.slider("n_estimators", 50, 300, 100, step=50)
        max_d  = rf2.slider("max_depth", 3, 15, 5)
    else:
        n_est, max_d = 100, 5

    FEATURES = ["Division", "Region", "Ship Mode", "Units",
                "Gross Profit", "Cost", "Unit Price", "Unit Cost",
                "Shipping_days", "order_month", "quarter"]
    TARGET = "Sales"

    if train_btn or st.session_state.model is not None:
        if train_btn:
            with st.spinner("Training model…"):
                model_data = df[FEATURES + [TARGET]].dropna()
                encoders = {}
                for col in ["Division", "Region", "Ship Mode"]:
                    le = LabelEncoder()
                    model_data[col] = le.fit_transform(model_data[col].astype(str))
                    encoders[col] = le

                X = model_data[FEATURES]
                y = model_data[TARGET]
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size/100, random_state=42)

                scaler  = StandardScaler()
                imputer = SimpleImputer(strategy="mean")
                X_train = imputer.fit_transform(X_train)
                X_test  = imputer.transform(X_test)
                X_train = scaler.fit_transform(X_train)
                X_test  = scaler.transform(X_test)

                if model_choice == "Random Forest":
                    model = RandomForestRegressor(n_estimators=n_est, max_depth=max_d, random_state=42)
                else:
                    model = LinearRegression()

                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                metrics = {
                    "MAE":  mean_absolute_error(y_test, y_pred),
                    "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
                    "R²":   r2_score(y_test, y_pred),
                    "MAPE": np.mean(np.abs((y_test - y_pred) / (y_test + 1e-9))) * 100,
                }
                st.session_state.update({
                    "model": model, "scaler": scaler, "imputer": imputer,
                    "encoders": encoders, "metrics": metrics,
                    "feature_names": FEATURES,
                    "_y_test": y_test.values, "_y_pred": y_pred,
                    "_model_choice": model_choice,
                })

        # ── Metrics ───────────────────────────────────────────────────────────
        metrics = st.session_state.metrics
        st.markdown('<div class="section-header">📊 Model Performance</div>', unsafe_allow_html=True)
        pm1, pm2, pm3, pm4 = st.columns(4)
        for col, label, val in [
            (pm1, "R² Score",  f"{metrics['R²']:.4f}"),
            (pm2, "MAE",       fmt_dollar(metrics["MAE"])),
            (pm3, "RMSE",      fmt_dollar(metrics["RMSE"])),
            (pm4, "MAPE",      f"{metrics['MAPE']:.2f}%"),
        ]:
            col.markdown(card(label, val), unsafe_allow_html=True)

        st.markdown("---")

        col_p, col_q = st.columns(2)

        # ── Actual vs Predicted ────────────────────────────────────────────────
        with col_p:
            st.markdown('<div class="section-header">🎯 Actual vs Predicted</div>', unsafe_allow_html=True)
            y_test_arr = st.session_state["_y_test"]
            y_pred_arr = st.session_state["_y_pred"]
            sample_idx = np.random.choice(len(y_test_arr), min(300, len(y_test_arr)), replace=False)
            fig_avp = go.Figure()
            fig_avp.add_trace(go.Scatter(
                x=y_test_arr[sample_idx], y=y_pred_arr[sample_idx],
                mode="markers", marker=dict(color="#a78bfa", opacity=0.6, size=5),
                name="Predictions",
            ))
            mn, mx = y_test_arr.min(), y_test_arr.max()
            fig_avp.add_trace(go.Scatter(x=[mn,mx], y=[mn,mx],
                mode="lines", line=dict(color="#f472b6", dash="dash"), name="Perfect fit"))
            fig_avp.update_layout(xaxis_title="Actual ($)", yaxis_title="Predicted ($)", **CHART_LAYOUT)
            st.plotly_chart(fig_avp, use_container_width=True)

        # ── Residuals ─────────────────────────────────────────────────────────
        with col_q:
            st.markdown('<div class="section-header">📉 Residual Distribution</div>', unsafe_allow_html=True)
            residuals = y_test_arr - y_pred_arr
            fig_res = px.histogram(x=residuals, nbins=50, color_discrete_sequence=["#7c3aed"],
                                   labels={"x": "Residual ($)", "count": "Frequency"})
            fig_res.add_vline(x=0, line_dash="dash", line_color="#f472b6")
            fig_res.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig_res, use_container_width=True)

        # ── Feature Importance (RF only) ──────────────────────────────────────
        if st.session_state.get("_model_choice") == "Random Forest":
            st.markdown('<div class="section-header">🔍 Feature Importance</div>', unsafe_allow_html=True)
            fi_df = pd.DataFrame({
                "Feature": FEATURES,
                "Importance": st.session_state.model.feature_importances_,
            }).sort_values("Importance", ascending=False)
            fig_fi = px.bar(fi_df, x="Importance", y="Feature", orientation="h",
                            color="Importance", color_continuous_scale="Purples",
                            labels={"Feature": ""})
            fig_fi.update_layout(**CHART_LAYOUT)
            fig_fi.update_yaxes(autorange="reversed", gridcolor="#1e1b4b")
            st.plotly_chart(fig_fi, use_container_width=True)

        st.markdown("---")

        # ── Single Prediction ─────────────────────────────────────────────────
        st.markdown('<div class="section-header">🧮 Predict a Single Order</div>', unsafe_allow_html=True)
        enc = st.session_state.encoders
        sp1, sp2, sp3 = st.columns(3)
        division  = sp1.selectbox("Division",  enc["Division"].classes_)
        region    = sp2.selectbox("Region",    enc["Region"].classes_)
        ship_mode = sp3.selectbox("Ship Mode", enc["Ship Mode"].classes_)

        sp4, sp5, sp6 = st.columns(3)
        units      = sp4.number_input("Units",      min_value=1, max_value=200,  value=5)
        unit_price = sp5.number_input("Unit Price ($)", min_value=0.5, max_value=50.0, value=3.49)
        unit_cost  = sp6.number_input("Unit Cost ($)",  min_value=0.1, max_value=20.0, value=1.0)

        sp7, sp8, sp9 = st.columns(3)
        ship_days = sp7.slider("Shipping Days", 1, 10, 3)
        order_month = sp8.selectbox("Order Month", list(range(1, 13)),
                                    format_func=lambda m: ["Jan","Feb","Mar","Apr","May","Jun",
                                                           "Jul","Aug","Sep","Oct","Nov","Dec"][m-1])
        quarter = sp9.selectbox("Quarter", [1,2,3,4])

        gross_profit = units * (unit_price - unit_cost)
        cost         = units * unit_cost

        if st.button("🔮 Predict Sales", use_container_width=True):
            input_data = pd.DataFrame([{
                "Division":      enc["Division"].transform([division])[0],
                "Region":        enc["Region"].transform([region])[0],
                "Ship Mode":     enc["Ship Mode"].transform([ship_mode])[0],
                "Units":         units,
                "Gross Profit":  gross_profit,
                "Cost":          cost,
                "Unit Price":    unit_price,
                "Unit Cost":     unit_cost,
                "Shipping_days": ship_days,
                "order_month":   order_month,
                "quarter":       quarter,
            }])
            X_inp = st.session_state.imputer.transform(input_data)
            X_inp = st.session_state.scaler.transform(X_inp)
            pred  = st.session_state.model.predict(X_inp)[0]
            st.markdown(
                f"""
                <div style='background:linear-gradient(135deg,#4c1d95,#7c3aed);border-radius:16px;
                padding:28px;text-align:center;margin-top:16px;'>
                    <div style='font-size:14px;color:#c4b5fd;font-weight:600;text-transform:uppercase;
                    letter-spacing:2px;'>Predicted Sales</div>
                    <div style='font-size:52px;font-weight:800;color:#fff;margin:8px 0;'>{fmt_dollar(pred)}</div>
                    <div style='font-size:13px;color:#a78bfa;'>Estimated Gross Profit: {fmt_dollar(gross_profit)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        st.markdown(
            '<div class="warn-box">👆 Configure your model above and click <b>Train Model</b> to begin.</div>',
            unsafe_allow_html=True,
        )
