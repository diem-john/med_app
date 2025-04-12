from methods import *

create_table()
conn = create_connection()

st.title('Meds Tracker & Inventory')
st.subheader(f'Date: {datetime.now().strftime("%m-%d-%Y")}')

st.sidebar.title('Task Management')
task_ = st.sidebar.selectbox('Select Task:',
                             ('Add New Medicine',
                              'Update Medicine',
                              'Delete Item'))

st.sidebar.header('Inventory Management')
if task_ == 'Add New Medicine':
    st.sidebar.subheader('Add New Medicine to Inventory')
    with st.sidebar.form('add_medicine_form'):
        generic_name = st.text_input('Enter Generic Name: ').strip()
        brand_name = st.text_input("Enter Brand Name (optional): ").strip()
        schedule_8am = converter(st.checkbox("Take at 8 AM?"))
        schedule_1pm = converter(st.checkbox("Take at 1 PM?"))
        schedule_8pm = converter(st.checkbox("Take at 8 PM?"))
        intended_duration_days = int(st.number_input("Enter Intended Duration (in days): "))
        doses_left = int(st.number_input("Enter Current Doses Left: "))  # Add doses_left input
        price = st.number_input("Price (₱): ")
        notes = st.text_input("Enter any notes (optional): ").strip()
        medicine = (generic_name, brand_name, schedule_8am, schedule_1pm,
                    schedule_8pm, intended_duration_days, doses_left, price, notes)
        submit_button = st.form_submit_button("Add this entry?")
        if submit_button:
            if not generic_name:
                st.error("Generic Name is required.")
            else:
                medicine = (
                    generic_name,
                    brand_name,
                    schedule_8am,
                    schedule_1pm,
                    schedule_8pm,
                    intended_duration_days,
                    doses_left,
                    price,
                    notes,
                )
                medicine_id = add_medicine(conn, medicine)
                if medicine_id:
                    st.success(f"Medicine '{generic_name}' added!")
                else:
                    st.error(f"Failed to add medicine '{generic_name}'.")
elif task_ == 'Update Medicine':
    st.sidebar.header("Update Medicine")
    medicines = get_all_medicines(conn)
    if not medicines:
        st.warning("No medicines to update.")
    medicine_names = [med[1] for med in medicines]
    selected_medicine_name = st.sidebar.selectbox("Select medicine to update", medicine_names)

    selected_medicine = next((med for med in medicines if med[1] == selected_medicine_name), None)
    if not selected_medicine:
        st.error("Medicine not found.")
    medicine_id_to_update = selected_medicine[0]
    with st.sidebar.form("update_medicine_form"):
        generic_name = st.text_input("Generic Name", value=selected_medicine[1], key="update_generic_name")
        brand_name = st.text_input("Brand Name (optional)", value=selected_medicine[2] or "", key="update_brand_name")
        schedule_8am = st.checkbox("8 AM", value=selected_medicine[3], key="update_schedule_8am")
        schedule_1pm = st.checkbox("1 PM", value=selected_medicine[4], key="update_schedule_1pm")
        schedule_8pm = st.checkbox("8 PM", value=selected_medicine[5], key="update_schedule_8pm")
        intended_duration_days = st.number_input("Intended Duration (days)", min_value=1, value=selected_medicine[6],
                                                 key="update_intended_duration")
        doses_left = st.number_input("Current Doses Left", min_value=0, value=selected_medicine[7],
                                     key="update_doses_left")
        price = st.number_input("Price", min_value=0.0, format="%.2f", value=selected_medicine[8] or 0,
                                key="update_price")
        notes = st.text_area("Notes (optional)", value=selected_medicine[9] or "", key="update_notes")

        update_button = st.form_submit_button("Update")
        if update_button:
            update_data = {}
            if generic_name != selected_medicine[1]:
                update_data["generic_name"] = generic_name
            if brand_name != selected_medicine[2]:
                update_data["brand_name"] = brand_name
            if converter(schedule_8am) != selected_medicine[3]:
                update_data["schedule_8am"] = converter(schedule_8am)
            if converter(schedule_1pm) != selected_medicine[4]:
                update_data["schedule_1pm"] = converter(schedule_1pm)
            if converter(schedule_8pm) != selected_medicine[5]:
                update_data["schedule_8pm"] = converter(schedule_8pm)
            if intended_duration_days != selected_medicine[6]:
                update_data["intended_duration_days"] = intended_duration_days
            if doses_left != selected_medicine[7]:
                update_data["doses_left"] = doses_left
            if price != selected_medicine[8]:
                update_data["price"] = price
            if notes != selected_medicine[9]:
                update_data["notes"] = notes

            if update_data:  # Only update if there are changes
                if update_medicine(conn, medicine_id_to_update, update_data):
                    st.success("Medicine updated successfully!")
                    display_inventory_streamlit(conn)
                else:
                    st.error("Failed to update medicine.")
            else:
                st.info("No changes were made.")
elif task_ == 'Delete Item':
    st.sidebar.header("Delete Medicine by ID")
    medicines = get_all_medicines(conn)
    medicine_names = [med[1] for med in medicines]
    selected_medicine_name = st.sidebar.selectbox("Select medicine to delete", medicine_names)
    if st.sidebar.button("Delete Medicine"):
        if delete_medicine_by_name(conn, selected_medicine_name):
            st.success(f"Medicine with ID {selected_medicine_name} deleted successfully.")
            display_inventory_streamlit(conn)
        else:
            st.error(f"Failed to delete medicine with ID {selected_medicine_name}.")

st.subheader('Inventory Display')
display_inventory_streamlit(conn)

total_price_to_buy = calculate_total_to_buy_price(conn)
st.write(f"Total Price of Medicines to Buy: ₱{total_price_to_buy:.2f}")

if conn:
    conn.close()
