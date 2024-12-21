from flask import Flask, render_template, request, jsonify
import pandas as pd
import re

# Load data from JSON files
final_report = pd.read_json('final_data_report.json')

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('home.html')

@app.route("/get", methods=["POST"])
def chat():
    user_input = request.form["msg"].lower().strip()
    response = get_chat_response(user_input)
    return jsonify(response)

def get_chat_response(user_input):
    if user_input == "hi":
        return [
            "Welcome! How can I help you today?",
            "Ask about financial data for companies like Microsoft, Tesla, or Apple."
        ]
    # Parse query for metric, company, and year (company and year are optional)
    match = re.search(
        r"(?:what is the|tell me|show me|give me)?\s*.*?(revenue|income|assets|liabilities|cash flow|total income)?(?:.*?\b(apple|microsoft|tesla)\b)?(?:.*?(\b\d{4}\b))?",
        user_input
    )

    if match:
        metric, company, year = match.groups()
        metric = metric.strip() if metric else None
        company = company.capitalize() if company else None
        year = int(year) if year else None

        # Debugging print statements (can be removed in production)
        print(f"Metric: {metric}, Company: {company}, Year: {year}")

        # Return filtered data
        return get_filtered_data(metric, company, year)
    
    return ["I couldn't understand your query. Please specify a metric (e.g., revenue, income) or a company name."]

def get_filtered_data(metric, company, year):
    # Map user-friendly terms to column names
    metric_map = {
        "revenue": "Total Revenue",
        "income": "Net Income",
        "assets": "Total Assets",
        "liabilities": "Total Liabilities",
        "cash flow": "Cash Flow from Operating Activities"
    }

    # Handle "total income" as a special case
    if metric == "total income":
        return calculate_total_income(company)

    # Validate metric
    column_name = metric_map.get(metric)
    if not column_name:
        return [f"Please specify a valid metric (e.g., revenue, income, assets, liabilities, cash flow, total income)."]

    # Filter data based on the company and year
    filtered_data = final_report
    if company:
        filtered_data = filtered_data[filtered_data["Company"].str.lower() == company.lower()]
    if year:
        filtered_data = filtered_data[filtered_data["Year"] == year]
    
    # If no data matches the filter, respond accordingly
    if filtered_data.empty:
        if company and year:
            return [f"No data found for {company} in {year}."]
        elif company:
            return [f"No data found for {company}."]
        elif year:
            return [f"No data found for the year {year}."]
        else:
            return ["No matching data found."]

    # Generate response
    results = [
        f"{metric.capitalize()} of {row['Company']} in {row['Year']}: ${row[column_name]:,.2f} million"
        for _, row in filtered_data.iterrows()
    ]

    return results

def calculate_total_income(company):
    # Ensure the company is provided
    if not company:
        return ["Please specify a company to calculate total income."]
    
    # Filter data for the company
    company_data = final_report[final_report["Company"].str.lower() == company.lower()]
    if company_data.empty:
        return [f"No data found for {company}."]

    # Calculate total income
    total_income = company_data["Net Income"].sum()
    return [f"Total income of {company}: ${total_income:,.2f} million."]

if __name__ == '__main__':
    app.run(debug=True)
