import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide"
)


# Načtení excelu


FILE  = "Ekvip_Case_Data.xlsx"

orders = pd.read_excel(FILE, sheet_name="Orders")
customers = pd.read_excel(FILE, sheet_name="Customer Master Data")
products = pd.read_excel(FILE, sheet_name="Product Master Data")
sales_person = pd.read_excel(FILE, sheet_name="Sales Person List")


# Vytvoření relací

df = orders.merge(
    customers,
    on="Sold to Customer ID",
    how="left"
)

df = df.merge(
    products,
    on="Product ID",
    how="left"
)

df = df.merge(
    sales_person,
    left_on="Delivered to Region",
    right_on="Region",
    how="left"
)


# DATOVÉ TYPY


df["Order Date"] = pd.to_datetime(
    df["Order Date"],
    dayfirst=True,
    errors="coerce"
)

df["Ship Date"] = pd.to_datetime(
    df["Ship Date"],
    dayfirst=True,
    errors="coerce"
)


# Výpočty - sloupec margin, Delivery Days, 


df["Margin"] = (
    df["Sales Amount"]
    - df["Production Cost Amount"]
)

df["Delivery Days"] = (
    df["Ship Date"]
    - df["Order Date"]
).dt.days


# Filtry - 


st.sidebar.header("Filters")

salesperson_filter = st.sidebar.multiselect(
    "Sales Person",
    sorted(
        df["Sales Person"]
        .dropna()
        .unique()
    )
)

customer_filter = st.sidebar.multiselect(
    "Customer",
    sorted(
        df["Sold to Customer Name"]
        .dropna()
        .unique()
    )
)

category_filter = st.sidebar.multiselect(
    "Category",
    sorted(
        df["Category"]
        .dropna()
        .unique()
    )
)

region_filter = st.sidebar.multiselect(
    "Region",
    sorted(
        df["Delivered to Region"]
        .dropna()
        .unique()
    )
)

state_filter = st.sidebar.multiselect(
    "State",
    sorted(
        df["Delivered to State"]
        .dropna()
        .unique()
    )
)


# Aplikace Filtrů


if salesperson_filter:
    df = df[
        df["Sales Person"]
        .isin(salesperson_filter)
    ]

if customer_filter:
    df = df[
        df["Sold to Customer Name"]
        .isin(customer_filter)
    ]

if category_filter:
    df = df[
        df["Category"]
        .isin(category_filter)
    ]

if region_filter:
    df = df[
        df["Delivered to Region"]
        .isin(region_filter)
    ]

if state_filter:
    df = df[
        df["Delivered to State"]
        .isin(state_filter)
    ]


# KPI - výkonnostní ukazatele

sales_amount = df["Sales Amount"].sum()

quantity = df["Quantity"].sum()

margin = df["Margin"].sum()

average_delivery_days = (
    df["Delivery Days"]
    .mean()
)

# RETURN RATE
# Objednávka je vrácená pokud má alespoň jednu položku Returned

total_orders = df["Order ID"].nunique()

returned_orders = (
    df.groupby("Order ID")["Cancellation"]
      .apply(lambda x: (x == "Returned").any())
      .sum()
)

return_rate = (
    returned_orders / total_orders * 100
    if total_orders > 0
    else 0
)

# KPI KARTY

st.title("Summary Dashboard")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Sales Amount",
    f"${sales_amount:,.0f}"
)

c2.metric(
    "Quantity",
    f"{quantity:,.0f}"
)

c3.metric(
    "Margin",
    f"${margin:,.0f}"
)

c4.metric(
    "Average Delivery Days",
    f"{average_delivery_days:.2f}"
)

c5.metric(
    "Orders With Return",
    f"{return_rate:.2f}%"
)



# Grafy


left, right = st.columns(2)

with left:

    sales_person_chart = (
        df.groupby("Sales Person")["Sales Amount"]
        .sum()
        .reset_index()
        .sort_values(
            "Sales Amount",
            ascending=False
        )
    )

    fig = px.bar(
        sales_person_chart,
        x="Sales Person",
        y="Sales Amount",
        title="Sales Amount by Sales Person"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

    goods = (
        df.groupby(
            ["Category", "Sub-Category"]
        )["Sales Amount"]
        .sum()
        .reset_index()
    )

    fig = px.sunburst(
        goods,
        path=[
            "Category",
            "Sub-Category"
        ],
        values="Sales Amount",
        title="Sales by Category"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# Top 10 customers

customers_chart = (
    df.groupby(
        [
            "Sold to Customer Name",
            "Sold to Segment"
        ]
    )["Sales Amount"]
    .sum()
    .reset_index()
    .sort_values(
        "Sales Amount",
        ascending=False
    )
    .head(10)
)

fig = px.bar(
    customers_chart,
    x="Sales Amount",
    y="Sold to Customer Name",
    color="Sold to Segment",
    orientation="h",
    title="Top 10 Customers by Segment",
    hover_data=["Sold to Segment"]
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.dataframe(
    customers_chart,
    use_container_width=True
)

# States chart


state_data = (
    df.groupby(
        "Delivered to State"
    )["Sales Amount"]
    .sum()
    .reset_index()
)

fig = px.treemap(
    state_data,
    path=["Delivered to State"],
    values="Sales Amount",
    title="Sales Amount by State"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# Average discount

discount = (
    df.groupby("Category")["Discount %"]
    .mean()
    .reset_index()
    .sort_values(
        "Discount %",
        ascending=False
    )
)

st.subheader(
    "Average Discount % by Category"
)

st.dataframe(
    discount,
    use_container_width=True
)


# DISCOUNT OVERVIEW BY PRODUCT Name

st.subheader(
    "Discount Overview by Product"
)

discount_products = (
    df.groupby(
        [
            "Product Name",
            "Category",
            "Sub-Category"
        ]
    )
    .agg(
        {
            "Discount %": "mean",
            "Sales Amount": "sum",
            "Margin": "sum"
        }
    )
    .reset_index()
    .sort_values(
        "Discount %",
        ascending=False
    )
)

st.dataframe(
    discount_products,
    use_container_width=True
)


# Detailní data

st.subheader("Order Details")

st.dataframe(
    df,
    use_container_width=True
)
