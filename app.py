import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

def calculate_portfolio():

    conn = sqlite3.connect("model_portfolio.db")
    cursor = conn.cursor()

    holdings = cursor.execute("""
    SELECT fund_id, fund_name, current_value
    FROM client_holdings
    WHERE client_id='C001'
    """).fetchall()

    model = cursor.execute("""
    SELECT fund_id, allocation_pct
    FROM model_funds
    """).fetchall()

    model_dict = {m[0]: m[1] for m in model}

    portfolio_value = sum(h[2] for h in holdings)

    results = []

    total_buy = 0
    total_sell = 0

    for fund_id, fund_name, value in holdings:

        current_pct = (value / portfolio_value) * 100
        target_pct = model_dict.get(fund_id)

        if target_pct is None:
            action = "REVIEW"
            amount = value

        else:
            drift = target_pct - current_pct
            amount = (drift / 100) * portfolio_value

            if amount > 0:
                action = "BUY"
                total_buy += amount
            else:
                action = "SELL"
                total_sell += abs(amount)

        results.append({
            "fund": fund_name,
            "current_pct": round(current_pct,2),
            "target_pct": target_pct,
            "action": action,
            "amount": round(abs(amount))
        })

    conn.close()

    net_cash = total_buy - total_sell

    return results, portfolio_value, round(total_buy), round(total_sell), round(net_cash)


@app.route("/")
def home():

    data, total, buy, sell, cash = calculate_portfolio()

    return render_template(
        "index.html",
        data=data,
        total=total,
        buy=buy,
        sell=sell,
        cash=cash
    )


if __name__ == "__main__":
    app.run(debug=True)