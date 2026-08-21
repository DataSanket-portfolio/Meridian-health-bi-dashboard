"""
ai_insights.py
=================
WHAT THIS SCRIPT DOES (in plain English):
1. Reads your sales data (the same CSVs you loaded into Tableau)
2. Calculates a handful of key business numbers (KPIs) — total revenue,
   profit margin, best-performing region, month-over-month growth, etc.
3. Sends those numbers to an AI model (Claude) with a prompt asking it
   to write a short, plain-English summary — the kind of paragraph a
   sales director might want at the top of a report, instead of having
   to read a dashboard themselves.
4. Saves that summary to a text file you could attach to an email,
   paste into a Slack update, or include in a report.

WHY THIS MATTERS FOR YOUR PORTFOLIO:
This demonstrates you can go beyond just building dashboards — you can
build a small automated pipeline that uses AI to turn raw numbers into
a business-readable narrative. This is a real, growing pattern in BI
work (sometimes called "natural language generation" or "NLG" for
reporting).

HOW TO RUN THIS YOURSELF LATER:
1. You need an Anthropic API key (from console.anthropic.com — separate
   from your normal claude.ai chat login). This costs a small amount
   per use (fractions of a cent for a script this size).
2. Install the two libraries this needs:
       pip install anthropic pandas --break-system-packages
3. Set your API key as an environment variable (never write it directly
   into the script — see the note below on why).
4. Run: python ai_insights.py
"""

import os
import pandas as pd
from datetime import datetime
import anthropic  # Anthropic's official Python library for calling Claude


# ============================================================
# STEP 1: Load the data
# ============================================================
# This assumes you're running the script from inside your project's
# root folder, with the CSVs sitting in /data — same files you loaded
# into Tableau. Adjust the path if your folder structure differs.

def load_data():
    fact_sales = pd.read_csv('data/FactSales.csv')
    dim_product = pd.read_csv('data/DimProduct.csv')
    dim_hospital = pd.read_csv('data/DimHospital.csv')
    dim_date = pd.read_csv('data/DimDate.csv')
    return fact_sales, dim_product, dim_hospital, dim_date


# ============================================================
# STEP 2: Calculate the KPIs
# ============================================================
# This is the SAME math you've already built in SQL and Tableau this
# week — Revenue, Profit, Profit Margin, YoY growth. We're just doing
# it in Python this time, using pandas instead of SQL or DAX/calculated
# fields. Notice the underlying LOGIC is identical; only the tool changed.

def calculate_kpis(fact_sales, dim_product, dim_hospital, dim_date):
    # Merge FactSales with its dimension tables — this is the pandas
    # equivalent of the JOINs you wrote constantly in SQL this week.
    df = fact_sales.merge(dim_product, on='product_id')
    df = df.merge(dim_hospital, on='hospital_id')
    df = df.merge(dim_date, on='date_id')

    # Revenue and Profit — same formulas as your Tableau calculated fields
    df['revenue'] = df['quantity'] * df['unit_price'] * (1 - df['discount'])
    df['profit'] = df['revenue'] - (df['quantity'] * df['unit_cost_x'])

    total_revenue = df['revenue'].sum()
    total_profit = df['profit'].sum()
    # Aggregate-first, divide-after — same "sum of ratios" trap you
    # caught and fixed in Tableau. Doing it right here too.
    profit_margin = total_profit / total_revenue

    # Top region and top category by revenue
    top_region = df.groupby('region')['revenue'].sum().idxmax()
    top_category = df.groupby('product_category')['revenue'].sum().idxmax()

    # Month-over-month growth for the most recent two months in the data
    monthly = df.groupby(['year', 'month_number'])['revenue'].sum().reset_index()
    monthly = monthly.sort_values(['year', 'month_number'])
    latest = monthly.iloc[-1]
    previous = monthly.iloc[-2]
    mom_growth_pct = ((latest['revenue'] - previous['revenue']) / previous['revenue']) * 100

    return {
        'total_revenue': round(total_revenue, 2),
        'total_profit': round(total_profit, 2),
        'profit_margin_pct': round(profit_margin * 100, 2),
        'top_region': top_region,
        'top_category': top_category,
        'latest_month': f"{int(latest['year'])}-{int(latest['month_number']):02d}",
        'mom_growth_pct': round(mom_growth_pct, 2),
    }


# ============================================================
# STEP 3: Build the prompt for the AI
# ============================================================
# This is the actual "AI integration" part. We're not asking the AI to
# invent numbers — we're handing it numbers WE already calculated and
# trust, and asking it only to turn them into readable prose. This is
# an important distinction: the AI is a writing tool here, not a
# calculator. Keeping that separation is good practice — never let an
# AI model do the actual arithmetic for a report; do the math yourself
# and let AI help communicate it.

def build_prompt(kpis):
    prompt = f"""You are a business analyst writing a short executive summary
for a MedTech company's monthly sales report. Using ONLY the numbers below,
write a concise, professional 3-4 sentence summary suitable for a sales
director. Do not invent any numbers not provided here.

Total Revenue: €{kpis['total_revenue']:,.2f}
Total Profit: €{kpis['total_profit']:,.2f}
Overall Profit Margin: {kpis['profit_margin_pct']}%
Top-Performing Region: {kpis['top_region']}
Top-Performing Product Category: {kpis['top_category']}
Latest Month ({kpis['latest_month']}) Growth vs. Previous Month: {kpis['mom_growth_pct']}%
"""
    return prompt


# ============================================================
# STEP 4: Call the AI model
# ============================================================
# WHY WE USE AN ENVIRONMENT VARIABLE FOR THE API KEY:
# An API key is like a password — anyone who has it can use YOUR AI
# credits/billing. If you typed it directly into this script and then
# pushed this file to GitHub (a PUBLIC repo), anyone in the world could
# see it and use it. Environment variables keep secrets OUT of your
# code entirely, so it's always safe to commit and share this script.

def get_ai_summary(prompt):
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "No API key found. Set it first by running this in your terminal:\n"
            "export ANTHROPIC_API_KEY='your-key-here'\n"
            "(On Windows, use: set ANTHROPIC_API_KEY=your-key-here)"
        )

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


# ============================================================
# STEP 5: Put it all together and save the result
# ============================================================

def main():
    print("Loading data...")
    fact_sales, dim_product, dim_hospital, dim_date = load_data()

    print("Calculating KPIs...")
    kpis = calculate_kpis(fact_sales, dim_product, dim_hospital, dim_date)
    print(f"KPIs calculated: {kpis}")

    print("Building prompt for AI...")
    prompt = build_prompt(kpis)

    print("Calling Claude to generate summary...")
    summary = get_ai_summary(prompt)

    # Save the output with a timestamp, so running this monthly builds
    # up a history of past summaries rather than overwriting each time.
    timestamp = datetime.now().strftime('%Y-%m-%d')
    output_path = f'docs/ai_summary_{timestamp}.md'
    with open(output_path, 'w') as f:
        f.write(f"# Meridian Health Devices — AI-Generated Sales Summary\n")
        f.write(f"*Generated: {timestamp}*\n\n")
        f.write(summary)

    print(f"\nDone! Summary saved to {output_path}")
    print(f"\n--- SUMMARY ---\n{summary}")


if __name__ == "__main__":
    main()