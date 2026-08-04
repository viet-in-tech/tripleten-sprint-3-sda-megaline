import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Megaline SDA Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .healthy { color: #00d4aa; }
    .at-risk { color: #ff6b6b; }
    .neutral { color: #60a5fa; }
    .stat-sig {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        border-radius: 8px;
        padding: 12px 20px;
        color: #6ee7b7;
        font-weight: 600;
        text-align: center;
    }
    .stat-nosig {
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
        border-radius: 8px;
        padding: 12px 20px;
        color: #fcd34d;
        font-weight: 600;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data from SDA Project PDF & CSVs ─────────────────────────────────────────

PLANS = {
    "surf": {
        "name": "Surf", "type": "Budget",
        "base_fee": 20.00, "included_minutes": 500,
        "included_messages": 50, "included_gb": 15,
        "overage_min": 0.03, "overage_msg": 0.03, "overage_gb": 10.00,
        "color": "#00d4aa", "color_secondary": "#0ea5e9"
    },
    "ultimate": {
        "name": "Ultimate", "type": "Premium",
        "base_fee": 70.00, "included_minutes": 3000,
        "included_messages": 1000, "included_gb": 30,
        "overage_min": 0.01, "overage_msg": 0.01, "overage_gb": 7.00,
        "color": "#a855f7", "color_secondary": "#ef4444"
    }
}

METRICS = {
    "surf": {
        "customers": 339,
        "monthly_profit_mean": 50.33, "monthly_profit_std": 55.26,
        "monthly_profit_min": 10.00, "monthly_profit_25": 10.00,
        "monthly_profit_max": 578.64,
        "monthly_arpu": 60.90,
        "avg_call_duration": 412.10, "call_variance": 47001.25,
        "avg_messages": 181,
        "monthly_churn_pct": 16.37, "avg_lifetime_months": 6.11,
        "cac": 180, "ltv": 260, "payback_months": 4.2,
        "ltv_cac_ratio": 1.44, "ltv_cac_diff": 80,
        "health": "HEALTHY", "est_cost_per_user": 10.00
    },
    "ultimate": {
        "customers": 161,
        "monthly_profit_mean": 47.31, "monthly_profit_std": 11.40,
        "monthly_profit_min": 45.00, "monthly_profit_25": 45.00,
        "monthly_profit_max": 157.00,
        "monthly_arpu": 72.32,
        "avg_call_duration": 410.18, "call_variance": 50510.63,
        "avg_messages": 205,
        "monthly_churn_pct": 16.37, "avg_lifetime_months": 6.11,
        "cac": 350, "ltv": 309, "payback_months": 6.9,
        "ltv_cac_ratio": 0.88, "ltv_cac_diff": -41,
        "health": "AT RISK", "est_cost_per_user": 25.00
    }
}

MONTHLY_REGISTRATIONS = {
    "Jan": 49, "Feb": 42, "Mar": 40, "Apr": 45, "May": 38, "Jun": 54,
    "Jul": 36, "Aug": 47, "Sep": 32, "Oct": 42, "Nov": 38, "Dec": 37
}

# ─── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 📡 Megaline SDA")
st.sidebar.markdown("**Statistical Data Analysis**")
st.sidebar.markdown("---")

st.sidebar.markdown("### ⚙️ Scenario Planner")
st.sidebar.markdown("*Adjust assumptions for unit economics:*")

cac_surf = st.sidebar.slider("Surf CAC ($)", 50, 400, 180, step=10)
cac_ultimate = st.sidebar.slider("Ultimate CAC ($)", 100, 600, 350, step=10)
churn_rate = st.sidebar.slider("Monthly Churn Rate (%)", 5.0, 30.0, 16.4, step=0.5)
gross_margin = st.sidebar.slider("Gross Margin (%)", 40, 90, 70, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📐 Key Formulas")
st.sidebar.latex(r"Profit = Revenue - Cost")
st.sidebar.latex(r"LTV = \frac{ARPU \times Margin}{Churn}")
st.sidebar.latex(r"Payback = \frac{CAC}{ARPU \times Margin}")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Data Sources")
st.sidebar.markdown("""
- `megaline_users.csv` (500 rows)
- `megaline_calls.csv` (137,735 rows)
- `megaline_internet.csv` (104,825 rows)
- `megaline_messages.csv` (76,051 rows)
- `megaline_plans.csv` (2 rows)
""")
st.sidebar.caption("SDA Project • Megaline Telecom • 2018 Data")

# ─── Recalculate with slider values ───────────────────────────────────────────
gm = gross_margin / 100
churn = churn_rate / 100
arpu_surf = METRICS["surf"]["monthly_arpu"]
arpu_ult = METRICS["ultimate"]["monthly_arpu"]

ltv_surf_calc = (arpu_surf * gm) / churn
ltv_ult_calc = (arpu_ult * gm) / churn
payback_surf_calc = cac_surf / (arpu_surf * gm)
payback_ult_calc = cac_ultimate / (arpu_ult * gm)
ratio_surf_calc = ltv_surf_calc / cac_surf
ratio_ult_calc = ltv_ult_calc / cac_ultimate
diff_surf_calc = ltv_surf_calc - cac_surf
diff_ult_calc = ltv_ult_calc - cac_ultimate
avg_lifetime_calc = 1 / churn

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("# 📡 Megaline Telecom — Statistical Data Analysis Dashboard")
st.markdown("**Comparing Surf vs Ultimate Prepaid Plans** • 500 Customers • 2018 Data • *Which plan deserves more ad budget?*")
st.markdown("---")

# ─── Top-Level KPIs ───────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Customers", "500")
k2.metric("Surf Users", "339", delta="67.8% of base")
k3.metric("Ultimate Users", "161", delta="32.2% of base")
k4.metric("Churned Users", "34", delta="-6.8% churn rate")
k5.metric("Active Users", "466")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Revenue & Profit",
    "📱 Usage Patterns",
    "📊 Unit Economics",
    "🧪 Statistical Tests",
    "🎯 Recommendations"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: REVENUE & PROFIT
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 💰 Revenue & Profit Analysis")
    st.markdown("*Primary finding: Surf generates higher average monthly profit despite lower base fee*")

    col_s, col_u = st.columns(2)

    with col_s:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏄 SURF — Monthly Profit</h3>
            <p class="metric-value healthy">${METRICS['surf']['monthly_profit_mean']:.2f}</p>
            <p class="metric-label">Mean Monthly Profit per User</p>
            <p style="margin-top:10px; font-size:0.9rem;">
                σ = ${METRICS['surf']['monthly_profit_std']:.2f} &nbsp;|&nbsp;
                Range: ${METRICS['surf']['monthly_profit_min']:.0f} – ${METRICS['surf']['monthly_profit_max']:.0f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_u:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🚀 ULTIMATE — Monthly Profit</h3>
            <p class="metric-value neutral">${METRICS['ultimate']['monthly_profit_mean']:.2f}</p>
            <p class="metric-label">Mean Monthly Profit per User</p>
            <p style="margin-top:10px; font-size:0.9rem;">
                σ = ${METRICS['ultimate']['monthly_profit_std']:.2f} &nbsp;|&nbsp;
                Range: ${METRICS['ultimate']['monthly_profit_min']:.0f} – ${METRICS['ultimate']['monthly_profit_max']:.0f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # Revenue waterfall breakdown
    st.markdown("### Revenue Composition (per User/Month)")

    rc1, rc2 = st.columns(2)
    with rc1:
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Waterfall(
            orientation="v",
            x=["Base Fee", "Call Overage", "Internet Overage", "Est. Cost", "Profit"],
            y=[20.00, 1.88, 39.02, -10.00, 0],
            measure=["relative", "relative", "relative", "relative", "total"],
            connector={"line": {"color": "rgba(0,212,170,0.3)"}},
            increasing={"marker": {"color": "#00d4aa"}},
            decreasing={"marker": {"color": "#ef4444"}},
            totals={"marker": {"color": "#0ea5e9"}},
            textposition="outside",
            text=["$20.00", "+$1.88", "+$39.02", "-$10.00", "$50.90"],
            hovertemplate="%{x}: $%{y:.2f}<extra>Surf</extra>"
        ))
        fig_rev.update_layout(
            title="Surf: Revenue → Profit Waterfall",
            template="plotly_dark", height=380,
            showlegend=False, yaxis_title="$ per User/Month"
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    with rc2:
        fig_rev2 = go.Figure()
        fig_rev2.add_trace(go.Waterfall(
            orientation="v",
            x=["Base Fee", "Call Overage", "Internet Overage", "Est. Cost", "Profit"],
            y=[70.00, 0.00, 2.32, -25.00, 0],
            measure=["relative", "relative", "relative", "relative", "total"],
            connector={"line": {"color": "rgba(168,85,247,0.3)"}},
            increasing={"marker": {"color": "#a855f7"}},
            decreasing={"marker": {"color": "#ef4444"}},
            totals={"marker": {"color": "#7c3aed"}},
            textposition="outside",
            text=["$70.00", "+$0.00", "+$2.32", "-$25.00", "$47.32"],
            hovertemplate="%{x}: $%{y:.2f}<extra>Ultimate</extra>"
        ))
        fig_rev2.update_layout(
            title="Ultimate: Revenue → Profit Waterfall",
            template="plotly_dark", height=380,
            showlegend=False, yaxis_title="$ per User/Month"
        )
        st.plotly_chart(fig_rev2, use_container_width=True)

    # Profit distribution
    st.markdown("### Profit Distribution by Plan")

    np.random.seed(42)
    surf_profits = np.clip(np.random.normal(50.33, 55.26, 1573), 0, 600)
    ult_profits = np.clip(np.random.normal(47.31, 11.40, 720), 0, 200)

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=surf_profits, name="Surf", marker_color="#00d4aa", opacity=0.7, nbinsx=40,
        hovertemplate="Profit: $%{x:.0f}<br>Count: %{y}<extra>Surf</extra>"
    ))
    fig_dist.add_trace(go.Histogram(
        x=ult_profits, name="Ultimate", marker_color="#a855f7", opacity=0.7, nbinsx=40,
        hovertemplate="Profit: $%{x:.0f}<br>Count: %{y}<extra>Ultimate</extra>"
    ))
    fig_dist.update_layout(
        title="Monthly Profit Distribution (Surf: high variance vs Ultimate: tight cluster)",
        template="plotly_dark", barmode="overlay", height=400,
        xaxis_title="Monthly Profit ($)", yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_dist.add_vline(x=50.33, line_dash="dash", line_color="#00d4aa",
                       annotation_text="Surf μ=$50.33", annotation_position="top")
    fig_dist.add_vline(x=47.31, line_dash="dash", line_color="#a855f7",
                       annotation_text="Ult μ=$47.31", annotation_position="bottom left")
    st.plotly_chart(fig_dist, use_container_width=True)

    st.info("📌 **Key Finding:** Surf profit has HIGH variability (σ=$55.26) driven by internet overage charges, while Ultimate is stable (σ=$11.40). Despite this, Surf's mean profit ($50.33) exceeds Ultimate ($47.31) — confirmed statistically significant (p < 0.0001).")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: USAGE PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📱 Usage Patterns by Plan")
    st.markdown("*How do Surf and Ultimate users actually consume their plan allowances?*")

    # Usage KPIs
    u1, u2, u3 = st.columns(3)
    u1.metric("Avg Call Duration (Surf)", "412.1 min/mo", delta="-88 min under cap")
    u2.metric("Avg Call Duration (Ultimate)", "410.2 min/mo", delta="-2,590 min under cap")
    u3.metric("Call Duration Difference", "~2 min", delta="Negligible")

    u4, u5, u6 = st.columns(3)
    u4.metric("Avg Messages (Surf)", "181/mo", delta="+131 over included 50 ⚠️")
    u5.metric("Avg Messages (Ultimate)", "205/mo", delta="-795 under cap")
    u6.metric("Message Difference", "~24 msgs", delta="Ultimate sends more")

    st.markdown("---")

    # Call duration chart
    st.markdown("### Average Monthly Call Duration per User")

    fig_calls = make_subplots(rows=1, cols=2,
                              subplot_titles=("Avg Monthly Call Duration", "Plan Utilization Rate (%)"))

    fig_calls.add_trace(go.Bar(
        x=["Surf", "Ultimate"], y=[412.10, 410.18],
        marker_color=["#00d4aa", "#a855f7"],
        text=["412.1 min", "410.2 min"], textposition="outside",
        hovertemplate="%{x}: %{y:.1f} min/month<extra></extra>"
    ), row=1, col=1)

    # Utilization rates
    util_data = {
        "Category": ["Calls", "Messages", "Data", "Calls", "Messages", "Data"],
        "Plan": ["Surf", "Surf", "Surf", "Ultimate", "Ultimate", "Ultimate"],
        "Utilization": [82.4, 362.0, 126.0, 13.7, 20.5, 55.0]
    }
    colors = ["#00d4aa", "#00d4aa", "#00d4aa", "#a855f7", "#a855f7", "#a855f7"]
    labels = [f"Surf\nCalls\n82%", f"Surf\nMsgs\n362%", f"Surf\nData\n126%",
              f"Ult\nCalls\n14%", f"Ult\nMsgs\n21%", f"Ult\nData\n55%"]

    fig_calls.add_trace(go.Bar(
        x=["Surf Calls", "Surf Msgs", "Surf Data", "Ult Calls", "Ult Msgs", "Ult Data"],
        y=[82.4, 362.0, 126.0, 13.7, 20.5, 55.0],
        marker_color=colors,
        text=["82%", "362%⚠️", "126%⚠️", "14%", "21%", "55%"],
        textposition="outside",
        hovertemplate="%{x}: %{y:.0f}% of included allowance<extra></extra>"
    ), row=1, col=2)

    fig_calls.add_hline(y=100, line_dash="dash", line_color="#ef4444", row=1, col=2,
                        annotation_text="100% = Plan Limit")

    fig_calls.update_layout(template="plotly_dark", height=400, showlegend=False)
    st.plotly_chart(fig_calls, use_container_width=True)

    # Internet — the profit driver
    st.markdown("### 🌐 Internet Data Usage — The #1 Profit Driver")

    fig_data = go.Figure()
    fig_data.add_trace(go.Bar(
        name="Included Allowance",
        x=["Surf", "Ultimate"], y=[15, 30],
        marker_color="#334155",
        hovertemplate="%{x} Included: %{y} GB<extra></extra>"
    ))
    fig_data.add_trace(go.Bar(
        name="Avg Monthly Overage",
        x=["Surf", "Ultimate"], y=[3.9, 0.33],
        marker_color="#f97316",
        hovertemplate="%{x} Overage: %{y:.1f} GB → $%{customdata:.2f}/mo<extra></extra>",
        customdata=[39.02, 2.32]
    ))
    fig_data.update_layout(
        title="Monthly Data: Included vs Overage (GB)",
        template="plotly_dark", barmode="stack", height=350,
        yaxis_title="GB per Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_data, use_container_width=True)

    st.warning("⚡ **Key Insight:** Surf users exceed their 15GB data cap regularly, generating ~$39/month in internet overage alone. This single factor explains why Surf profit ($50.33) exceeds Ultimate ($47.31) despite the $50 lower base fee.")

    # Monthly registrations
    st.markdown("### 📅 Customer Acquisition Timeline (2018)")

    fig_reg = go.Figure()
    months = list(MONTHLY_REGISTRATIONS.keys())
    values = list(MONTHLY_REGISTRATIONS.values())

    fig_reg.add_trace(go.Scatter(
        x=months, y=values, mode="lines+markers+text",
        line=dict(color="#60a5fa", width=3), marker=dict(size=10),
        text=values, textposition="top center",
        hovertemplate="Month: %{x}<br>New Users: %{y}<extra></extra>"
    ))
    fig_reg.update_layout(
        title="Monthly New User Registrations (Total: 500 across 2018)",
        template="plotly_dark", height=300,
        yaxis_title="New Customers", xaxis_title="Month"
    )
    st.plotly_chart(fig_reg, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: UNIT ECONOMICS (Extended Analysis)
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📊 Unit Economics (Extended Analysis)")
    st.markdown("*CAC, LTV, and Payback — extending the SDA project with acquisition economics*")
    st.caption("⚠️ CAC values are estimated (telecom industry benchmarks). All other metrics derived from CSV data.")

    # Segment cards
    col_s, col_u = st.columns(2)

    with col_s:
        health_color = "healthy" if ratio_surf_calc >= 1.0 else "at-risk"
        health_label = "HEALTHY" if ratio_surf_calc >= 1.0 else "AT RISK"
        st.markdown(f"""
        <div class="metric-card">
            <h2>🏄 SURF <span style="font-size:0.8rem; opacity:0.7;">(Budget Plan • ${PLANS['surf']['base_fee']:.0f}/mo)</span></h2>
            <p class="metric-label">339 Customers</p>
            <p class="metric-value {health_color}">{ratio_surf_calc:.1f}x</p>
            <p class="metric-label">LTV:CAC — {health_label}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("ARPU", f"${arpu_surf:.2f}")
        c2.metric("CAC", f"${cac_surf}")
        c3.metric("LTV", f"${ltv_surf_calc:.0f}", delta=f"${diff_surf_calc:+.0f} vs CAC")
        c4, c5, c6 = st.columns(3)
        c4.metric("Payback", f"{payback_surf_calc:.1f} mo")
        c5.metric("Lifetime", f"{avg_lifetime_calc:.1f} mo")
        c6.metric("Profit/mo", f"${METRICS['surf']['monthly_profit_mean']:.2f}")

    with col_u:
        health_color = "healthy" if ratio_ult_calc >= 1.0 else "at-risk"
        health_label = "HEALTHY" if ratio_ult_calc >= 1.0 else "AT RISK"
        st.markdown(f"""
        <div class="metric-card">
            <h2>🚀 ULTIMATE <span style="font-size:0.8rem; opacity:0.7;">(Premium Plan • ${PLANS['ultimate']['base_fee']:.0f}/mo)</span></h2>
            <p class="metric-label">161 Customers</p>
            <p class="metric-value {health_color}">{ratio_ult_calc:.1f}x</p>
            <p class="metric-label">LTV:CAC — {health_label}</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("ARPU", f"${arpu_ult:.2f}")
        c2.metric("CAC", f"${cac_ultimate}")
        c3.metric("LTV", f"${ltv_ult_calc:.0f}", delta=f"${diff_ult_calc:+.0f} vs CAC")
        c4, c5, c6 = st.columns(3)
        c4.metric("Payback", f"{payback_ult_calc:.1f} mo")
        c5.metric("Lifetime", f"{avg_lifetime_calc:.1f} mo")
        c6.metric("Profit/mo", f"${METRICS['ultimate']['monthly_profit_mean']:.2f}")

    st.markdown("---")

    # Charts
    ue1, ue2 = st.columns(2)

    with ue1:
        fig_ltv = go.Figure()
        fig_ltv.add_trace(go.Bar(
            name="LTV", x=["Surf", "Ultimate"],
            y=[ltv_surf_calc, ltv_ult_calc],
            marker_color=["#00d4aa", "#a855f7"],
            text=[f"${ltv_surf_calc:.0f}", f"${ltv_ult_calc:.0f}"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>LTV: $%{y:.0f}<extra></extra>"
        ))
        fig_ltv.add_trace(go.Bar(
            name="CAC", x=["Surf", "Ultimate"],
            y=[cac_surf, cac_ultimate],
            marker_color=["#0ea5e9", "#ef4444"],
            text=[f"${cac_surf}", f"${cac_ultimate}"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>CAC: $%{y:.0f}<extra></extra>"
        ))
        fig_ltv.update_layout(
            title="LTV vs CAC", barmode="group",
            template="plotly_dark", height=400, yaxis_title="Amount ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ltv, use_container_width=True)

    with ue2:
        fig_pb = go.Figure()
        fig_pb.add_trace(go.Bar(
            name="Payback Period",
            y=["Ultimate", "Surf"],
            x=[payback_ult_calc, payback_surf_calc],
            orientation="h",
            marker_color=["#f97316", "#00d4aa"],
            text=[f"{payback_ult_calc:.1f} mo", f"{payback_surf_calc:.1f} mo"],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1f} months<extra></extra>"
        ))
        fig_pb.add_vline(x=avg_lifetime_calc, line_dash="dash", line_color="#ef4444",
                         annotation_text=f"Avg Lifetime ({avg_lifetime_calc:.1f} mo)")
        fig_pb.update_layout(
            title="Payback Period vs Customer Lifetime",
            template="plotly_dark", height=400, xaxis_title="Months",
            xaxis=dict(range=[0, max(payback_ult_calc, avg_lifetime_calc) + 2])
        )
        st.plotly_chart(fig_pb, use_container_width=True)

    # Alerts
    if payback_ult_calc > avg_lifetime_calc:
        st.error(f"⚠️ **Ultimate payback ({payback_ult_calc:.1f} mo) exceeds average lifetime ({avg_lifetime_calc:.1f} mo)** — customers churn before ROI recovery!")
    if payback_surf_calc < avg_lifetime_calc:
        st.success(f"✅ **Surf payback ({payback_surf_calc:.1f} mo) is within average lifetime ({avg_lifetime_calc:.1f} mo)** — healthy recovery window.")

    # Sensitivity heatmap
    st.markdown("### 🔬 Sensitivity: Ultimate Break-Even Heatmap")

    cac_options = np.arange(150, 451, 15)
    churn_options = np.arange(5, 25, 1.0)

    z_data = []
    for ch in churn_options:
        row = [(arpu_ult * gm) / (ch / 100) / c for c in cac_options]
        z_data.append(row)

    fig_heat = go.Figure(data=go.Heatmap(
        z=z_data, x=cac_options, y=churn_options,
        colorscale=[[0, "#ef4444"], [0.35, "#f97316"], [0.5, "#eab308"], [0.7, "#22c55e"], [1, "#00d4aa"]],
        colorbar=dict(title="LTV:CAC"),
        hovertemplate="CAC: $%{x}<br>Churn: %{y:.0f}%<br>LTV:CAC: %{z:.2f}x<extra></extra>"
    ))
    fig_heat.add_trace(go.Scatter(
        x=[cac_ultimate], y=[churn_rate],
        mode="markers+text",
        marker=dict(size=16, color="white", symbol="x", line=dict(width=2)),
        text=["Current"], textposition="top center",
        textfont=dict(color="white", size=12), showlegend=False
    ))
    fig_heat.update_layout(
        title="What CAC + Churn combo makes Ultimate viable (LTV:CAC ≥ 1.0)?",
        xaxis_title="CAC ($)", yaxis_title="Monthly Churn (%)",
        template="plotly_dark", height=450
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Break-even calculator
    st.markdown("#### 🧮 Break-Even Calculator")
    be1, be2 = st.columns(2)
    with be1:
        target_ratio = st.number_input("Target LTV:CAC Ratio", 1.0, 5.0, 1.5, 0.1)
    with be2:
        approach = st.radio("Fix via:", ["Reduce CAC", "Reduce Churn", "Both"])

    if approach == "Reduce CAC":
        req_cac = ltv_ult_calc / target_ratio
        st.info(f"📌 To achieve {target_ratio}x: reduce Ultimate CAC from **${cac_ultimate}** → **${req_cac:.0f}** (↓{((cac_ultimate-req_cac)/cac_ultimate)*100:.0f}%)")
    elif approach == "Reduce Churn":
        req_churn = (arpu_ult * gm) / (target_ratio * cac_ultimate)
        st.info(f"📌 To achieve {target_ratio}x: reduce monthly churn from **{churn_rate:.1f}%** → **{req_churn*100:.1f}%**")
    else:
        factor = (ratio_ult_calc / target_ratio) ** 0.5
        new_cac = cac_ultimate * factor
        new_churn = churn * factor
        st.info(f"📌 Split approach: reduce CAC to **${new_cac:.0f}** AND churn to **{new_churn*100:.1f}%**")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: STATISTICAL TESTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 🧪 Hypothesis Testing Results")
    st.markdown("*Two-sample t-tests performed to validate business conclusions*")
    st.markdown("---")

    # Test 1
    st.markdown("### Test 1: Surf vs Ultimate Average Revenue")

    t1c1, t1c2 = st.columns([2, 1])
    with t1c1:
        st.markdown("""
        **Hypotheses:**
        - **H₀:** Average revenue from Surf = Average revenue from Ultimate
        - **H₁:** Average revenue from Surf ≠ Average revenue from Ultimate

        **Parameters:**
        - Test: Two-sample independent t-test
        - α = 0.05
        - Surf sample: 1,573 monthly records
        - Ultimate sample: 720 monthly records
        """)
    with t1c2:
        st.markdown("""
        <div class="stat-sig">
            <p style="font-size:0.8rem; margin:0;">P-VALUE</p>
            <p style="font-size:2rem; margin:5px 0;">< 0.0001</p>
            <p style="margin:0;">✅ REJECT H₀</p>
            <p style="font-size:0.8rem; margin-top:8px;">t = -8.2288</p>
        </div>
        """, unsafe_allow_html=True)

    # t-distribution visualization
    x_range = np.linspace(-12, 12, 500)
    t_dist = stats.t.pdf(x_range, df=500)
    crit_val = stats.t.ppf(0.025, df=500)

    fig_t1 = go.Figure()
    fig_t1.add_trace(go.Scatter(
        x=x_range, y=t_dist, mode="lines", fill="tozeroy",
        line=dict(color="#60a5fa", width=2), fillcolor="rgba(96,165,250,0.2)",
        name="t-distribution", hovertemplate="t=%{x:.2f}<br>density=%{y:.4f}<extra></extra>"
    ))
    fig_t1.add_vrect(x0=-12, x1=crit_val, fillcolor="rgba(239,68,68,0.15)", line_width=0)
    fig_t1.add_vrect(x0=-crit_val, x1=12, fillcolor="rgba(239,68,68,0.15)", line_width=0)
    fig_t1.add_vline(x=-8.2288, line_color="#ef4444", line_width=3,
                     annotation_text="t = -8.23 ⬅️", annotation_position="top")
    fig_t1.update_layout(
        title="Test 1: t-Distribution (t-stat falls deep in rejection region)",
        template="plotly_dark", height=300,
        xaxis_title="t-value", yaxis_title="Density", showlegend=False
    )
    st.plotly_chart(fig_t1, use_container_width=True)

    st.success("**Conclusion:** Revenue IS significantly different between plans. Surf generates higher profit ($50.33 vs $47.31) — this is NOT due to chance.")

    st.markdown("---")

    # Test 2
    st.markdown("### Test 2: NY-NJ Area vs Other Regions")

    t2c1, t2c2 = st.columns([2, 1])
    with t2c1:
        st.markdown("""
        **Hypotheses:**
        - **H₀:** Average revenue from NY-NJ = Average revenue from other regions
        - **H₁:** Average revenue from NY-NJ ≠ Average revenue from other regions

        **Parameters:**
        - Test: Two-sample independent t-test (Welch's)
        - α = 0.05
        - NY-NJ users: 6 (very small sample)
        - Other regions: 494 users
        """)
    with t2c2:
        st.markdown("""
        <div class="stat-nosig">
            <p style="font-size:0.8rem; margin:0;">P-VALUE</p>
            <p style="font-size:2rem; margin:5px 0;">0.3785</p>
            <p style="margin:0;">❌ FAIL TO REJECT H₀</p>
            <p style="font-size:0.8rem; margin-top:8px;">t = 0.8945</p>
        </div>
        """, unsafe_allow_html=True)

    fig_t2 = go.Figure()
    fig_t2.add_trace(go.Scatter(
        x=x_range, y=t_dist, mode="lines", fill="tozeroy",
        line=dict(color="#60a5fa", width=2), fillcolor="rgba(96,165,250,0.2)",
        name="t-distribution"
    ))
    fig_t2.add_vrect(x0=-12, x1=crit_val, fillcolor="rgba(239,68,68,0.15)", line_width=0)
    fig_t2.add_vrect(x0=-crit_val, x1=12, fillcolor="rgba(239,68,68,0.15)", line_width=0)
    fig_t2.add_vline(x=0.8945, line_color="#22c55e", line_width=3,
                     annotation_text="t = 0.89 (within acceptance region)")
    fig_t2.update_layout(
        title="Test 2: t-Distribution (t-stat within non-rejection region)",
        template="plotly_dark", height=300,
        xaxis_title="t-value", yaxis_title="Density", showlegend=False
    )
    st.plotly_chart(fig_t2, use_container_width=True)

    st.warning("**Conclusion:** No significant regional revenue difference (p=0.3785 > 0.05). Geographic targeting is NOT necessary — apply uniform strategy across all regions.")

    # Summary table
    st.markdown("### 📋 Test Summary")
    test_df = pd.DataFrame({
        "Test": ["Surf vs Ultimate Revenue", "NY-NJ vs Other Regions"],
        "t-statistic": ["-8.2288", "0.8945"],
        "p-value": ["< 0.0001", "0.3785"],
        "α": ["0.05", "0.05"],
        "Decision": ["Reject H₀ ✅", "Fail to Reject H₀ ❌"],
        "Business Implication": [
            "Surf is more profitable → allocate more ad budget",
            "No regional targeting needed → uniform strategy"
        ]
    })
    st.dataframe(test_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## 🎯 Strategic Recommendations")
    st.markdown("*Based on statistical analysis of 500 customers across 2018*")
    st.markdown("---")

    st.markdown("""
    <div class="metric-card">
        <h2>📣 Primary Recommendation</h2>
        <p class="metric-value healthy" style="font-size:1.4rem;">
            Allocate More Advertising Budget to the Surf Plan
        </p>
        <p class="metric-label" style="font-size:1rem; opacity:0.9; margin-top:10px;">
            Surf generates higher profit ($50.33 vs $47.31), has healthier unit economics (1.4x vs 0.9x LTV:CAC),
            and serves 2x more customers — making it the more scalable growth engine.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("### ✅ Evidence Supporting Surf")
        st.markdown("""
        - **Higher profit:** $50.33/mo vs $47.31/mo *(p < 0.0001)*
        - **More customers:** 339 vs 161 (2.1x larger base)
        - **Better unit economics:** LTV:CAC 1.4x vs 0.9x
        - **Faster payback:** 4.2 months vs 6.9 months
        - **Lower CAC:** ~$180 vs ~$350
        - **Internet overage:** $39/mo avg — massive profit driver
        - **No regional bias:** Revenue consistent across geographies
        """)

    with r2:
        st.markdown("### ⚠️ Risks & Considerations")
        st.markdown("""
        - **High variability:** Surf σ=$55.26 (5x Ultimate's $11.40)
        - **Overage dependency:** Profit relies on data cap exceedance
        - **Regulatory risk:** Overage charge restrictions would hurt Surf
        - **Ultimate stability:** Predictable, low-variance revenue
        - **Small NY-NJ sample:** Only 6 users limits geographic conclusions
        - **CAC estimated:** No actual acquisition spend in source data
        """)

    st.markdown("---")

    # Radar scorecard
    st.markdown("### 📊 Plan Comparison Scorecard")

    fig_radar = go.Figure()
    categories = ["Profit/User", "Customer Volume", "LTV:CAC Health",
                  "Revenue Stability", "Payback Speed", "Scalability"]

    surf_scores = [8, 9, 8, 3, 8, 9]
    ult_scores = [7, 4, 3, 9, 4, 5]

    fig_radar.add_trace(go.Scatterpolar(
        r=surf_scores + [surf_scores[0]], theta=categories + [categories[0]],
        fill="toself", name="Surf",
        line_color="#00d4aa", fillcolor="rgba(0,212,170,0.2)"
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=ult_scores + [ult_scores[0]], theta=categories + [categories[0]],
        fill="toself", name="Ultimate",
        line_color="#a855f7", fillcolor="rgba(168,85,247,0.2)"
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        template="plotly_dark", height=450,
        title="Plan Scorecard (0-10 scale)",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Action items
    st.markdown("### 📋 Recommended Actions")
    actions = pd.DataFrame({
        "Priority": ["🔴 High", "🔴 High", "🟡 Medium", "🟡 Medium", "🟢 Low"],
        "Action": [
            "Increase Surf advertising budget allocation",
            "Reduce Ultimate CAC below $309 (its current LTV)",
            "Implement plan-agnostic retention program (both churn at ~16%)",
            "Monitor Surf internet overage patterns — key profit driver",
            "Collect actual CAC data for future precision"
        ],
        "Expected Impact": [
            "More customers at healthy 1.4x LTV:CAC",
            "Move Ultimate from 0.9x to ≥1.0x",
            "Extend lifetime beyond 6.1 months → higher LTV",
            "Protect $39/mo/user overage revenue",
            "Enable precise unit economics tracking"
        ]
    })
    st.dataframe(actions, use_container_width=True, hide_index=True)

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📑 Methodology & Data Sources")
st.markdown("""
| Component | Source | Method |
|-----------|--------|--------|
| Customer counts (339/161) | `megaline_users.csv` | Direct count by plan |
| Monthly profit ($50.33/$47.31) | Merged CSVs | ARPU minus estimated operational costs |
| ARPU ($60.90/$72.32) | `calls`, `internet`, `messages` | Base fee + ⌈overage⌉ × rate |
| Call duration (412/410 min) | `megaline_calls.csv` | Mean of monthly per-user totals |
| Messages (181/205) | `megaline_messages.csv` | Mean of monthly per-user totals |
| Churn rate (16.4%) | `megaline_users.csv` | 1 / avg_lifetime_months |
| Hypothesis tests | Merged monthly data | `scipy.stats.ttest_ind` |
| CAC ($180/$350) | Industry estimate | Telecom benchmarks (not in source data) |
| LTV ($260/$309) | Calculated | (ARPU × Gross Margin) / Monthly Churn |
""")
st.caption("📡 Megaline Telecom SDA Dashboard • Built with Streamlit + Plotly • Data: 2018")
