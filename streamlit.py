import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pydeck as pdk
import json
import sqlite3

conn = sqlite3.connect("brickview_realestate.db")
cursor = conn.cursor()

@st.cache_data
def get_table_names():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [t[0] for t in cursor.fetchall()]
def get_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]
def get_ids(table_name, id_column):
    cursor.execute(f"SELECT {id_column} FROM {table_name}")
    return [str(row[0]) for row in cursor.fetchall()]

df = pd.read_json(r"C:\AIML\Projects\agents_20k.json")
sales=pd.read_csv(r"C:\AIML\Projects\sales_20k.csv")
list=pd.read_json(r"C:\AIML\Projects\listings_20k.json")
agents_20=pd.read_json(r"C:\AIML\Projects\agents_20k.json")
agents_enhanced=pd.read_json(r"C:\AIML\Projects\agents_enhanced_20k.json")



st.set_page_config(page_title="Brickview Project")

st.sidebar.title("Navigation")
page=st.sidebar.radio("GO To",['Project Introduction','View Tables','Filters','CRUD Operations','Visualisations','SQL Queries','Creator Info'])


if page == "Project Introduction":
    st.title("🏠 BrickView: Real Estate Analytics")
    st.subheader("📊 A Streamlit App for Exploring Real Estate Trends")
    st.write("""
    This project analyzes real estate data from multiple cities using an SQLite database.
    It enables users to explore property listings, sales performance, and agent activity
    through interactive filters, visualizations, and SQL-based insights.

    **Features:**
    - View and filter property listings by city, property type, and price range.
    - Perform CRUD (Create, Read, Update, Delete) operations on listings.
    - Run predefined SQL queries to uncover market insights.
    - Visualize trends such as monthly sales, property distribution, and pricing patterns.

    **Database Used:** `brickview_realestate.db`
    """)

elif page == 'View Tables':
    table_names = get_table_names()
    selected_table = st.selectbox("Choose Table", table_names)
    A=cursor.execute(f"SELECT * FROM {selected_table} ORDER BY ROWID ASC LIMIT 500")
    st.subheader(f"Table: {selected_table}")
    st.dataframe(A, use_container_width=True)

elif page == "Filters":

    st.header("🔎 Dynamic Table Filters")

    # 1️⃣ Select table
    table_names = get_table_names()
    selected_table = st.selectbox("Choose Table", table_names)

    # 2️⃣ Get columns
    columns = get_columns(selected_table)

    filters = {}
    query = f"SELECT * FROM {selected_table} WHERE 1=1"
    params = []

    st.subheader("Choose Filters")

    # 3️⃣ Create dropdowns dynamically
    for col in columns:

        values = pd.read_sql(
            f"SELECT DISTINCT {col} FROM {selected_table}",
            conn
        )[col].dropna().tolist()

        # Only create dropdown if column has reasonable unique values
        if 1 < len(values) > 0:

            selected_vals = st.multiselect(f"{col}", values)

            if selected_vals:
                placeholders = ",".join(["?"] * len(selected_vals))
                query += f" AND {col} IN ({placeholders})"
                params.extend(selected_vals)

    # 4️⃣ Run query only if at least one filter chosen
    if params:
        result = pd.read_sql(query, conn, params=params)

        st.subheader("Filtered Results")
        st.dataframe(result, use_container_width=True)
    else:
        st.info("Select at least one filter to see results.")


elif page == "CRUD Operations":

    p=st.radio("Select a Table",['view','Add','Update','Delete'])
    table_names = get_table_names()

    selected_table = st.selectbox("Choose Table", table_names)
    if p=="view":
        
        A=cursor.execute(f"SELECT * FROM {selected_table} ORDER BY ROWID ASC LIMIT 500")
        st.subheader(f"Table: {selected_table}")
        st.dataframe(A, use_container_width=True)
        # Get table names

    elif p=="Add":
        st.subheader(f"➕ Add New Record to {selected_table}")
        columns = get_columns(selected_table)

        data = {}

        for col in columns:
            data[col] = st.text_input(col)

        if st.button("Insert Record"):

            cols = ",".join(columns)
            placeholders = ",".join(["?"] * len(columns))

            query = f"""
            INSERT INTO {selected_table}
            ({cols})
            VALUES ({placeholders})
            """

            cursor.execute(query, tuple(data.values()))
            conn.commit()

            st.success("Record Added Successfully ✅")

    elif p == "Update":

        st.subheader(f"✏️ Update Record in {selected_table}")

        columns = get_columns(selected_table)

        id_column = st.selectbox("Select ID Column", columns)

        record_ids = get_ids(selected_table, id_column)
        selected_id = st.selectbox("Select Record ID", record_ids)

        update_column = st.selectbox("Select Column to Update", columns)

        new_value = st.text_input("Enter New Value")

        if st.button("Update Record"):

            if new_value == "":
                st.warning("Please enter a value")
            else:
                query = f"""
                UPDATE {selected_table}
                SET {update_column} = ?
                WHERE {id_column} = ?
                """

                cursor.execute(query, (new_value, selected_id))
                conn.commit()

                st.success("Record Updated Successfully ✅")

    elif p == "Delete":

                st.subheader(f"🗑 Delete Record from {selected_table}")

                columns = get_columns(selected_table)

                id_column = st.selectbox("Select ID Column", columns)

                record_ids = get_ids(selected_table, id_column)

                selected_id = st.selectbox("Select Record ID", record_ids)

                st.warning("⚠ This action cannot be undone!")

                if st.button("Delete Record"):

                    query = f"""
                    DELETE FROM {selected_table}
                    WHERE {id_column} = ?
                    """

                    cursor.execute(query, (selected_id,))
                    conn.commit()

                    st.success("Record Deleted Successfully ✅") 

elif page == "Visualisations":
    
    type_counts = list["Property_Type"].value_counts()

    fig, ax = plt.subplots()
    ax.pie(type_counts, labels=type_counts.index, autopct="%1.1f%%")
    ax.set_title("Distribution of Property Types")

    st.pyplot(fig)

# Bar Chart
    city_counts = list["City"].value_counts().reset_index()
    city_counts.columns = ["City", "Count of City"]
    st.bar_chart(city_counts.set_index("City"))

# Line Chart
    list["Date_Listed"] = pd.to_datetime(list["Date_Listed"])
    sales["Date_Sold"] = pd.to_datetime(sales["Date_Sold"])

# Create month column
    list["Month"] = list["Date_Listed"].dt.to_period("M")
    sales["Month"] = sales["Date_Sold"].dt.to_period("M")

# Count per month
    monthly_listings = list.groupby("Month").size()
    monthly_sales = sales.groupby("Month").size()

# Plot

    fig, ax = plt.subplots()
    ax.plot(monthly_listings.index.astype(str), monthly_listings.values, label="Listings")
    ax.plot(monthly_sales.index.astype(str), monthly_sales.values, label="Sales")
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.set_title("Monthly Listings and Sales Trend")
    plt.xticks(rotation=45)
    ax.legend()

    st.pyplot(fig)

# Map Chart
    city_centers = {
        "New York": [40.7128, -74.0060],
        "Los Angeles": [34.0522, -118.2437],
        "Houston": [29.7604, -95.3698],
        "Phoenix": [33.4484, -112.0740],
        "Chicago": [41.8781, -87.6298]
    }
    list["Latitude"] = list["City"].map(lambda x: city_centers.get(x, [None,None])[0])
    list["Longitude"] = list["City"].map(lambda x: city_centers.get(x, [None,None])[1])


    list = list.dropna(subset=["Latitude", "Longitude"])

    st.title("Real Estate Listings Map")

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=list,
        get_position=["Longitude", "Latitude"],
        get_radius=20000,
        get_fill_color=[255, 0, 0, 160],
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=list["Latitude"].mean(),
        longitude=list["Longitude"].mean(),
        zoom=4
    )

    tooltip = {
        "text": "City: {city}\nType: {property_type}\nPrice: ${Price}"
    }

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    ))       
  
elif page == "SQL Queries":
    questions = [
        "1.What is the average listing price by city?",
        "2.What is the average price per square foot by property type?",
        "3.How does furnishing status impact property prices?",
        "4.Do properties closer to metro stations command higher prices?",
        "5.Are rented properties priced differently from non-rented ones?",
        "6.How do bedrooms and bathrooms affect pricing?",
        "7.Do properties with parking and power backup sell at higher prices?",
        "8.How does year built influence listing price?",
        "9.Which cities have the highest median property prices?",
        "10.How are properties distributed across price buckets?",
        "11.What is the average days on market by city?",
        "12.Which property types sell the fastest?",
        "13.What percentage of properties are sold above listing price?",
        "14.What is the sale-to-list price ratio by city?",
        "15.Which listings took more than 90 days to sell?",
        "16.How does metro distance affect time on market?",
        "17.What is the monthly sales trend?",
        "18.Which properties are currently unsold?",
        "19.Which agents have closed the most sales?",
        "20.Who are the top agents by total sales revenue?",
        "21.Which agents close deals fastest?",
        "22.Does experience correlate with deals closed?",
        "23.Do agents with higher ratings close deals faster?",
        "24.What is the average commission earned by each agent?",
        "25.Which agents currently have the most active listings?",
        "26.What percentage of buyers are investors vs end users?",
        "27.Which cities have the highest loan uptake rate?",
        "28.What is the average loan amount by buyer type?",
        "29.Which payment mode is most commonly used?",
        "30.Do loan-backed purchases take longer to close?"
    ]
    selected = st.selectbox("Select a Question", questions)

    if selected == "1.What is the average listing price by city?":
        query="""
        SELECT city,AVG(price) AS avg_price from listings group by city;
    """
    elif selected == "2.What is the average price per square foot by property type?":
        query="""
    select property_type,AVG(price/sqft) AS Avg_price_per_sqft from listings group by property_type order by Avg_price_per_sqft;
    """
    elif selected == "3.How does furnishing status impact property prices?":
        query="""
    select p.furnishing_status,AVG(l.price) as avg_price from listings l INNER JOIN property_attributes p ON l.listing_id = p.listing_id group by p.furnishing_status order by avg_price;
    """
    elif selected == "4.Do properties closer to metro stations command higher prices?":
        query="""
    select ROUND(p.metro_distance_km) AS metro_distance,AVG(l.price) AS price from listings l INNER JOIN property_attributes p ON l.listing_id=p.listing_id  group by ROUND(p.metro_distance_km) order by metro_distance;
    """
    elif selected == "5.Are rented properties priced differently from non-rented ones?":
        query = """
    select p.is_rented,AVG(l.price)as price from listings l INNER JOIN property_attributes p ON l.listing_id=p.listing_id group by p.is_rented
    """
    elif selected == "6.How do bedrooms and bathrooms affect pricing?":
        query = """
    select p.bedrooms,p.bathrooms,avg(price) as price from listings l INNER JOIN property_attributes p on l.listing_id=p.listing_id group by p.bedrooms,p.bathrooms order by p.bedrooms,p.bathrooms
    """
    elif selected == "7.Do properties with parking and power backup sell at higher prices?":
        query = """
    select p.parking_available,p.power_backup,AVG(l.price) as price from listings l INNER JOIN property_attributes p on l.listing_id=p.listing_id group by p.parking_available,p.power_backup order by p.parking_available,p.power_backup
    """
    elif selected == "8.How does year built influence listing price?":
        query = """
    select p.year_built	,AVG(l.price) as price from listings l inner join property_attributes p on l.listing_id=p.listing_id group by p.year_built
    """
    elif selected == "9.Which cities have the highest median property prices?":
        query = """
    select city,round(avg(price)) as price from listings group by city order by price
    """
    elif selected == "10.How are properties distributed across price buckets?":
        query = """"
    
    """
    elif selected == "11.What is the average days on market by city?":
        query="""
    select l.city,avg(Days_on_Market) as days from sales s inner join listings l on s.Listing_ID=l.Listing_ID group by l.city
    """
    elif selected == "12.Which property types sell the fastest?":
        query="""
    select l.property_type,round(avg(s.Days_on_Market)) as days from sales s inner join listings l on s.Listing_ID	= l.Listing_ID group by l.property_type
    """
    elif selected == "13.What percentage of properties are sold above listing price?":
        query="""
    SELECT 
        (COUNT(*) * 100.0 / 
            (SELECT COUNT(*) 
            FROM sales s
            JOIN listings l 
            ON s.listing_id = l.listing_id)
        ) AS percentage_higher_sales
    FROM sales s
    JOIN listings l 
    ON s.listing_id = l.listing_id
    WHERE s.sale_price > l.price
    """
    elif selected == "14.What is the sale-to-list price ratio by city?":
        query="""

    """
    elif selected == "15.Which listings took more than 90 days to sell?":
        query="""
    select l.Listing_ID,l.City,l.Property_Type,l.Price,s.Sale_Price,s.Days_on_Market from sales s inner join listings l on s.Listing_ID=l.Listing_ID where s.Days_on_Market>90 order by s.Days_on_Market
    """
    elif selected=="16.How does metro distance affect time on market?":
        query="""
    select round(avg(Days_on_Market)) as days
    ,round(metro_distance_km) as metro_distance from sales s inner join property_attributes p on s.listing_id = p.listing_id group by metro_distance
    """
    elif selected=="17.What is the monthly sales trend?":
        query="""
    
    """
    elif selected=="18.Which properties are currently unsold?":
        query="""

    """
    elif selected=="19.Which agents have closed the most sales?":
        query="""
    select Agent_id,deals_closed from agents_enhanced
    """
    elif selected=="20.Who are the top agents by total sales revenue?":
        query="""
    select agent_id,avg(price) from listings group by Agent_id
    """
    elif selected=="21.Which agents close deals fastest?":
        query="""
    select agent_id,avg_closing_days from agents_enhanced order by avg_closing_days
    """
    elif selected=="22.Does experience correlate with deals closed?":
        query="""
    select experience_years,round(avg(deals_closed)) as deals from agents_enhanced group by experience_years
    """
    elif selected=="23.Do agents with higher ratings close deals faster?":
        query="""
    select rating,round(avg(deals_closed)) as deals from agents_enhanced group by rating
    """
    elif selected=="24.What is the average commission earned by each agent?":
        query="""
    select l.Agent_Id,Avg(l.price*(a.commission_rate)/100) from agents_enhanced a inner join listings l on a.Agent_Id = l.Agent_Id group by l.Agent_Id
    """
    elif selected=="25.Which agents currently have the most active listings?":
        query="""
    select Agent_Id,count(*) as active_listings from listings group by Agent_Id order by active_listings desc
    """
    elif selected=="26.What percentage of buyers are investors vs end users?":
        query="""

    """
    elif selected=="27.Which cities have the highest loan uptake rate?":
        query="""
    select l.City,AVG(b.loan_taken ) AS loan_rate FROM buyers b JOIN listings l ON b.sale_id = l.Listing_ID GROUP BY l.City order by loan_rate
    """
    elif selected=="28.What is the average loan amount by buyer type?":
        query="""
    select buyer_type,round(avg(loan_amount)) as amount from buyers WHERE loan_taken = 1 group by buyer_type
    """
    elif selected=="29.Which payment mode is most commonly used?":
        query="""
    select payment_mode,count(*) as commonly_used from buyers group by payment_mode
    """
    elif selected=="30Do loan-backed purchases take longer to close?":
        query="""
    select b.loan_taken,round(avg(s.Days_on_Market)) as days from buyers b inner join sales s on b.sale_id=s.Listing_ID GROUP BY b.Loan_Taken;
    """
    result = pd.read_sql(query, conn)
    st.dataframe(result)

elif page == "Creator Info":
    st.title("👩‍💻 Creator of this Project")
    st.write("""
    **Developed by:** Vasantha leela 
             
    **Skills:** Python, SQL, Data Analysis,Streamlit, Pandas   
    """)