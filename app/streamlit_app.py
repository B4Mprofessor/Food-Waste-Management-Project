import streamlit as st
import sqlite3
import pandas as pd
import os


# ------------------------
# Connect to DB
# ------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, '..', 'db', 'food_waste.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ------------------------
# App Title
# ------------------------
st.title("\U0001F371 Local Food Waste Management System")
st.markdown("Helping redistribute surplus food to reduce waste.")

# ------------------------
# Sidebar Navigation
# ------------------------
menu = st.sidebar.radio(
    "Navigation",
    ["View Listings", "Filter Listings", "Food Claims", "Provider Stats", "Receiver Stats", "Add New Listing", "Manage Listings"]
)

# ------------------------
# View Listings
# ------------------------
if menu == "View Listings":
    st.subheader("\U0001F4CB All Available Food Listings")
    listings_df = pd.read_sql("SELECT * FROM food_listings", conn)
    st.dataframe(listings_df)

# ------------------------
# Filter Listings
# ------------------------
elif menu == "Filter Listings":
    st.subheader("\U0001F50D Filter Food Listings")
    cities = pd.read_sql("SELECT DISTINCT Location FROM food_listings", conn)['Location'].dropna().tolist()
    food_types = pd.read_sql("SELECT DISTINCT Food_Type FROM food_listings", conn)['Food_Type'].dropna().tolist()
    meal_types = pd.read_sql("SELECT DISTINCT Meal_Type FROM food_listings", conn)['Meal_Type'].dropna().tolist()

    city = st.selectbox("Select City", cities)
    food_type = st.selectbox("Select Food Type", food_types)
    meal_type = st.selectbox("Select Meal Type", meal_types)

    filter_query = """
SELECT f.Food_ID, f.Food_Name, f.Quantity, f.Expiry_Date,
       f.Food_Type, f.Meal_Type, f.Location,
       p.Name AS Provider_Name, p.Contact AS Provider_Contact
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
WHERE f.Location = ? AND f.Food_Type = ? AND f.Meal_Type = ?
"""

    filtered_data = pd.read_sql(filter_query, conn, params=(city, food_type, meal_type))
    st.write(f"### Results for {city} - {food_type} - {meal_type}")
    st.dataframe(filtered_data)

# ------------------------
# Food Claims
# ------------------------
elif menu == "Food Claims":
    st.subheader("\U0001F4E6 All Food Claims")
    claims_query = '''
    SELECT c.Claim_ID, f.Food_Name, r.Name AS Receiver_Name, c.Status, c.Timestamp
    FROM claims c
    JOIN food_listings f ON c.Food_ID = f.Food_ID
    JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
    ORDER BY c.Timestamp DESC
    '''
    claims_df = pd.read_sql(claims_query, conn)
    st.dataframe(claims_df)

# ------------------------
# Provider Stats
# ------------------------
elif menu == "Provider Stats":
    st.subheader("\U0001F4CA Total Food Donated by Each Provider")
    provider_query = '''
    SELECT p.Name AS Provider_Name,
           SUM(f.Quantity) AS Total_Quantity_Donated
    FROM food_listings f
    JOIN providers p ON f.Provider_ID = p.Provider_ID
    GROUP BY p.Name
    ORDER BY Total_Quantity_Donated DESC
    '''
    provider_stats = pd.read_sql(provider_query, conn)
    st.dataframe(provider_stats)

# ------------------------
# Receiver Stats
# ------------------------
elif menu == "Receiver Stats":
    st.subheader("\U0001F4C8 Most Active Food Receivers")
    receiver_query = '''
    SELECT r.Name AS Receiver_Name, COUNT(c.Claim_ID) AS Total_Claims
    FROM claims c
    JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
    GROUP BY r.Name
    ORDER BY Total_Claims DESC
    '''
    receiver_stats = pd.read_sql(receiver_query, conn)
    st.dataframe(receiver_stats)

# ------------------------
# Add New Listing
# ------------------------
elif menu == "Add New Listing":
    st.subheader("\u2795 Add a New Food Listing")
    col1, col2 = st.columns(2)

    with col1:
        food_name = st.text_input("\U0001F35D Food Name")
        quantity = st.number_input("\U0001F4E6 Quantity", min_value=1)
        expiry_date = st.date_input("\u23F3 Expiry Date")

    with col2:
        provider_id = st.number_input("\U0001F464 Provider ID", min_value=1)
        provider_type = st.selectbox("\U0001F3EA Provider Type", ["Restaurant", "Grocery Store", "Supermarket"])
        location = st.text_input("\U0001F4CD City / Location")

    food_type = st.selectbox("\U0001F957 Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
    meal_type = st.selectbox("\U0001F374 Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

    if st.button("✅ Submit Listing"):
        try:
            cursor.execute('''
                INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type,
                Location, Food_Type, Meal_Type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (food_name, quantity, str(expiry_date), provider_id, provider_type, location, food_type, meal_type))
            conn.commit()
            st.success("🎉 New listing added successfully!")
        except Exception as e:
            st.error(f"Error: {e}")

# ------------------------
# Manage Listings (Update/Delete)
# ------------------------
elif menu == "Manage Listings":
    st.subheader("🛠️ Edit or Delete a Food Listing")
    food_ids = pd.read_sql("SELECT Food_ID FROM food_listings", conn)['Food_ID'].dropna().astype(int).tolist()


    if food_ids:
        selected_id = st.selectbox("Select Food ID to Manage", food_ids)
        result = pd.read_sql("SELECT * FROM food_listings WHERE Food_ID = ?", conn, params=(selected_id,))

        if not result.empty:
            data = result.iloc[0]
            col1, col2 = st.columns(2)

            with col1:
                food_name = st.text_input("🍽️ Food Name", data['Food_Name'])
                quantity = st.number_input("📦 Quantity", value=int(data['Quantity']), min_value=1)
                expiry_date = st.date_input("⏳ Expiry Date", pd.to_datetime(data['Expiry_Date']))

            with col2:
                provider_id = st.number_input("👤 Provider ID", value=int(data['Provider_ID']), min_value=1)
                provider_type = st.text_input("🏪 Provider Type", data['Provider_Type'])
                location = st.text_input("📍 Location", data['Location'])

            food_type = st.text_input("🥗 Food Type", data['Food_Type'])
            meal_type = st.text_input("🍴 Meal Type", data['Meal_Type'])

            if st.button("✏️ Update Listing"):
                try:
                    cursor.execute('''
                        UPDATE food_listings SET
                            Food_Name = ?, Quantity = ?, Expiry_Date = ?, Provider_ID = ?, Provider_Type = ?,
                            Location = ?, Food_Type = ?, Meal_Type = ?
                        WHERE Food_ID = ?
                    ''', (
                        food_name, quantity, str(expiry_date), provider_id, provider_type,
                        location, food_type, meal_type, selected_id
                    ))
                    conn.commit()
                    st.success("✅ Listing updated successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

            if st.button("🗑️ Delete Listing"):
                try:
                    cursor.execute("DELETE FROM food_listings WHERE Food_ID = ?", (selected_id,))
                    conn.commit()
                    st.warning("⚠️ Listing deleted.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No listing found with that ID.")
    else:
        st.info("No listings available to manage.")
