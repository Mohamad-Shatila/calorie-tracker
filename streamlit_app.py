import streamlit as st
import pandas as pd
import datetime
import numpy as np
from io import BytesIO
import base64

# Set page configuration
st.set_page_config(
    page_title="Calorie Tracker",
    page_icon="🍏",
    layout="wide"
)

# Initialize session state variables
if 'meals' not in st.session_state:
    st.session_state.meals = pd.DataFrame(columns=['Date', 'Meal', 'Protein', 'Carbs', 'Fat', 'Calories'])
if 'bmr' not in st.session_state:
    st.session_state.bmr = None
if 'weights' not in st.session_state:
    st.session_state.weights = pd.DataFrame(columns=['Date', 'Weight'])

# App title and description
st.title("🍏 Calorie Tracker")
st.markdown("Track your meals, monitor your macros, and measure your progress toward your fitness goals.")

# Sidebar for BMR and navigation
with st.sidebar:
    st.header("Settings")
    
    # BMR input
    current_bmr = st.session_state.bmr if st.session_state.bmr else 0
    new_bmr = st.number_input("Your BMR (Calories)", min_value=0, value=current_bmr, step=10)
    if new_bmr != current_bmr:
        st.session_state.bmr = new_bmr
        st.success("BMR updated!")
    
    st.divider()
    
    # Navigation
    st.header("Navigation")
    page = st.radio("Go to", ["Add Meal", "View Progress", "Edit Data", "Export Data"])
    
    st.divider()
    
    # Quick stats
    if not st.session_state.meals.empty:
        today = datetime.date.today().isoformat()
        today_calories = st.session_state.meals[
            st.session_state.meals['Date'] == today
        ]['Calories'].sum()
        
        st.metric("Today's Calories", f"{today_calories:.0f}")
        
        if st.session_state.bmr:
            remaining = st.session_state.bmr - today_calories
            st.metric("Remaining Calories", f"{remaining:.0f}")

# Add Meal page
if page == "Add Meal":
    st.header("Add New Meal")
    
    with st.form("meal_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            meal_date = st.date_input("Date", value=datetime.date.today())
            meal_name = st.text_input("Meal Name")
        
        with col2:
            protein = st.number_input("Protein (g)", min_value=0.0, step=0.5)
            carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.5)
            fat = st.number_input("Fat (g)", min_value=0.0, step=0.5)
        
        # Calculate calories if not provided
        calories = st.number_input("Calories (optional)", min_value=0, step=10, 
                                  help="Leave as 0 to calculate from macros")
        
        submitted = st.form_submit_button("Add Meal")
        
        if submitted:
            if meal_name == "":
                st.error("Please enter a meal name")
            else:
                # Calculate calories if not provided (4 cal/g for protein and carbs, 9 cal/g for fat)
                if calories == 0:
                    calories = protein * 4 + carbs * 4 + fat * 9
                
                # Add meal to dataframe
                new_meal = pd.DataFrame({
                    'Date': [meal_date.isoformat()],
                    'Meal': [meal_name],
                    'Protein': [protein],
                    'Carbs': [carbs],
                    'Fat': [fat],
                    'Calories': [calories]
                })
                
                st.session_state.meals = pd.concat([st.session_state.meals, new_meal], ignore_index=True)
                st.success(f"Added {meal_name} with {calories} calories!")
                
                # Option to add weight
                add_weight = st.checkbox("Add weight measurement for this date")
                if add_weight:
                    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
                    if weight > 0:
                        if meal_date.isoformat() in st.session_state.weights['Date'].values:
                            st.session_state.weights.loc[
                                st.session_state.weights['Date'] == meal_date.isoformat(), 'Weight'
                            ] = weight
                        else:
                            new_weight = pd.DataFrame({
                                'Date': [meal_date.isoformat()],
                                'Weight': [weight]
                            })
                            st.session_state.weights = pd.concat(
                                [st.session_state.weights, new_weight], ignore_index=True
                            )
                        st.success("Weight updated!")

# View Progress page
elif page == "View Progress":
    st.header("Your Progress")
    
    if st.session_state.meals.empty:
        st.info("No meals recorded yet. Add some meals to see your progress.")
    else:
        # Daily calories chart
        daily_calories = st.session_state.meals.groupby('Date')['Calories'].sum().reset_index()
        daily_calories['Date'] = pd.to_datetime(daily_calories['Date'])
        
        st.subheader("Daily Calorie Intake")
        st.line_chart(daily_calories, x='Date', y='Calories')
        
        # Macro breakdown
        st.subheader("Macro Distribution")
        daily_macros = st.session_state.meals.groupby('Date')[['Protein', 'Carbs', 'Fat']].sum().reset_index()
        daily_macros['Date'] = pd.to_datetime(daily_macros['Date'])
        
        tab1, tab2, tab3 = st.tabs(["Protein", "Carbs", "Fat"])
        
        with tab1:
            st.area_chart(daily_macros, x='Date', y='Protein')
        with tab2:
            st.area_chart(daily_macros, x='Date', y='Carbs')
        with tab3:
            st.area_chart(daily_macros, x='Date', y='Fat')
        
        # Progress calculation
        if st.session_state.bmr and not st.session_state.weights.empty:
            st.subheader("Weight Loss Analysis")
            
            # Prepare weight data
            weight_data = st.session_state.weights.copy()
            weight_data['Date'] = pd.to_datetime(weight_data['Date'])
            weight_data = weight_data.sort_values('Date')
            
            # Calculate theoretical weight loss
            calorie_data = daily_calories.copy()
            calorie_data = calorie_data.merge(weight_data, on='Date', how='outer').sort_values('Date')
            calorie_data['BMR'] = st.session_state.bmr
            calorie_data['CalorieDeficit'] = calorie_data['BMR'] - calorie_data['Calories']
            calorie_data['CumulativeDeficit'] = calorie_data['CalorieDeficit'].cumsum()
            calorie_data['TheoreticalLoss'] = calorie_data['CumulativeDeficit'] / 7700  # 7700 cal ≈ 1 kg
            
            # Display comparison
            comparison_df = calorie_data[['Date', 'Weight', 'TheoreticalLoss']].dropna()
            if not comparison_df.empty:
                comparison_df['ActualLoss'] = comparison_df['Weight'].iloc[0] - comparison_df['Weight']
                
                st.line_chart(
                    comparison_df, 
                    x='Date', 
                    y=['ActualLoss', 'TheoreticalLoss'],
                    color=['#FF0000', '#0000FF']
                )
                
                latest = comparison_df.iloc[-1]
                st.metric("Actual Weight Loss", f"{latest['ActualLoss']:.2f} kg")
                st.metric("Theoretical Weight Loss", f"{latest['TheoreticalLoss']:.2f} kg")
                st.metric("Difference", f"{abs(latest['ActualLoss'] - latest['TheoreticalLoss']):.2f} kg",
                         delta=f"{((latest['ActualLoss'] - latest['TheoreticalLoss'])/latest['TheoreticalLoss']*100):.1f}%" 
                         if latest['TheoreticalLoss'] != 0 else "N/A")

# Edit Data page
elif page == "Edit Data":
    st.header("Edit Your Data")
    
    edit_option = st.radio("What would you like to edit?", 
                          ["Meal entries", "Weight entries"])
    
    if edit_option == "Meal entries":
        if st.session_state.meals.empty:
            st.info("No meals to edit.")
        else:
            edited_meals = st.data_editor(
                st.session_state.meals,
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("Save Meal Changes"):
                st.session_state.meals = edited_meals
                st.success("Meals updated!")
    
    else:  # Weight entries
        if st.session_state.weights.empty:
            st.info("No weight entries to edit.")
        else:
            edited_weights = st.data_editor(
                st.session_state.weights,
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("Save Weight Changes"):
                st.session_state.weights = edited_weights
                st.success("Weights updated!")
        
        # Add new weight entry
        st.subheader("Add New Weight Entry")
        with st.form("weight_form"):
            w_col1, w_col2 = st.columns(2)
            with w_col1:
                weight_date = st.date_input("Date", key="weight_date", value=datetime.date.today())
            with w_col2:
                new_weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
            
            if st.form_submit_button("Add Weight Entry"):
                if new_weight > 0:
                    if weight_date.isoformat() in st.session_state.weights['Date'].values:
                        st.session_state.weights.loc[
                            st.session_state.weights['Date'] == weight_date.isoformat(), 'Weight'
                        ] = new_weight
                    else:
                        new_entry = pd.DataFrame({
                            'Date': [weight_date.isoformat()],
                            'Weight': [new_weight]
                        })
                        st.session_state.weights = pd.concat(
                            [st.session_state.weights, new_entry], ignore_index=True
                        )
                    st.success("Weight entry added/updated!")

# Export Data page
elif page == "Export Data":
    st.header("Export Your Data")
    
    # Create Excel file in memory
    @st.cache_data
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Meals')
            if not st.session_state.weights.empty:
                st.session_state.weights.to_excel(writer, index=False, sheet_name='Weights')
            settings_df = pd.DataFrame({
                'Setting': ['BMR'],
                'Value': [st.session_state.bmr]
            })
            settings_df.to_excel(writer, index=False, sheet_name='Settings')
        processed_data = output.getvalue()
        return processed_data
    
    if not st.session_state.meals.empty:
        excel_data = convert_df_to_excel(st.session_state.meals)
        st.download_button(
            label="Download Excel file",
            data=excel_data,
            file_name="calorie_tracker.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("Current Data Preview")
        st.dataframe(st.session_state.meals, use_container_width=True)
        
        if not st.session_state.weights.empty:
            st.dataframe(st.session_state.weights, use_container_width=True)
    else:
        st.info("No data to export yet.")

# Footer
st.divider()
st.caption("Calorie Tracker App - Track your nutrition and progress")
