import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()
Faker.seed(101)
random.seed(101)

# ============================================
# DimDate — every day from 2023-01-01 to 2026-08-01
# ============================================
dim_date = []
d = date(2023, 1, 1)
end = date(2026, 8, 1)
date_id = 1
while d <= end:
    day_name = d.strftime('%A')
    is_weekend = d.weekday() >= 5
    month_name = d.strftime('%B')
    month_number = d.month
    quarter = f"Q{(d.month-1)//3 + 1}"
    year = d.year
    fiscal_year = f"FY{year}"  # assumption: fiscal year = calendar year
    # a handful of simple fixed holidays (not exhaustive, illustrative)
    is_holiday = (d.month, d.day) in [(1,1), (12,25), (12,26), (10,3)]  # New Year, Christmas, German Unity Day
    dim_date.append((date_id, d, day_name, is_weekend, is_holiday, month_name, month_number, quarter, year, fiscal_year))
    date_id += 1
    d += timedelta(days=1)

date_lookup = {row[1]: row[0] for row in dim_date}  # full_date -> date_id

# ============================================
# DimProduct
# ============================================
categories = {
    'Diagnostic Devices': ['ScanPro X200', 'ScanPro X400', 'PulseCheck Mini', 'PulseCheck Pro', 'VitalTrack Home'],
    'Surgical Instruments': ['PrecisionBlade S1', 'PrecisionBlade S2', 'ClampMaster', 'SutureKit Advanced'],
    'Consumables': ['SteriGlove Box-100', 'SteriGlove Box-200', 'IV Line Set', 'Wound Dressing Pack'],
    'Monitoring Equipment': ['CardioMonitor 3000', 'CardioMonitor 5000', 'O2 Sensor Clip', 'RemoteVitals Hub'],
    'Mobility Aids': ['FlexWalk Cane', 'FlexWalk Frame', 'GlideChair Standard', 'GlideChair Deluxe'],
}
dim_product = []
pid = 1
for cat, names in categories.items():
    for n in names:
        unit_cost = round(random.uniform(15, 900), 2)
        list_price = round(unit_cost * random.uniform(1.4, 2.2), 2)
        dim_product.append((pid, n, cat, list_price, unit_cost))
        pid += 1

# ============================================
# DimHospital
# ============================================
regions_countries = {
    'Bavaria': 'Germany', 'North Rhine-Westphalia': 'Germany', 'Hesse': 'Germany',
    'Ile-de-France': 'France', 'Auvergne-Rhone-Alpes': 'France',
    'North Holland': 'Netherlands', 'South Holland': 'Netherlands',
    'Vienna': 'Austria', 'Zurich': 'Switzerland',
}
hospital_types = ['Private Clinic', 'University Hospital', 'Public Hospital Network', 'Specialty Center']
org_sizes = ['Small', 'Medium', 'Large']

dim_hospital = []
for hid in range(1, 121):
    region = random.choice(list(regions_countries.keys()))
    country = regions_countries[region]
    customer_since = fake.date_between(start_date=date(2022,6,1), end_date=date(2026,3,1))
    dim_hospital.append((
        hid, f"{fake.city()} {random.choice(['General Hospital','Medical Center','Clinic','University Hospital'])}",
        region, country, random.choice(hospital_types), random.choice(org_sizes), customer_since
    ))

# ============================================
# DimSalesRep
# ============================================
dim_salesrep = []
for rid in range(1, 13):
    employed_since = fake.date_between(start_date='-6y', end_date='-3m')
    dim_salesrep.append((rid, fake.name(), random.choice(list(regions_countries.keys())), employed_since))

# ============================================
# FactSales — one row per product line within a sale
# ============================================
fact_sales = []
sale_id = 1
sale_line_id = 1
current = date(2023, 1, 1)

while current <= end:
    # simulate seasonal dip in Jul/Aug
    n_sales_today = random.randint(0, 4)
    if current.month in (7, 8):
        n_sales_today = random.randint(0, 2)

    for _ in range(n_sales_today):
        hospital = random.choice(dim_hospital)
        rep = random.choice(dim_salesrep)
        d_id = date_lookup[current]
        n_lines = random.randint(1, 4)
        chosen_products = random.sample(dim_product, n_lines)
        for prod in chosen_products:
            qty = random.randint(1, 25)
            discount = random.choice([0, 0, 0, 0.05, 0.1, 0.15])
            unit_price = prod[3]  # usually matches list_price, occasionally negotiated lower
            if random.random() < 0.2:
                unit_price = round(unit_price * random.uniform(0.85, 0.98), 2)
            fact_sales.append((
                sale_line_id, sale_id, d_id, prod[0], hospital[0], rep[0],
                qty, unit_price, prod[4], discount
            ))
            sale_line_id += 1
        sale_id += 1
    current += timedelta(days=1)

def sqlval(v):
    if v is None:
        return 'NULL'
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, date):
        return f"'{v.isoformat()}'"
    s = str(v).replace("'", "''")
    return f"'{s}'"

with open('/home/claude/meridian_data.sql', 'w') as f:
    f.write("-- Meridian Health Devices — Full Star Schema Dataset\n")
    f.write("-- Import via MySQL Workbench: File > Open SQL Script > run whole file\n\n")
    f.write("CREATE DATABASE IF NOT EXISTS meridian_dw;\nUSE meridian_dw;\n\n")
    f.write("DROP TABLE IF EXISTS FactSales;\nDROP TABLE IF EXISTS DimDate;\nDROP TABLE IF EXISTS DimProduct;\nDROP TABLE IF EXISTS DimHospital;\nDROP TABLE IF EXISTS DimSalesRep;\n\n")

    f.write("""CREATE TABLE DimDate (
    date_id INT PRIMARY KEY,
    full_date DATE,
    day_name VARCHAR(10),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    month_name VARCHAR(10),
    month_number INT,
    quarter VARCHAR(2),
    year INT,
    fiscal_year VARCHAR(6)
);\n\n""")

    f.write("""CREATE TABLE DimProduct (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    product_category VARCHAR(50),
    list_price DECIMAL(10,2),
    unit_cost DECIMAL(10,2)
);\n\n""")

    f.write("""CREATE TABLE DimHospital (
    hospital_id INT PRIMARY KEY,
    hospital_name VARCHAR(150),
    region VARCHAR(50),
    country VARCHAR(50),
    hospital_type VARCHAR(50),
    organization_size VARCHAR(20),
    customer_since DATE
);\n\n""")

    f.write("""CREATE TABLE DimSalesRep (
    sales_rep_id INT PRIMARY KEY,
    rep_name VARCHAR(100),
    region VARCHAR(50),
    employed_since DATE
);\n\n""")

    f.write("""CREATE TABLE FactSales (
    sale_line_id INT PRIMARY KEY,
    sale_id INT,
    date_id INT,
    product_id INT,
    hospital_id INT,
    sales_rep_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    unit_cost DECIMAL(10,2),
    discount DECIMAL(4,2),
    FOREIGN KEY (date_id) REFERENCES DimDate(date_id),
    FOREIGN KEY (product_id) REFERENCES DimProduct(product_id),
    FOREIGN KEY (hospital_id) REFERENCES DimHospital(hospital_id),
    FOREIGN KEY (sales_rep_id) REFERENCES DimSalesRep(sales_rep_id)
);\n\n""")

    f.write("INSERT INTO DimDate (date_id, full_date, day_name, is_weekend, is_holiday, month_name, month_number, quarter, year, fiscal_year) VALUES\n")
    f.write(",\n".join(f"({r[0]}, {sqlval(r[1])}, {sqlval(r[2])}, {sqlval(r[3])}, {sqlval(r[4])}, {sqlval(r[5])}, {r[6]}, {sqlval(r[7])}, {r[8]}, {sqlval(r[9])})" for r in dim_date))
    f.write(";\n\n")

    f.write("INSERT INTO DimProduct (product_id, product_name, product_category, list_price, unit_cost) VALUES\n")
    f.write(",\n".join(f"({r[0]}, {sqlval(r[1])}, {sqlval(r[2])}, {r[3]}, {r[4]})" for r in dim_product))
    f.write(";\n\n")

    f.write("INSERT INTO DimHospital (hospital_id, hospital_name, region, country, hospital_type, organization_size, customer_since) VALUES\n")
    f.write(",\n".join(f"({r[0]}, {sqlval(r[1])}, {sqlval(r[2])}, {sqlval(r[3])}, {sqlval(r[4])}, {sqlval(r[5])}, {sqlval(r[6])})" for r in dim_hospital))
    f.write(";\n\n")

    f.write("INSERT INTO DimSalesRep (sales_rep_id, rep_name, region, employed_since) VALUES\n")
    f.write(",\n".join(f"({r[0]}, {sqlval(r[1])}, {sqlval(r[2])}, {sqlval(r[3])})" for r in dim_salesrep))
    f.write(";\n\n")

    # FactSales can be huge — write in batches
    f.write("INSERT INTO FactSales (sale_line_id, sale_id, date_id, product_id, hospital_id, sales_rep_id, quantity, unit_price, unit_cost, discount) VALUES\n")
    f.write(",\n".join(f"({r[0]}, {r[1]}, {r[2]}, {r[3]}, {r[4]}, {r[5]}, {r[6]}, {r[7]}, {r[8]}, {r[9]})" for r in fact_sales))
    f.write(";\n")

print(f"DimDate: {len(dim_date)} rows")
print(f"DimProduct: {len(dim_product)} rows")
print(f"DimHospital: {len(dim_hospital)} rows")
print(f"DimSalesRep: {len(dim_salesrep)} rows")
print(f"FactSales: {len(fact_sales)} rows")
print(f"Total sale transactions: {sale_id - 1}")
