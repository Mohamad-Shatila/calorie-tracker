import streamlit as st
import pandas as pd
import os

FILE_NAME = "calorie_log.xlsx"

# Load or create Excel file
if os.path.exists(FILE_NAME):
    df = pd.read_excel(FILE_NAME)
else:
    df = pd.DataFrame(columns=["Meal", "Calories", "Protein (g)", "Carbs (g)", "Fat (g)"])

st.title("🍽️ Calorie & Macro Tracker")

# --- Add New Meal ---
st.header("Add a Meal")
meal = st.text_input("Meal Name")
calories = st.number_input("Calories", min_value=0, step=1)
protein = st.number_input("Protein (g)", min_value=0.0, step=0.1)
carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.1)
fat = st.number_input("Fat (g)", min_value=0.0, step=0.1)

if st.button("Add Meal"):
    new_row = {"Meal": meal, "Calories": calories, "Protein (g)": protein, "Carbs (g)": carbs, "Fat (g)": fat}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(FILE_NAME, index=False)
    st.success(f"✅ Added {meal}!")

# --- View Meals ---
st.header("Logged Meals")
st.dataframe(df)

# --- Edit / Delete ---
st.header("Edit or Delete a Meal")
if not df.empty:
    selected_index = st.number_input("Select meal index to edit/delete", min_value=0, max_value=len(df)-1, step=1)

    selected_row = df.iloc[selected_index]
    st.write("Currently selected:", selected_row)

    new_meal = st.text_input("Edit Meal Name", selected_row["Meal"])
    new_calories = st.number_input("Edit Calories", value=int(selected_row["Calories"]))
    new_protein = st.number_input("Edit Protein (g)", value=float(selected_row["Protein (g)"]))
    new_carbs = st.number_input("Edit Carbs (g)", value=float(selected_row["Carbs (g)"]))
    new_fat = st.number_input("Edit Fat (g)", value=float(selected_row["Fat (g)"]))

    if st.button("Update Meal"):
        df.loc[selected_index] = [new_meal, new_calories, new_protein, new_carbs, new_fat]
        df.to_excel(FILE_NAME, index=False)
        st.success("✅ Meal updated!")

    if st.button("Delete Meal"):
        df = df.drop(selected_index).reset_index(drop=True)
        df.to_excel(FILE_NAME, index=False)
        st.warning("🗑️ Meal deleted!")

# --- Download Excel ---
st.header("Download Your Log")
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "rb") as f:
        st.download_button("⬇️ Download Excel", f, file_name=FILE_NAME)
