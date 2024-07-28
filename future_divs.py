import pandas as pd


def calculate_future_income(age_range, average_yield, starting_investment, monthly_investment, capital_appreciation_percent, tax_rate, expense_ratio):
    """Calculates the monthly income from dividends in the future"""

    data = pd.DataFrame()
    data["Date"] = pd.date_range(start=pd.Timestamp.today().date(), periods=12 * (age_range[1] - age_range[0]), freq="ME")

    annual_income = starting_investment * average_yield / 100
    monthly_income = annual_income / 12
    weekly_income = annual_income / 52
    capital_gains_loss = (capital_appreciation_percent - (expense_ratio * 100)) / 12 

    total_monthly_income = monthly_income - (monthly_income * tax_rate / 100)

    # save first month of data off. then loop through the rest of the months
    data.loc[0, "Capital"] = starting_investment
    data.loc[0, "Total Contributions"] = starting_investment
    data.loc[0, "Weekly Income"] = weekly_income
    data.loc[0, "Monthly Income"] = monthly_income
    data.loc[0, "Annual Income"] = annual_income
    data.loc[0, "Capital Appreciation"] = capital_gains_loss * starting_investment / 100
    data.loc[0, "Taxes"] = -1 * ((monthly_income * tax_rate) / 100)
    data.loc[0, "Total Monthly Income"] = total_monthly_income

    for i in range(1, len(data)):
        capital = data.loc[i - 1, "Capital"] + monthly_investment + data.loc[i - 1, "Monthly Income"] + data.loc[i - 1, "Capital Appreciation"] + data.loc[i - 1, "Taxes"]

        annual_income = capital * average_yield / 100
        monthly_income = annual_income / 12
        weekly_income = annual_income / 52
        total_monthly_income = monthly_income - (monthly_income * tax_rate / 100)
        capital_gains_loss = ((capital_appreciation_percent - expense_ratio * 100) / 12)
        taxes = -1 * (monthly_income * tax_rate / 100)

        data.loc[i, "Capital"] = capital
        data.loc[i, "Total Contributions"] = data.loc[i - 1, "Total Contributions"] + monthly_investment
        data.loc[i, "Weekly Income"] = weekly_income
        data.loc[i, "Monthly Income"] = monthly_income
        data.loc[i, "Annual Income"] = annual_income
        data.loc[i, "Capital Appreciation"] = capital_gains_loss * capital / 100
        data.loc[i, "Taxes"] = taxes
        data.loc[i, "Total Monthly Income"] = total_monthly_income
    
    # round the data to 2 decimal places
    data = data.round(2)


    return data


if __name__ == "__main__":
    print(calculate_future_income(23, 90.28, 1000, 833.33, 38.62, 22, 1.01).head(150))