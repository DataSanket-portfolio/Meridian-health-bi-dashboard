"""
Meridian Health Devices — synthetic data generator
Matches the star schema in docs/schema.md:
  FactSales, DimDate, DimProduct, DimHospital, DimSalesRep

Run from your project's ROOT folder (not inside /scripts):
    python3 scripts/generate_meridian_data.py

Output: CSV files written to data/ (FactSales.csv, DimDate.csv,
DimProduct.csv, DimHospital.csv, DimSalesRep.csv)

NOTE ON RANDOMNESS: this script deliberately has NO fixed random seed.
Every time it runs, it generates genuinely different numbers. That's
intentional — it's what makes the Day 6 GitHub Actions "weekly refresh"
workflow meaningful. A seeded script would produce identical data every
run, which wouldn't demonstrate anything actually refreshing.
"""

import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("de_DE")  # German-flavored names/addresses to match the MedTech/DACH target market
# No Faker.seed() / random.seed() on purpose — see note above.

# ============================================================
# DimDate — one row per calendar day, last 2 years through today
# ============================================================
START_DATE = date.today() - timedelta(days=730)
END_DATE = date.today()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

GERMAN_HOLIDAYS = {(1, 1), (5, 1), (10, 3), (12, 25), (12, 26)}

dim_date = []
d = START_DATE
date_id = 1
date_id_lookup = {}
while d <= END_DATE:
    quarter = f"Q{((d.month - 1) // 3) + 1}"
    dim_date.append({
        "date_id": date_id,
        "full_date": d.isoformat(),
        "day_name": DAY_NAMES[d.weekday()],
        "is_weekend": d.weekday() >= 5,
        "is_holiday": (d.month, d.day) in GERMAN_HOLIDAYS,
        "month_name": MONTH_NAMES[d.month - 1],
        "month_number": d.month,
        "quarter": quarter,
        "year": d.year,
        "fiscal_year": f"FY{d.year}",
    })
    date_id_lookup[d] = date_id
    date_id += 1
    d += timedelta(days=1)

# ============================================================
# DimProduct — medical device / consumable catalog
# ============================================================
PRODUCT_CATALOG = [
    ("ScanPro X200", "Imaging", 42000.00, 28500.00),
    ("ScanPro X200 Mini", "Imaging", 24500.00, 16800.00),
    ("UltraView C3", "Imaging", 18900.00, 12200.00),
    ("VitalTrack Monitor M5", "Monitoring Equipment", 3200.00, 1950.00),
    ("VitalTrack Monitor M5 Pro", "Monitoring Equipment", 4600.00, 2900.00),
    ("PulseGuard Wearable", "Monitoring Equipment", 850.00, 480.00),
    ("RapidDx Analyzer", "Diagnostics", 15600.00, 10100.00),
    ("RapidDx Test Cartridge (Box of 50)", "Consumables", 340.00, 190.00),
    ("SteriSeal Surgical Kit", "Consumables", 210.00, 130.00),
    ("SteriSeal Surgical Kit Pro", "Consumables", 285.00, 175.00),
    ("InfuseFlow Pump", "Monitoring Equipment", 5400.00, 3600.00),
    ("InfuseFlow Tubing Set (Pack of 20)", "Consumables", 95.00, 52.00),
    ("BioSample Centrifuge", "Diagnostics", 9800.00, 6300.00),
    ("BioSample Test Strips (Box of 100)", "Consumables", 120.00, 68.00),
    ("NeoCare Incubator", "Monitoring Equipment", 22500.00, 15400.00),
    ("MobiScan Handheld Ultrasound", "Imaging", 11200.00, 7400.00),
    ("ClearView Endoscope", "Diagnostics", 13800.00, 9200.00),
    ("GlucoTrack Sensor Pack (Box of 30)", "Consumables", 180.00, 98.00),
]

dim_product = []
for i, (name, cat, list_price, unit_cost) in enumerate(PRODUCT_CATALOG, start=1):
    dim_product.append({
        "product_id": i,
        "product_name": name,
        "product_category": cat,
        "list_price": list_price,
        "unit_cost": unit_cost,
    })

# ============================================================
# DimHospital — customer hospitals across German-speaking regions
# ============================================================
REGIONS = {
    "Bavaria": ["Munich", "Nuremberg", "Augsburg", "Regensburg"],
    "North Rhine-Westphalia": ["Cologne", "Dusseldorf", "Dortmund", "Essen"],
    "Baden-Wurttemberg": ["Stuttgart", "Mannheim", "Freiburg"],
    "Berlin": ["Berlin"],
    "Hesse": ["Frankfurt", "Wiesbaden"],
}
HOSPITAL_TYPES = ["General Hospital", "University Hospital", "Specialty Clinic", "Private Practice Group"]
ORG_SIZES = ["Small", "Medium", "Large"]
HOSPITAL_SUFFIXES = ["Klinikum", "Krankenhaus", "Medical Center", "Universitatsklinik", "Klinik"]

dim_hospital = []
hospital_id = 1
for region, cities in REGIONS.items():
    n_hospitals = random.randint(6, 9)
    for _ in range(n_hospitals):
        city = random.choice(cities)
        suffix = random.choice(HOSPITAL_SUFFIXES)
        name = f"{city} {suffix}"
        org_size = random.choices(ORG_SIZES, weights=[0.35, 0.4, 0.25])[0]
        htype = random.choices(HOSPITAL_TYPES, weights=[0.4, 0.15, 0.3, 0.15])[0]
        customer_since = fake.date_between(start_date="-6y", end_date="-3m")
        dim_hospital.append({
            "hospital_id": hospital_id,
            "hospital_name": name,
            "region": region,
            "country": "Germany",
            "hospital_type": htype,
            "organization_size": org_size,
            "customer_since": customer_since.isoformat(),
        })
        hospital_id += 1

# ============================================================
# DimSalesRep
# ============================================================
dim_sales_rep = []
sales_rep_id = 1
for region in REGIONS.keys():
    n_reps = random.randint(2, 3)
    for _ in range(n_reps):
        dim_sales_rep.append({
            "sales_rep_id": sales_rep_id,
            "rep_name": fake.name(),
            "region": region,
            "employed_since": fake.date_between(start_date="-5y", end_date="-6m").isoformat(),
        })
        sales_rep_id += 1

hospitals_by_region = {}
for h in dim_hospital:
    hospitals_by_region.setdefault(h["region"], []).append(h["hospital_id"])

reps_by_region = {}
for r in dim_sales_rep:
    reps_by_region.setdefault(r["region"], []).append(r["sales_rep_id"])

# ============================================================
# FactSales — grain: one row per product-line within a transaction
# ============================================================
fact_sales = []
sale_line_id = 1
sale_id = 1


def month_seasonality_weight(month_number):
    if month_number in (10, 11, 12):
        return 1.6
    if month_number == 8:
        return 0.5
    return 1.0


ANOMALY_SPIKE_START = date(END_DATE.year, END_DATE.month, 1) - timedelta(days=200)
ANOMALY_SPIKE_END = ANOMALY_SPIKE_START + timedelta(days=10)
ANOMALY_DIP_START = date(END_DATE.year, END_DATE.month, 1) - timedelta(days=430)
ANOMALY_DIP_END = ANOMALY_DIP_START + timedelta(days=14)

weighted_days = []
for row in dim_date:
    d_obj = date.fromisoformat(row["full_date"])
    if row["is_weekend"]:
        continue
    weight = month_seasonality_weight(row["month_number"])
    if ANOMALY_SPIKE_START <= d_obj <= ANOMALY_SPIKE_END:
        weight *= 4.0
    if ANOMALY_DIP_START <= d_obj <= ANOMALY_DIP_END:
        weight *= 0.15
    weighted_days.extend([row["full_date"]] * int(weight * 10))

TARGET_TRANSACTIONS = 2200

for _ in range(TARGET_TRANSACTIONS):
    full_date = random.choice(weighted_days)
    date_id = date_id_lookup[date.fromisoformat(full_date)]

    region = random.choice(list(REGIONS.keys()))
    hospital_id = random.choice(hospitals_by_region[region])
    sales_rep_id = random.choice(reps_by_region[region])

    n_line_items = random.choices([1, 2, 3, 4], weights=[0.45, 0.3, 0.15, 0.1])[0]
    products_in_this_sale = random.sample(dim_product, k=min(n_line_items, len(dim_product)))

    for product in products_in_this_sale:
        quantity = random.choices([1, 2, 3, 5, 10, 25, 50], weights=[0.25, 0.2, 0.15, 0.15, 0.1, 0.1, 0.05])[0]
        if product["product_category"] != "Consumables":
            quantity = 1 if random.random() < 0.85 else 2

        discount = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[0.4, 0.25, 0.2, 0.1, 0.05])[0]
        unit_price = round(product["list_price"] * (1 - discount), 2)

        fact_sales.append({
            "sale_line_id": sale_line_id,
            "sale_id": sale_id,
            "date_id": date_id,
            "product_id": product["product_id"],
            "hospital_id": hospital_id,
            "sales_rep_id": sales_rep_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "unit_cost": product["unit_cost"],
            "discount": discount,
        })
        sale_line_id += 1

    sale_id += 1

# ---- realistic messiness ----
for row in fact_sales:
    if random.random() < 0.02:
        row["discount"] = ""

for row in dim_hospital:
    if random.random() < 0.01:
        row["organization_size"] = ""

# ============================================================
# Write CSVs — PascalCase filenames to match what's already in your
# repo and what ai_insights.py expects (data/FactSales.csv, etc.)
# ============================================================
import csv
import os

OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)


def write_csv(filename, rows, fieldnames):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} rows -> {path}")


write_csv("DimDate.csv", dim_date, list(dim_date[0].keys()))
write_csv("DimProduct.csv", dim_product, list(dim_product[0].keys()))
write_csv("DimHospital.csv", dim_hospital, list(dim_hospital[0].keys()))
write_csv("DimSalesRep.csv", dim_sales_rep, list(dim_sales_rep[0].keys()))
write_csv("FactSales.csv", fact_sales, list(fact_sales[0].keys()))

print("\nDone. All 5 CSVs match the schema in docs/schema.md.")
