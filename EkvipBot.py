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

df["Days to Sell"] = (
    df["Ship Date"]
    - df["Order Date"]
).dt.days


# Filtry - 


st.sidebar.header("Filters")

segment_filter = st.sidebar.multiselect(
    "Sold to Segment",
    sorted(
        df["Sold to Segment"]
        .dropna()
        .unique()
    )
)

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

if segment_filter:
    df = df[
        df["Sold to Segment"]
        .isin(segment_filter)
    ]


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

orders_count = df["Order ID"].nunique()

margin = df["Margin"].sum()

order_delivery = (
    df.groupby("Order ID")
      .agg({
          "Order Date": "min",
          "Ship Date": "min"
      })
)

order_delivery["Days to Sell"] = (
    order_delivery["Ship Date"]
    - order_delivery["Order Date"]
).dt.days

average_days_to_sell = (
    order_delivery["Days to Sell"]
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

st.title("Summary Report: 2017:2021")

c1, c2, c3, c4, c5, c6 = st.columns([1.2,1,1,1,1,1])

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
    "Average Days to Sell",
    f"{average_days_to_sell:.2f}"
)

c5.metric(
    "Orders With Return",
    f"{return_rate:.2f}%"
)

c6.metric(
    "Orders",
    f"{orders_count:,.0f}"
)


# KPI Trends

kpi_by_year = (
    df.assign(Year=df["Ship Date"].dt.year)
      .groupby("Year")
      .agg({
          "Sales Amount": "sum",
          "Quantity": "sum",
          "Margin": "sum",
          "Days to Sell": "mean",
          "Order ID": "nunique"
      })
      .reset_index()
)

kpi_by_year.rename(
    columns={
        "Order ID": "Orders"
    },
    inplace=True
)

# pevně roky 2017–2021
all_years = pd.DataFrame(
    {"Year": [2017, 2018, 2019, 2020, 2021]}
)

kpi_by_year = (
    all_years
    .merge(
        kpi_by_year,
        on="Year",
        how="left"
    )
    .fillna(0)
)

# Return Rate po letech

returns_by_year = (
    df.assign(Year=df["Ship Date"].dt.year)
      .groupby("Year")
      .apply(
          lambda x: (
              x.groupby("Order ID")["Cancellation"]
               .apply(lambda y: (y == "Returned").any())
               .mean() * 100
          )
      )
      .reset_index(name="Return Rate")
)

kpi_by_year = (
    kpi_by_year
    .merge(
        returns_by_year,
        on="Year",
        how="left"
    )
    .fillna(0)
)

t1, t2, t3, t4, t5, t6 = st.columns(6)

def mini_trend(column, title, container):

    with container:

        fig = px.line(
            kpi_by_year,
            x="Year",
            y=column,
            markers=True
        )

        fig.update_layout(
    height=80,
    showlegend=False,
    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0
    ),
    xaxis_title=None,
    yaxis_title=None
)

        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

mini_trend("Sales Amount", "Sales", t1)
mini_trend("Quantity", "Qty", t2)
mini_trend("Margin", "Margin", t3)
mini_trend("Days to Sell", "Delivery", t4)
mini_trend("Return Rate", "Returns", t5)
mini_trend("Orders", "Orders", t6)


# Grafy


left, right = st.columns(2)

with left:


    sales_person_chart = (
        df.assign(Year=df["Ship Date"].dt.year)
          .groupby(
              ["Sales Person", "Year"]
          )["Sales Amount"]
          .sum()
          .reset_index()
    )

    fig = px.bar(
        sales_person_chart,
        x="Sales Person",
        y="Sales Amount",
        color="Year",
        barmode="group",
        title="Sales Amount by Sales Person and Year"
    )

    fig.update_layout(
        xaxis_title="Sales Person",
        yaxis_title="Sales Amount",
        legend_title="Year"
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


# Dynamic Map (USA states or countries)

st.subheader("Top 5 Locations by Sales")

top_locations = (
    df.groupby("Delivered to State")["Sales Amount"]
    .sum()
    .reset_index()
    .sort_values(
        "Sales Amount",
        ascending=False
    )
    .head(5)
)

us_state_abbrev = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR",
    "California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE",
    "Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID",
    "Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS",
    "Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
    "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
    "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
    "Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT",
    "Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV",
    "Wisconsin":"WI","Wyoming":"WY"
}

# Pokud jsou všechny hodnoty US státy
if top_locations["Delivered to State"].isin(us_state_abbrev.keys()).all():

    top_locations["Code"] = (
        top_locations["Delivered to State"]
        .map(us_state_abbrev)
    )

    fig = px.choropleth(
        top_locations,
        locations="Code",
        locationmode="USA-states",
        color="Sales Amount",
        scope="usa",
        hover_name="Delivered to State",
        title="Top 5 States by Sales"
    )

else:

    fig = px.choropleth(
        top_locations,
        locations="Delivered to State",
        locationmode="country names",
        color="Sales Amount",
        hover_name="Delivered to State",
        title="Top 5 Countries by Sales"
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
# Sales Amount Trend by Year
st.subheader("Sales Amount Trend by Year")

sales_by_year = (
    df.assign(Year=df["Ship Date"].dt.year)
      .groupby("Year")["Sales Amount"]
      .sum()
      .reset_index()
)

# zajistí zobrazení všech let 2017–2021
all_years = pd.DataFrame(
    {"Year": [2017, 2018, 2019, 2020, 2021]}
)

sales_by_year = (
    all_years
    .merge(
        sales_by_year,
        on="Year",
        how="left"
    )
    .fillna(0)
)

fig = px.line(
    sales_by_year,
    x="Year",
    y="Sales Amount",
    markers=True,
    title="Sales Amount Trend by Year"
)

fig.update_traces(
    line=dict(width=4),
    marker=dict(size=10)
)

fig.update_layout(
    xaxis=dict(
        tickmode="array",
        tickvals=[2017, 2018, 2019, 2020, 2021]
    ),
    yaxis_title="Sales Amount",
    xaxis_title="Year",
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)




# Top Selling Products

st.subheader("Top 10 Products by Sales Amount")

top_products = (
    df.groupby("Product Name")
      .agg(
          {
              
              "Sales Amount": "sum",
              
          }
      )
      .reset_index()
      .sort_values(
          "Sales Amount",
          ascending=False
      )
      .head(10)
)

fig = px.bar(
    top_products,
    x="Sales Amount",
    y="Product Name",
    orientation="h",
    title="Top 10 Products by Sales Amount"
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(
    fig,
    use_container_width=True
)


