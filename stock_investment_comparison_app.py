import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt

# --- Set page config ---
st.set_page_config(page_title="Stock Investment Comparison", layout="centered")

st.title("📈 Stock Investment Strategy Comparison")
st.write("Compare **lump sum** vs **recurring investments** (weekly, monthly, or quarterly).")

# --- User Inputs ---
symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, VOO):", "AAPL").upper()
lump_sum_amount = st.number_input("Lump Sum Investment Amount ($):", min_value=0.0, value=6800.0)
recurring_amount = st.number_input("Recurring Investment Amount ($):", min_value=0.0, value=100.0)
frequency = st.selectbox("Select Recurring Investment Frequency:", ["Weekly", "Monthly", "Quarterly"])
user_start_date = st.date_input("Select Start Date for Investment:", datetime(2024, 1, 2))

# --- Functions ---
def fetch_stock_history(symbol, start_date, end_date):
    try:
        stock = yf.Ticker(symbol)
        history = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval="1d")
        return history
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

def check_lump_sum_investment(history, investment_input):
    if history.empty:
        return None
    start_price = history.iloc[0]['Close']
    today_price = history.iloc[-1]['Close']
    shares = investment_input / start_price
    current_value = shares * today_price
    profit_loss = current_value - investment_input
    percent_change = (profit_loss / investment_input) * 100
    return {
        "Initial Investment": investment_input,
        "Shares Bought": shares,
        "Current Value": current_value,
        "Profit/Loss": profit_loss,
        "Percentage Change": f"{abs(percent_change):.2f}% {'profit' if percent_change >= 0 else 'loss'}"
    }

def get_interval_days(freq):
    if freq == "Weekly":
        return 7
    elif freq == "Monthly":
        return 30
    elif freq == "Quarterly":
        return 90
    else:
        return 7

def simulate_recurring_investment(history, start_date, today, amount, freq):
    total_investment = 0.0
    total_shares = 0.0
    current_date = start_date
    history_values = history.copy()
    history_values['Investment Value'] = 0.0

    interval_days = get_interval_days(freq)

    while current_date <= today:
        available_dates = history.index[history.index >= current_date]
        if not available_dates.empty:
            closest_date = available_dates[0]
            price = history.loc[closest_date]['Close']
            shares_bought = amount / price
            total_shares += shares_bought
            total_investment += amount
            history_values.at[closest_date, 'Investment Value'] = total_shares * price
        current_date += timedelta(days=interval_days)

    current_price = history.iloc[-1]['Close']
    current_value = total_shares * current_price
    profit_loss = current_value - total_investment
    percent_change = (profit_loss / total_investment) * 100

    return {
        "Total Investment": total_investment,
        "Shares Bought": total_shares,
        "Current Value": current_value,
        "Profit/Loss": profit_loss,
        "Percentage Change": f"{abs(percent_change):.2f}% {'profit' if percent_change >= 0 else 'loss'}"
    }, history_values[['Investment Value']]

# --- Main Logic ---
if st.button("Compare Investment Strategies"):
    start_date = datetime.combine(user_start_date, datetime.min.time())
    today = datetime.today()

    # Localize to Eastern timezone
    eastern = pytz.timezone('America/New_York')
    start_date = eastern.localize(start_date)
    today = eastern.localize(today)

    history = fetch_stock_history(symbol, start_date, today)

    if history is None or history.empty:
        st.warning("No data available for this stock symbol.")
    else:
        st.success(f"Data fetched for {symbol}")

        lump_sum_result = check_lump_sum_investment(history, lump_sum_amount)
        recurring_result, recurring_values = simulate_recurring_investment(history, start_date, today, recurring_amount, frequency)

        # --- Display results ---
        st.subheader("📊 Comparison Summary")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Lump Sum Investment")
            for k, v in lump_sum_result.items():
                st.write(f"**{k}:** {'$' + str(round(v, 2)) if isinstance(v, float) else v}")

        with col2:
            st.markdown(f"### {frequency} Investment")
            for k, v in recurring_result.items():
                st.write(f"**{k}:** {'$' + str(round(v, 2)) if isinstance(v, float) else v}")

        # --- Plot line chart ---
        st.subheader("📈 Investment Value Over Time")

        lump_sum_value = history['Close'] * (lump_sum_amount / history.iloc[0]['Close'])

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(history.index, lump_sum_value, label='Lump Sum Value', color='blue')
        ax.plot(recurring_values.index, recurring_values['Investment Value'], label=f'{frequency} Investment Value', color='orange')
        ax.set_title(f"{symbol} Investment Strategy Comparison")
        ax.set_xlabel("Date")
        ax.set_ylabel("Investment Value ($)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        st.pyplot(fig)
