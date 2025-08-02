import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from fpdf import FPDF
import tempfile
import os

# Page config
st.set_page_config(page_title="FinFit Dashboard", layout="wide")

# Role selector in sidebar
user_mode = st.sidebar.selectbox(
    "Select Role",
    ["Coach", "Client", "Admin", "Funder"],
    index=0
)

st.title(f"FinFit {'Client' if user_mode == 'Client' else ''} Dashboard")

# Load your data



@st.cache_data
def load_data():
    # Always use the static CSV for now
    df = pd.read_csv("dummy_finfit_data.csv")
    return df, False

df, has_time_series = load_data()

# Calculate derived column
df["Total_Expenses"] = df["Expenses_Fixed"] + df["Expenses_Variable"] + df["Expenses_Discretionary"]


## Remove duplicate sidebar filter block and ensure all multiselects have unique keys
## Only keep the role-based filter blocks below, which already have unique keys

# Add date filter for time-series data
st.sidebar.header("Filter Clients")
if has_time_series:
    st.sidebar.subheader("Time Period")
    view_mode = st.sidebar.radio("View Mode", ["Latest Month", "All Months (Trend)"], key="view_mode")
    if view_mode == "Latest Month":
        selected_date = st.sidebar.selectbox(
            "Select Month",
            options=df["Date"].dt.strftime("%Y-%m").unique(),
            format_func=lambda x: pd.to_datetime(x).strftime("%B %Y"),
            key="selected_month"
        )
        df = df[df["Date"].dt.strftime("%Y-%m") == selected_date]
    # Note: When in "All Months" mode, we keep all dates for trending


# ...existing code...

def generate_smart_tips(client_data):
    """Generate personalized financial tips based on client metrics."""
    tips = []
    
    if client_data["Total_Expenses"] > client_data["Net_Income"]:
        tips.append({
            "icon": "🔍",
            "title": "Budget Alert",
            "tip": "Your expenses exceed your income. Consider reducing discretionary spending by tracking daily expenses.",
            "severity": "error"
        })
    
    if client_data["Debt_to_Income"] > 0.5:
        tips.append({
            "icon": "⚠️",
            "title": "High Debt Load",
            "tip": "Your debt payments are high relative to income. Consider debt consolidation or speaking with a financial advisor.",
            "severity": "warning"
        })
    
    if client_data["Savings_to_Income"] < 0.1:
        tips.append({
            "icon": "💰",
            "title": "Low Savings",
            "tip": "Try to save at least 10% of your income. Consider setting up automatic transfers to a savings account.",
            "severity": "info"
        })
    
    if client_data["Financial_Stress_Index"] > 70:
        tips.append({
            "icon": "🎯",
            "title": "High Stress Level",
            "tip": "Your financial stress is elevated. Schedule a session with our financial wellness coach.",
            "severity": "warning"
        })
    
    if not tips:
        tips.append({
            "icon": "✨",
            "title": "On Track!",
            "tip": "You're managing your finances well. Keep up the good work!",
            "severity": "success"
        })
    
    return tips

# Sidebar filters based on role
st.sidebar.header("Filters")

if user_mode == "Coach":
    # Coach-specific filters
    risk_filter = st.sidebar.multiselect(
        "Risk Factors",
        ["High Debt", "Low Savings", "High Stress"],
        default=[]
    )
    gender_filter = st.sidebar.multiselect("Gender", options=df["Gender"].unique(), default=df["Gender"].unique())
    region_filter = st.sidebar.multiselect("Region", options=df["Region"].unique(), default=df["Region"].unique())
    pattern_filter = st.sidebar.multiselect("Spending Pattern", options=df["Spending_Pattern"].unique(), default=df["Spending_Pattern"].unique())
    # Apply filters with risk factors
    filtered_df = df[
        (df["Region"].isin(region_filter)) &
        (df["Spending_Pattern"].isin(pattern_filter)) &
        (df["Gender"].isin(gender_filter))
    ]
    # Apply risk filters
    if "High Debt" in risk_filter:
        filtered_df = filtered_df[filtered_df["Debt_to_Income"] > 0.5]
    if "Low Savings" in risk_filter:
        filtered_df = filtered_df[filtered_df["Savings_to_Income"] < 0.1]
    if "High Stress" in risk_filter:
        filtered_df = filtered_df[filtered_df["Financial_Stress_Index"] > 70]

elif user_mode == "Client":
    # Simulate client login with demo ID selection
    client_login = st.sidebar.selectbox("Demo Client ID", options=df["Client_ID"].unique())
    filtered_df = df[df["Client_ID"] == client_login]

elif user_mode == "Admin":
    # Admin filters
    gender_filter = st.sidebar.multiselect("Gender", options=df["Gender"].unique(), default=df["Gender"].unique())
    region_filter = st.sidebar.multiselect("Region", options=df["Region"].unique(), default=df["Region"].unique())
    metric_filter = st.sidebar.multiselect(
        "Key Metrics",
        ["Financial Wellness", "Stress Index", "Debt Ratio", "Savings Rate"],
        default=["Financial Wellness"]
    )
    filtered_df = df[(df["Region"].isin(region_filter)) & (df["Gender"].isin(gender_filter))]

else:  # Funder view
    # Region and gender filter for funders
    gender_filter = st.sidebar.multiselect("Gender", options=df["Gender"].unique(), default=df["Gender"].unique())
    region_filter = st.sidebar.multiselect("Region", options=df["Region"].unique(), default=df["Region"].unique())
    filtered_df = df[(df["Region"].isin(region_filter)) & (df["Gender"].isin(gender_filter))].copy()
    # Anonymize client data
    filtered_df["Client_ID"] = filtered_df["Client_ID"].apply(lambda x: f"Client_{hash(x) % 1000:03d}")

# Role-specific KPIs and features
if user_mode == "Coach":
    # Coach KPIs focused on client risk factors
    st.markdown("### Client Risk Overview")
    kpi1, kpi2, kpi3 = st.columns(3)
    total_clients = len(filtered_df)
    high_risk_clients = len(filtered_df[
        (filtered_df["Debt_to_Income"] > 0.5) |
        (filtered_df["Savings_to_Income"] < 0.1) |
        (filtered_df["Financial_Stress_Index"] > 70)
    ])
    
    kpi1.metric("Total Clients", total_clients)
    kpi2.metric("High Risk Clients", high_risk_clients)
    kpi3.metric("Risk Rate", f"{(high_risk_clients/total_clients*100):.1f}%")
    
    # Show flagged clients table
    if high_risk_clients > 0:
        st.markdown("### Flagged Clients")
        risk_df = filtered_df.copy()
        risk_df["Risk Factors"] = risk_df.apply(lambda x: ", ".join([
            "High Debt" if x["Debt_to_Income"] > 0.5 else "",
            "Low Savings" if x["Savings_to_Income"] < 0.1 else "",
            "High Stress" if x["Financial_Stress_Index"] > 70 else ""
        ]).strip(", "), axis=1)
        
        st.dataframe(
            risk_df[risk_df["Risk Factors"] != ""][
                ["Client_ID", "Risk Factors", "Financial_Wellness_Score"]
            ]
        )

elif user_mode == "Client":
    # Client KPIs focused on personal progress
    st.markdown("### Your Financial Overview")
    kpi1, kpi2, kpi3 = st.columns(3)
    client_data = filtered_df.iloc[0]
    
    kpi1.metric("Net Income", f"N$ {client_data['Net_Income']:,.0f}")
    kpi2.metric("Wellness Score", f"{client_data['Financial_Wellness_Score']:.1f}")
    kpi3.metric("Stress Index", client_data["Financial_Stress_Index"])
    
    # Personal recommendations
    st.markdown("### Personal Recommendations")
    if client_data["Savings_to_Income"] < 0.1:
        st.info("💡 Try saving at least 10% of your monthly income")
    if client_data["Debt_to_Income"] > 0.5:
        st.warning("⚠️ Consider reducing your debt burden")
    if client_data["Financial_Stress_Index"] > 70:
        st.error("🎯 Focus on stress management and financial planning")

elif user_mode == "Admin":
    # Admin KPIs focused on overall metrics
    st.markdown("### Performance Metrics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    kpi1.metric("Total Clients", len(filtered_df))
    kpi2.metric("Avg. Wellness Score", f"{filtered_df['Financial_Wellness_Score'].mean():.1f}")
    kpi3.metric("High Risk Clients", len(filtered_df[filtered_df["Financial_Stress_Index"] > 70]))
    kpi4.metric("Avg. Debt Ratio", f"{filtered_df['Debt_to_Income'].mean():.2f}")

else:  # Funder view
    # Funder KPIs focused on impact metrics
    st.markdown("### Impact Metrics")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    kpi1.metric("Clients Served", len(filtered_df))
    kpi2.metric("Avg. Wellness Score", f"{filtered_df['Financial_Wellness_Score'].mean():.1f}")
    kpi3.metric(
        "Stress Reduction",
        f"{(70 - filtered_df['Financial_Stress_Index'].mean()):.1f}%",
        delta="↓ 12%"
    )

# Show Flagged Clients for Coach and Admin views
if user_mode in ["Coach", "Admin"]:
    st.markdown("### 🚨 Flagged Clients")
    
    # Create risk dataframe
    risk_df = filtered_df.copy()
    risk_df["Risk_Tags"] = risk_df.apply(lambda x: ", ".join(filter(None, [
        "High Debt" if x["Debt_to_Income"] > 0.5 else "",
        "Low Savings" if x["Savings_to_Income"] < 0.1 else "",
        "High Stress" if x["Financial_Stress_Index"] > 70 else "",
        "Negative Worth" if x["Net_Worth"] < 0 else ""
    ])), axis=1)
    
    # Filter only clients with risks
    flagged_df = risk_df[risk_df["Risk_Tags"] != ""][
        ["Client_ID", "Region", "Debt_to_Income", "Savings_to_Income", 
         "Financial_Stress_Index", "Risk_Tags"]
    ].sort_values("Financial_Stress_Index", ascending=False)
    
    if not flagged_df.empty:
        st.dataframe(
            flagged_df,
            column_config={
                "Client_ID": "Client ID",
                "Debt_to_Income": st.column_config.NumberColumn(
                    "Debt Ratio",
                    format="%.2f",
                    help="Debt-to-Income Ratio"
                ),
                "Savings_to_Income": st.column_config.NumberColumn(
                    "Savings Ratio",
                    format="%.2f",
                    help="Savings-to-Income Ratio"
                ),
                "Financial_Stress_Index": st.column_config.NumberColumn(
                    "Stress Index",
                    help="Financial Stress Index (0-100)"
                ),
                "Risk_Tags": "Risk Factors"
            },
            hide_index=True
        )
        
        # Option to download flagged clients report
        if st.button("Download Flagged Clients Report"):
            flagged_df.to_csv("flagged_clients.csv", index=False)
            with open("flagged_clients.csv", "rb") as f:
                st.download_button(
                    "Download CSV",
                    f,
                    file_name="flagged_clients.csv",
                    mime="text/csv"
                )
    else:
        st.success("🎉 No clients currently flagged for risk factors!")

# Show raw data
with st.expander("View Raw Data"):
    st.dataframe(filtered_df)

# Visualization Settings
st.subheader("Financial Metrics Visualization")
viz_container = st.container()

# Chart Type Selection
chart_type = st.radio(
    "Select Chart Type",
    ["Interactive (Plotly)", "Static (Matplotlib)"],
    horizontal=True
)

# Metric Selection for Y-axis
y_metric = st.selectbox(
    "Select Metric to Compare with Net Income",
    ["Total_Expenses", "Financial_Wellness_Score", "Financial_Stress_Index"],
    index=0
)

# Create visualizations based on selection
if chart_type == "Interactive (Plotly)":
    # Plotly scatter plot
    fig = px.scatter(
        filtered_df,
        x="Net_Income",
        y=y_metric,
        color="Spending_Pattern",
        hover_data=["Client_ID", "Region", "Gender"],
        title=f"Net Income vs {y_metric.replace('_', ' ')}",
        template="simple_white"
    )
    
    # Update layout for better appearance
    fig.update_layout(
        height=600,
        xaxis_title="Net Income (N$)",
        yaxis_title=y_metric.replace("_", " "),
        legend_title="Spending Pattern",
        showlegend=True
    )
    
    # Display the plot
    st.plotly_chart(fig, use_container_width=True)

else:
    # Matplotlib/Seaborn static plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=filtered_df,
        x="Net_Income",
        y=y_metric,
        hue="Spending_Pattern",
        ax=ax
    )
    ax.set_title(f"Net Income vs {y_metric.replace('_', ' ')}")
    ax.set_xlabel("Net Income (N$)")
    ax.set_ylabel(y_metric.replace("_", " "))
    st.pyplot(fig)

# --- Client Scorecard ---
st.subheader("Client Scorecard")

def generate_pdf(client_row):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", size=16)
    pdf.cell(0, 10, "FinFit Financial Wellness Report", ln=True, align="C")
    pdf.ln(10)
    
    # Client Information
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(0, 10, "Client Profile", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Client ID: {client_row['Client_ID']}", ln=True)
    pdf.cell(0, 10, f"Region: {client_row['Region']}", ln=True)
    pdf.cell(0, 10, f"Gender: {client_row['Gender']}", ln=True)
    pdf.cell(0, 10, f"Financial Personality: {client_row['Financial_Personality']}", ln=True)
    pdf.cell(0, 10, f"Spending Pattern: {client_row['Spending_Pattern']}", ln=True)
    pdf.ln(10)
    
    # Financial Metrics
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(0, 10, "Financial Overview", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Net Income: N$ {client_row['Net_Income']:,.0f}", ln=True)
    pdf.cell(0, 10, f"Total Expenses: N$ {client_row['Total_Expenses']:,.0f}", ln=True)
    pdf.cell(0, 10, f"Savings-to-Income Ratio: {client_row['Savings_to_Income']:.2f}", ln=True)
    pdf.cell(0, 10, f"Debt-to-Income Ratio: {client_row['Debt_to_Income']:.2f}", ln=True)
    pdf.ln(10)
    
    # Wellness Indicators
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(0, 10, "Wellness Indicators", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Financial Stress Index: {client_row['Financial_Stress_Index']}", ln=True)
    pdf.cell(0, 10, f"Happiness Index: {client_row['Happiness_Index']}", ln=True)
    pdf.cell(0, 10, f"Financial Wellness Score: {client_row['Financial_Wellness_Score']}", ln=True)
    pdf.ln(10)
    
    # Progress Summary (simulated trends)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(0, 10, "Progress Summary", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    # Simulate progress metrics (in real app, use historical data)
    stress_change = -12  # Example: 12% reduction in stress
    wellness_change = 8  # Example: 8% improvement in wellness
    savings_change = 15  # Example: 15% increase in savings
    
    pdf.cell(0, 10, f"Stress Level: {'-' if stress_change < 0 else '+'}{abs(stress_change)}%", ln=True)
    pdf.cell(0, 10, f"Wellness Score: {'+' if wellness_change > 0 else '-'}{abs(wellness_change)}%", ln=True)
    pdf.cell(0, 10, f"Savings Rate: {'+' if savings_change > 0 else '-'}{abs(savings_change)}%", ln=True)
    pdf.ln(10)
    
    # Smart Tips
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(0, 10, "Personalized Recommendations", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    tips = generate_smart_tips(client_row)
    for tip in tips:
        # Remove emoji icons for PDF
        pdf.multi_cell(0, 10, f"{tip['title']}: {tip['tip']}")
    pdf.ln(5)

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

if not filtered_df.empty:
    client_id = st.selectbox("Select Client", options=filtered_df["Client_ID"].unique())
    client_row = filtered_df[filtered_df["Client_ID"] == client_id].iloc[0]

    with st.container():
        st.markdown(f"**Region:** {client_row['Region']}")
        st.markdown(f"**Gender:** {client_row['Gender']}")
        st.markdown(f"**Financial Personality:** {client_row['Financial_Personality']}")
        st.markdown(f"**Spending Pattern:** {client_row['Spending_Pattern']}")
        
        st.markdown("---")
        st.markdown(f"**Net Income:** N$ {client_row['Net_Income']:,.0f}")
        st.markdown(f"**Total Expenses:** N$ {client_row['Total_Expenses']:,.0f}")
        st.markdown(f"**Savings-to-Income Ratio:** {client_row['Savings_to_Income']:.2f}")
        st.markdown(f"**Debt-to-Income Ratio:** {client_row['Debt_to_Income']:.2f}")
        
        st.markdown("---")
        st.markdown(f"**Financial Stress Index:** {client_row['Financial_Stress_Index']}")
        st.markdown(f"**Happiness Index:** {client_row['Happiness_Index']}")
        st.markdown(f"**Financial Wellness Score:** {client_row['Financial_Wellness_Score']}")
        
        st.markdown("---")
        insights = []
        if client_row['Total_Expenses'] > client_row['Net_Income']:
            insights.append("Spending exceeds income.")
        if client_row['Debt_to_Income'] > 0.5:
            insights.append("High debt-to-income ratio.")
        if client_row['Savings_to_Income'] < 0.1:
            insights.append("Low savings rate.")
        if client_row['Financial_Stress_Index'] > 70:
            insights.append("High financial stress.")

        st.markdown("### Smart Financial Tips")
        tips = generate_smart_tips(client_row)
        for tip in tips:
            if tip["severity"] == "error":
                st.error(f"{tip['icon']} **{tip['title']}**: {tip['tip']}")
            elif tip["severity"] == "warning":
                st.warning(f"{tip['icon']} **{tip['title']}**: {tip['tip']}")
            elif tip["severity"] == "info":
                st.info(f"{tip['icon']} **{tip['title']}**: {tip['tip']}")
            else:
                st.success(f"{tip['icon']} **{tip['title']}**: {tip['tip']}")

        # Add PDF download button
        if st.button("Generate PDF Report"):
            pdf_path = generate_pdf(client_row)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download Client Report",
                    f,
                    file_name=f"{client_row['Client_ID']}_Report.pdf",
                    mime="application/pdf"
                )
            # Cleanup temporary file
            os.unlink(pdf_path)
else:
    st.info("No data available with current filters.")
