import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

st.set_page_config(
    page_title="HHS Forecast",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>

[data-testid="stSidebar"]{
    padding-top:6rem;
    
    border-radius:12px;

    overflow:hidden;
}

[data-testid="stSidebar"] *{
    line-height:1.5;
}

[data-testid="stSidebar"] label{
    font-size:15px;
}

[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stSlider{
    margin-bottom:18px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.stApp {
    background: transparent;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
padding: 16px 22px;
border-radius: 18px;
background: linear-gradient(
    90deg,
    #1e3a8a,
    #2563eb,
    #3b82f6
);
text-align:center;
margin-bottom: 20px;
">

<h1 class="hero-title"
style="
color:white;
font-size:40px;
margin-bottom:8px;
">
📈 Predictive Forecasting of HHS Care Load
</h1>

<p class="hero-subtitle"
style="
color:white;
font-size:20px;
">
SARIMA/ARIMA-based forecasting dashboard for future care-load planning.
</p>

</div>
""", unsafe_allow_html=True)

st.sidebar.title("🔎 Filters")

st.sidebar.markdown(
    "<div style='margin-bottom:-15px'></div>",
    unsafe_allow_html=True)

df = pd.read_csv("Data/HHS_Unaccompanied_Alien_Children_Program.csv")

# Convert date column
df["Date"] = pd.to_datetime(df["Date"])

# Remove duplicate dates
df = df.drop_duplicates(subset="Date")

# Set datetime index
df = df.set_index("Date")

# Sort dates
df = df.sort_index()

# Daily frequency
df = df.asfreq("D")

st.sidebar.caption(
    "Adjust forecasting horizon."
)

forecast_days = st.sidebar.slider(
    "Forecast Days",
    7,
    90,
    30
)

st.sidebar.subheader("Model Settings")

model_name = st.sidebar.selectbox(
    "Forecast Model",
    [
        "SARIMA",
        "ARIMA",
    ]
)

date_filter = st.sidebar.selectbox(
    "Historical Window",
    [
        "All",
        "Last 12 Months",
        "Last 6 Months"
    ]
)

filtered_df = df.copy()

if date_filter == "Last 12 Months":

    end_date = df.index.max()

    start_date = end_date - pd.DateOffset(months=12)

    filtered_df = df[df.index >= start_date]

elif date_filter == "Last 6 Months":

    end_date = df.index.max()

    start_date = end_date - pd.DateOffset(months=6)

    filtered_df = df[df.index >= start_date]

# Clean numeric columns
numeric_cols = [
    "Children apprehended and placed in CBP custody*",
    "Children in CBP custody",
    "Children transferred out of CBP custody",
    "Children in HHS Care",
    "Children discharged from HHS Care"
]

for col in numeric_cols:

    filtered_df[col] = (
        filtered_df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    filtered_df[col] = pd.to_numeric(
        filtered_df[col],
        errors="coerce"
    )

filtered_df = filtered_df.ffill()

# Target variable
target = "Children in HHS Care"

if model_name == "SARIMA":

    model = SARIMAX(
        filtered_df[target],
        order=(1,1,1),
        seasonal_order=(1,1,1,7)
    )

    model_fit = model.fit(disp=False)

    forecast_obj = model_fit.get_forecast(
        steps=forecast_days
    )

    forecast_mean = forecast_obj.predicted_mean
    conf_int = forecast_obj.conf_int()


elif model_name == "ARIMA":

    model = ARIMA(
        filtered_df[target],
        order=(1,1,1)
    )

    model_fit = model.fit()

    forecast_mean = model_fit.forecast(
        steps=forecast_days
    )

    conf_int = pd.DataFrame({
        "lower": forecast_mean * 0.95,
        "upper": forecast_mean * 1.05
    })

change_pct = (
    (forecast_mean.iloc[-1]
     - filtered_df[target].iloc[-1])
    /
    filtered_df[target].iloc[-1]
) * 100

forecast_change = (
    (forecast_mean.max()
     - filtered_df[target].iloc[-1])
    /
    filtered_df[target].iloc[-1]
) * 100

# Future dates
future_dates = pd.date_range(
    start=filtered_df.index[-1] + pd.Timedelta(days=1),
    periods=forecast_days,
    freq="D"
)

tab1, tab2, tab3 = st.tabs(
    [
        "📊 Overview",
        "📈 Forecast",
        "📋 Data Explorer "
    ]
)

with tab1:

    st.subheader("Forecast Insights")
    
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(
            135deg,
            rgba(37,99,235,0.25),
            rgba(59,130,246,0.10)
        );
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition:0.25s ease;
        
    .metric-card:hover{

    transform:translateY(-4px);

    box-shadow:0 10px 25px rgba(59,130,246,.20);

    }
    
    }
    .metric-title {
        color: inherit;
        font-size: 14px;
        margin-bottom:8px;
        font-weight:500;
    }
    .metric-value {
        color: inherit;
        font-size: 34px;
        font-weight: bold;
    }
    
    @media (max-width:768px){
    .metric-card{
        padding:14px;
    }
    .metric-title{
        font-size:12px;
    }
    .metric-value{
        font-size:24px !important;
    }
    }
    
    @media (max-width:768px){
    .hero-title{
        font-size:34px !important;
    }
    .hero-subtitle{
        font-size:15px !important;
    }
    }
    </style>
    """, unsafe_allow_html=True)

    # ROW 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👥 Current Load</div>
            <div class="metric-value">
                 {int(filtered_df[target].iloc[-1]):,}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Forecast Peak</div>
            <div class="metric-value">
                 {int(forecast_mean.max()):,}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📊 Forecast Change</div>
            <div class="metric-value">
                 {change_pct:.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Forecast Horizon</div>
            <div class="metric-value">
                 {forecast_days} Days
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ROW 2
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📂 Records</div>
            <div class="metric-value">
                 {len(filtered_df):,}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👾 Model</div>
            <div class="metric-value">
                 {model_name}
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📏 Forecast Range</div>
            <div class="metric-value">
                 {int(forecast_mean.min())} - {int(forecast_mean.max())}
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # ROW 3 
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📅 Analysis Period</div>
            <div class="metric-value" style="font-size:34.4px;">
                {filtered_df.index.min().strftime("%d-%b-%Y")}
                →
                {filtered_df.index.max().strftime("%d-%b-%Y")}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🗓️ Data Coverage</div>
            <div class="metric-value">
                {(filtered_df.index.max() - filtered_df.index.min()).days:,} Days
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    st.subheader("Executive Summary")

    st.info(
        f"""
        Current HHS care load stands at
        {int(filtered_df[target].iloc[-1]):,} children.

        The {model_name} model forecasts a peak
        of {int(forecast_mean.max()):,}
        within the next {forecast_days} days.

        Expected overall change:
        {change_pct:.2f}%.

        Forecasts are generated using historical HHS care load trends and should be interpreted as planning estimates rather than exact future values.
        """
        
    )

with tab3:

    st.subheader("Dataset Preview")

    st.dataframe(
        filtered_df.tail(20),
        use_container_width=True
    )

    st.caption(
        f"Showing latest 20 rows out of {len(filtered_df)} records."
    )

historical_fig = px.line(
    filtered_df,
    x=filtered_df.index,
    y=target
)

historical_fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Children Count"
)

forecast_fig = go.Figure()

forecast_fig.add_trace(
    go.Scatter(
        x=filtered_df.index,
        y=filtered_df[target],
        mode="lines",
        name="Historical"
    )
)

forecast_fig.add_trace(
    go.Scatter(
        x=future_dates,
        y=forecast_mean,
        mode="lines",
        name="Forecast"
    )
)

forecast_fig.add_trace(
    go.Scatter(
        x=list(future_dates) + list(future_dates[::-1]),
        y=list(conf_int.iloc[:,1]) +
          list(conf_int.iloc[:,0][::-1]),
        fill="toself",
        fillcolor="rgba(0,176,246,0.25)",
        name="Confidence Interval",
        opacity=0.2
    )
)

forecast_fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Children Count"
    
)

forecast_df = pd.DataFrame({
    "Date": future_dates,
    "Forecast": forecast_mean
})

forecast_df["Forecast"] = (
    forecast_df["Forecast"]
    .round(0)
    .astype(int)
)

forecast_df["Date"] = (
    forecast_df["Date"]
    .dt.strftime("%d-%b-%Y")
)

forecast_fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

with tab2:

    with st.expander("Model Details"):

        m1, m2, m3 = st.columns(3)

        m1.metric("Model", model_name)
        m2.metric("Records", len(filtered_df))
        m3.metric("Horizon", forecast_days)

        if model_name == "SARIMA":
           st.markdown("**Order:** (1,1,1)")
           st.markdown("**Seasonal Order:** (1,1,1,7)")
           st.markdown(
               "**Purpose:** Captures trend and weekly seasonality in HHS care load."
           )

        elif model_name == "ARIMA":
           st.markdown("**Order:** (1,1,1)")
           st.markdown(
               "**Purpose:** Captures trend patterns without seasonal effects."
           )

        st.markdown(
            f"**Analysis Period:** "
            f"{filtered_df.index.min().strftime('%d-%b-%Y')} → "
            f"{filtered_df.index.max().strftime('%d-%b-%Y')}"
        )
        
        st.markdown(f"**Forecast Period:** Next {forecast_days} Days")

    st.subheader("Historical Trends & Forecast Outlook")

    st.plotly_chart(
        forecast_fig,
        use_container_width=True,
        key="forecast_chart"
    )
    
    gauge_fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=forecast_change,
        number={"suffix": "%"},
        delta={
            "reference": 0,
            "relative": False
        },
        title={"text": f"Forecast Peak Change (%)"},
        gauge={
            "axis": {"range": [-10, 10]},
            "bar": {"thickness": 0.8},
            "steps": [
                {"range": [-10, -2], "color": "#ff6b6b"},
                {"range": [-2, 2], "color": "#ffd166"},
                {"range": [2, 10], "color": "#06d6a0"}
            ]
        }
    )
 )

    gauge_fig.update_layout(
       height=340,
       template="plotly",
       margin=dict(t=50, b=20, l=20, r=20)
 )
    
    monthly_df = (
    filtered_df[target]
    .resample("ME")
    .mean()
    .reset_index()
    .round(0)
 )

    monthly_df.columns = [
       "Month",
       "Average HHS Care Load"
 ]
    
    monthly_bar_fig = px.bar(
    monthly_df,
    x="Month",
    y="Average HHS Care Load",
    title="Monthly Average HHS Care Load",
 )

    monthly_bar_fig.update_layout(
    template="plotly",
    xaxis_title="Month",
    yaxis_title="Children Count",
    height=340,
    margin=dict(t=50, b=20, l=20, r=20)
 )

    monthly_bar_fig.update_traces(
    marker_line_width=0
 )
    
    col1, col2 = st.columns([1,1])
    
    with col1:
        st.plotly_chart(gauge_fig, use_container_width=False)
        
    with col2:
        st.plotly_chart(monthly_bar_fig, use_container_width=True)
        
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔻 Forecast Min</div>
            <div class="metric-value">
                 {int(forecast_mean.min()):,}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📊 Forecast Avg</div>
            <div class="metric-value">
                 {int(forecast_mean.mean()):,}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔺 Forecast Max</div>
            <div class="metric-value">
                 {int(forecast_mean.max()):,}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📏 Forecast Std Dev</div>
            <div class="metric-value">
                 {forecast_mean.std():.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)     
    
    st.markdown("---")
    st.subheader("Forecast Value Distribution")
    
    histogram_fig = px.histogram(
        forecast_df,
        x="Forecast",
        nbins=10
 )

    histogram_fig.update_layout(
        template="plotly",
        height=280,
        xaxis_title="Forecasted Children Count",
        yaxis_title="Frequency",
        margin=dict(
        t=20,
        b=20,
        l=20,
        r=20
    )
 )

    histogram_fig.update_traces(
        marker=dict(
            color="#3b82f6",
            line=dict(
                color="#1d4ed8",
                width=1
            )
        )
    )
    
    st.plotly_chart(
       histogram_fig,
       use_container_width=True
 )
    
    with st.expander("Forecast Dataset"):

        st.dataframe(forecast_df)

        st.download_button(
            "📥 Download Forecast CSV",
            forecast_df.to_csv(index=False),
            file_name="hhs_forecast.csv",
            mime="text/csv"
        )
