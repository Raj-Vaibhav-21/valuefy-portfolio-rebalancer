import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)


def get_connection():
    return sqlite3.connect("model_portfolio.db")


def calculate_portfolio():

    conn = get_connection()
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
            drift = None

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
            "fund_id": fund_id,
            "fund": fund_name,
            "current_pct": round(current_pct, 2),
            "target_pct": target_pct,
            "drift": None if drift is None else round(drift, 2),
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


@app.route("/holdings")
def holdings():

    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute("""
    SELECT fund_name, current_value
    FROM client_holdings
    WHERE client_id='C001'
    """).fetchall()

    total = sum(r[1] for r in rows)

    conn.close()

    return render_template("holdings.html", rows=rows, total=total)


@app.route("/history")
def history():

    conn = get_connection()
    cursor = conn.cursor()

    sessions = cursor.execute("""
    SELECT session_id, created_at, portfolio_value, status
    FROM rebalance_sessions
    ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return render_template("history.html", sessions=sessions)


@app.route("/edit", methods=["GET", "POST"])
def edit():

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        f1 = int(float(request.form["F001"]))
        f2 = int(float(request.form["F002"]))
        f3 = int(float(request.form["F003"]))
        f4 = int(float(request.form["F004"]))
        f5 = int(float(request.form["F005"]))

        if f1 + f2 + f3 + f4 + f5 != 100:
            return "Allocations must equal 100%"

        cursor.execute(
            "UPDATE model_funds SET allocation_pct=? WHERE fund_id='F001'", (f1,))
        cursor.execute(
            "UPDATE model_funds SET allocation_pct=? WHERE fund_id='F002'", (f2,))
        cursor.execute(
            "UPDATE model_funds SET allocation_pct=? WHERE fund_id='F003'", (f3,))
        cursor.execute(
            "UPDATE model_funds SET allocation_pct=? WHERE fund_id='F004'", (f4,))
        cursor.execute(
            "UPDATE model_funds SET allocation_pct=? WHERE fund_id='F005'", (f5,))

        conn.commit()

        return redirect("/")

    funds = cursor.execute("""
    SELECT fund_id, fund_name, allocation_pct
    FROM model_funds
    """).fetchall()

    conn.close()

    return render_template("edit.html", funds=funds)


if __name__ == "__main__":
    app.run(debug=True)