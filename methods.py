import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Global Variable
DATABASE_NAME = 'med_tracker_inventory_final.db'

# Helper Functions and Methods
def create_connection():
    """Creates a database connection."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

conn = create_connection()

def create_table():
    """Creates the Medicines table."""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Medicines (
                medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                generic_name TEXT NOT NULL UNIQUE,
                brand_name TEXT,
                schedule_8am INTEGER DEFAULT 0,
                schedule_1pm INTEGER DEFAULT 0,
                schedule_8pm INTEGER DEFAULT 0,
                intended_duration_days INTEGER NOT NULL DEFAULT 0,
                doses_left INTEGER NOT NULL DEFAULT 0,
                price REAL,
                notes TEXT,
                last_updated TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")
    finally:
        if conn:
            conn.close()


def add_medicine(conn, medicine):
    """Adds a new medicine."""
    sql = '''INSERT INTO Medicines(generic_name, brand_name, schedule_8am, schedule_1pm, schedule_8pm, 
    intended_duration_days, doses_left, price, notes, last_updated) VALUES(?,?,?,?,?,?,?,?,?,?)'''
    cursor = conn.cursor()
    try:
        cursor.execute(sql, medicine)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        st.error(f"Error: Medicine '{medicine[0]}' already exists.")
        return None


def update_medicine(conn, medicine_id, update_data):
    """Updates an existing medicine, only changing the fields provided in update_data."""
    sql_parts = ["UPDATE Medicines SET last_updated = ?"]
    values = [datetime.now().strftime("%d-%m-%Y")]  # Use DD-MM-YYYY format
    if update_data.get("generic_name") is not None:
        sql_parts.append(", generic_name = ?")
        values.append(update_data["generic_name"])
    if update_data.get("brand_name") is not None:
        sql_parts.append(", brand_name = ?")
        values.append(update_data["brand_name"])
    if update_data.get("schedule_8am") is not None:
        sql_parts.append(", schedule_8am = ?")
        values.append(update_data["schedule_8am"])
    if update_data.get("schedule_1pm") is not None:
        sql_parts.append(", schedule_1pm = ?")
        values.append(update_data["schedule_1pm"])
    if update_data.get("schedule_8pm") is not None:
        sql_parts.append(", schedule_8pm = ?")
        values.append(update_data["schedule_8pm"])
    if update_data.get("intended_duration_days") is not None:
        sql_parts.append(", intended_duration_days = ?")
        values.append(update_data["intended_duration_days"])
    if update_data.get("doses_left") is not None:
        sql_parts.append(", doses_left = ?")
        values.append(update_data["doses_left"])
    if update_data.get("price") is not None:
        sql_parts.append(", price = ?")
        values.append(update_data["price"])
    if update_data.get('last_updated') is not None:
        sql_parts.append(", last_updated = ?")
        values.append(update_data["last_updated"])
    if update_data.get("notes") is not None:
        sql_parts.append(", notes = ?")
        values.append(update_data["notes"])

    sql_parts.append(" WHERE medicine_id = ?")
    values.append(medicine_id)

    sql = " ".join(sql_parts)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error updating medicine: {e}")
        return False


def get_all_medicines(conn):
    """Retrieves all medicines from the table."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Medicines")
    rows = cursor.fetchall()
    return rows


def calculate_doses_per_day(schedule_8am, schedule_1pm, schedule_8pm):
    """Calculates the number of doses taken per day."""
    return schedule_8am + schedule_1pm + schedule_8pm


def calculate_to_buy(doses_per_day, doses_left, intended_days):
    """Calculates the number of doses to buy to reach the desired stock level."""
    needed_doses = intended_days * doses_per_day
    to_buy = needed_doses - doses_left
    return max(0, to_buy)


def calculate_days_available(doses_per_day, doses_left):
    """Calculates the number of days the current stock will last."""
    if doses_per_day > 0 and doses_left >= 0:
        return doses_left // doses_per_day
    elif doses_left < 0:
        return 0
    else:
        return 0


def medicines_to_dictionaries(medicines, current_date):
    """Converts a list of medicine tuples to a list of dictionaries,
    calculating computed columns."""
    medicine_dicts = []
    for med in medicines:
        (
            medicine_id,
            generic_name,
            brand_name,
            sch_8am,
            sch_1pm,
            sch_8pm,
            intended_days,
            left,
            price,
            notes,
            last_updated,
        ) = med
        schedule_str = (
            f"{'8AM' if sch_8am else ''} {'1PM' if sch_1pm else ''} {'8PM' if sch_8pm else ''}"
        ).strip()
        doses_per_day = calculate_doses_per_day(sch_8am, sch_1pm, sch_8pm)
        try:
            last_updated_date = datetime.strptime(last_updated, "%Y-%m-%d").date() #convert string to date object
        except:
            last_updated_date = datetime.strptime(last_updated, "%d-%m-%Y").date()  # convert string to date object
        try:
            current_date = datetime.strptime(current_date, "%d%m%Y").date()
        except:
            pass

        formatted_current_date = current_date.strftime("%d-%m-%Y")
        formatted_last_updated = last_updated_date.strftime("%d-%m-%Y")

        # st.text(f'Current {current_date} | Last Updated {last_updated}')
        # st.text(f'Current {type(current_date)} | Last Updated {type(last_updated_date)}')

        tdiff = current_date - last_updated_date
        days_since_update = int(tdiff.days)
        # st.text(f'Days Since Last Update: {days_since_update}')

        adjusted_intended_days = max(0, intended_days - days_since_update, 0)
        adjusted_left = max(0, left - (doses_per_day * days_since_update), 0)
        to_buy = calculate_to_buy(doses_per_day, adjusted_left, adjusted_intended_days)
        price_per_day = doses_per_day * price if price is not None else 0
        days_remaining = calculate_days_available(doses_per_day, adjusted_left)

        medicine_dict = {
            "Medicine": f"{generic_name}",
            "Schedule": schedule_str,
            "Prescribed Days": adjusted_intended_days,
            "Stock Remaining (Days)": days_remaining,
            "Stocks Left (Item)": adjusted_left,
            "Price per Piece": price,  # Price Per Piece
            "Price Per Day": price_per_day,
            "To Buy": to_buy,
            "Notes": notes,
            "Last Updated": current_date,
        }
        medicine_dicts.append(medicine_dict)

        if days_remaining < 3:
            st.warning(f'Stock for {generic_name} low, please restock.')

        if days_since_update > 0:
            update_data = {
                "generic_name": generic_name,
                "brand_name": med[2],
                "schedule_8am": med[3],
                "schedule_1pm": med[4],
                "schedule_8pm": med[5],
                "intended_duration_days": adjusted_intended_days,
                "doses_left": adjusted_left,
                "price": price,
                "last_updated": current_date,
                "notes": notes,
            }
            update_medicine(conn, med[0], update_data)

    return medicine_dicts


def display_inventory_streamlit(conn, current_date):
    """Displays the medicine inventory using Streamlit."""
    medicines = get_all_medicines(conn)
    if not medicines:
        st.warning("No medicines in the inventory.")
        return

    medicine_dicts = medicines_to_dictionaries(medicines, current_date=current_date)
    df = pd.DataFrame(medicine_dicts)

    # Reorder columns for display
    df = df[["Medicine", "Schedule", "Prescribed Days", "Stock Remaining (Days)", "Stocks Left (Item)", "Price per Piece", "Price Per Day", "To Buy", "Notes", "Last Updated"]]

    st.dataframe(df)


def delete_medicine_by_name(conn, medicine_name):
    """Deletes a medicine from the database by its generic name."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Medicines WHERE generic_name = ?", (medicine_name,))
        conn.commit()
        return True  # Indicate success
    except sqlite3.Error as e:
        st.error(f"Error deleting medicine: {e}")
        return False  # Indicate failure


def calculate_total_to_buy_price(conn):
    """Calculates the total price of medicines to be purchased."""
    medicines = get_all_medicines(conn)
    total_price = 0
    for med in medicines:
        doses_per_day = calculate_doses_per_day(med[3], med[4], med[5])
        to_buy = calculate_to_buy(doses_per_day, med[7], med[6])
        if to_buy > 0 and med[8] is not None:  # Check if price is not None
            total_price += to_buy * med[8]
    return total_price


def converter(variable):
    if not variable:
        return 0
    else:
        return 1
