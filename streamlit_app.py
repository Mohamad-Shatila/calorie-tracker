import streamlit as st
import pandas as pd
import datetime
import numpy as np
from io import BytesIO
import json
import os

# Set page configuration
st.set_page_config(
    page_title="Calorie Tracker",
    page_icon="🍏",
    layout="wide"
)

# Function to load data from file
def load_data():
    try:
        if os.path.exists('calorie_tracker_data.json'):
            with open('calorie_tracker_data.json', 'r') as f:
                data = json.load(f)
                
            # Convert back to DataFrames
            meals = pd.DataFrame(data['meals']) if data['meals'] else pd.DataFrame(columns=['Date', 'Meal', 'Protein', 'Carbs', 'Fat', 'Calories'])
            weights = pd.DataFrame(data['weights']) if data['weights'] else pd.DataFrame(columns=['Date', 'Weight'])
            exercises = pd.DataFrame(data['exercises']) if data['exercises'] else pd.DataFrame(columns=['Date', 'Activity', 'Duration', 'CaloriesBurned'])
            
            return meals, weights, exercises, data['bmr']
    except:
        pass
    
    # Return empty data if file doesn't exist or error occurs
    return (pd.DataFrame(columns=['Date', 'Meal', 'Protein', 'Carbs', 'Fat', 'Calories']),
            pd.DataFrame(columns=['Date', 'Weight']),
            pd.DataFrame(columns=['Date', 'Activity', 'Duration', 'CaloriesBurned']),
            None)

# Function to save data to file
def save_data(meals, weights, exercises, bmr):
    data = {
        'meals': meals.to_dict('records'),
        'weights': weights.to_dict('records'),
        'exercises': exercises.to_dict('records'),
        'bmr': bmr
    }
    
    with open('calorie_tracker_data.json', 'w') as f:
        json.dump(data, f)

# Load data at startup
if 'initialized' not in st.session_state:
    st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr = load_data()
    st.session_state.initialized = True

# More precise activity database with MET values
ACTIVITY_DB = {
    "Walking (slow, 2 mph)": 2.5,
    "Walking (moderate, 3 mph)": 3.5,
    "Walking (brisk, 3.5 mph)": 4.0,
    "Walking (very brisk, 4 mph)": 5.0,
    "Running (5 mph/8 kmh)": 8.0,
    "Running (6 mph/9.6 kmh)": 10.0,
    "Running (7.5 mph/12 kmh)": 12.5,
    "Cycling (leisure, <10 mph)": 6.0,
    "Cycling (moderate, 12-14 mph)": 8.0,
    "Swimming (moderate effort)": 8.0,
    "Weight Training (moderate)": 5.0,
    "Weight Training (vigorous)": 7.0,
    "HIIT Workout": 9.0,
    "Padel/Tennis (doubles)": 6.0,
    "Padel/Tennis (singles)": 8.0,
    "Basketball": 8.0,
    "Yoga": 3.0,
    "Pilates": 4.0
}

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
        save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
        st.success("BMR updated!")
    
    st.divider()
    
    # Navigation
    st.header("Navigation")
    page = st.radio("Go to", ["Add Meal", "Log Exercise", "View Progress", "Edit Data", "Export Data"])
    
    st.divider()
    
    # Quick stats
    if not st.session_state.meals.empty and st.session_state.bmr:
        today = datetime.date.today().isoformat()
        
        # Calculate today's calories from food
        today_calories = st.session_state.meals[
            st.session_state.meals['Date'] == today
        ]['Calories'].sum()
        
        # Calculate today's calories burned from exercise
        today_exercise_cals = st.session_state.exercises[
            st.session_state.exercises['Date'] == today
        ]['CaloriesBurned'].sum()
        
        # Calculate net calories
        net_calories = today_calories - st.session_state.bmr - today_exercise_cals
        
        st.metric("Today's Calories", f"{today_calories:.0f}")
        st.metric("Exercise Calories", f"{today_exercise_cals:.0f}")
        st.metric("Net Balance", f"{net_calories:.0f}", 
                 delta="Surplus" if net_calories > 0 else "Deficit")

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
                save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
                st.success(f"Added {meal_name} with {calories} calories!")

# Log Exercise page
elif page == "Log Exercise":
    st.header("Log Exercise Activity")
    
    with st.form("exercise_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            ex_date = st.date_input("Date", value=datetime.date.today())
            activity = st.selectbox("Activity", options=list(ACTIVITY_DB.keys()))
            duration = st.number_input("Duration (minutes)", min_value=1, value=30)
        
        with col2:
            if st.session_state.bmr:
                # Calculate calories burned using the correct formula: Calories = MET * weight_kg * time_hours
                weight_est = 134.25  # Default to your provided weight
                if not st.session_state.weights.empty:
                    # Get the most recent weight entry
                    weight_est = st.session_state.weights.sort_values('Date').iloc[-1]['Weight']
                
                met_value = ACTIVITY_DB[activity]
                hours = duration / 60  # Convert minutes to hours
                calories_burned = met_value * weight_est * hours
                
                st.metric("Estimated Calories Burned", f"{calories_burned:.0f}")
            else:
                st.info("Enter your BMR in settings to calculate calories burned")
                calories_burned = 0
        
        submitted = st.form_submit_button("Log Exercise")
        
        if submitted:
            new_exercise = pd.DataFrame({
                'Date': [ex_date.isoformat()],
                'Activity': [activity],
                'Duration': [duration],
                'CaloriesBurned': [calories_burned]
            })
            
            st.session_state.exercises = pd.concat([st.session_state.exercises, new_exercise], ignore_index=True)
            save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
            st.success(f"Logged {duration} minutes of {activity}!")

# View Progress page
elif page == "View Progress":
    st.header("Your Progress")
    
    if st.session_state.meals.empty:
        st.info("No meals recorded yet. Add some meals to see your progress.")
    else:
        # Create combined data for analysis
        daily_calories = st.session_state.meals.groupby('Date')['Calories'].sum().reset_index()
        daily_calories['Date'] = pd.to_datetime(daily_calories['Date'])
        
        # Add exercise data if available
        if not st.session_state.exercises.empty:
            daily_exercise = st.session_state.exercises.groupby('Date')['CaloriesBurned'].sum().reset_index()
            daily_exercise['Date'] = pd.to_datetime(daily_exercise['Date'])
            daily_calories = daily_calories.merge(daily_exercise, on='Date', how='left')
            daily_calories['CaloriesBurned'] = daily_calories['CaloriesBurned'].fillna(0)
            daily_calories['NetCalories'] = daily_calories['Calories'] - daily_calories['CaloriesBurned']
        else:
            daily_calories['CaloriesBurned'] = 0
            daily_calories['NetCalories'] = daily_calories['Calories']
        
        st.subheader("Daily Calorie Intake vs Burned")
        st.bar_chart(daily_calories, x='Date', y=['Calories', 'CaloriesBurned'])
        
        # Calculate theoretical weight loss with exercise
        if st.session_state.bmr and not st.session_state.weights.empty:
            st.subheader("Weight Loss Analysis with Exercise")
            
            # Prepare weight data
            weight_data = st.session_state.weights.copy()
            weight_data['Date'] = pd.to_datetime(weight_data['Date'])
            weight_data = weight_data.sort_values('Date')
            
            # Calculate theoretical weight loss
            analysis_data = daily_calories.copy()
            analysis_data = analysis_data.merge(weight_data, on='Date', how='outer').sort_values('Date')
            analysis_data['BMR'] = st.session_state.bmr
            analysis_data['CalorieDeficit'] = analysis_data['BMR'] - analysis_data['NetCalories']
            analysis_data['CumulativeDeficit'] = analysis_data['CalorieDeficit'].cumsum()
            analysis_data['TheoreticalLoss'] = analysis_data['CumulativeDeficit'] / 7700  # 7700 cal ≈ 1 kg
            
            # Display comparison
            comparison_df = analysis_data[['Date', 'Weight', 'TheoreticalLoss']].dropna()
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
                          ["Meal entries", "Weight entries", "Exercise entries"])
    
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
                save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
                st.success("Meals updated!")
    
    elif edit_option == "Weight entries":
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
                save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
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
                    save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
                    st.success("Weight entry added/updated!")
    
    else:  # Exercise entries
        if st.session_state.exercises.empty:
            st.info("No exercise entries to edit.")
        else:
            edited_exercises = st.data_editor(
                st.session_state.exercises,
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("Save Exercise Changes"):
                st.session_state.exercises = edited_exercises
                save_data(st.session_state.meals, st.session_state.weights, st.session_state.exercises, st.session_state.bmr)
                st.success("Exercises updated!")

# Export Data page
elif page == "Export Data":
    st.header("Export Your Data")
    
    # Create Excel file in memory
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Meals')
            if not st.session_state.weights.empty:
                st.session_state.weights.to_excel(writer, index=False, sheet_name='Weights')
            if not st.session_state.exercises.empty:
                st.session_state.exercises.to_excel(writer, index=False, sheet_name='Exercises')
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
            
        if not st.session_state.exercises.empty:
            st.dataframe(st.session_state.exercises, use_container_width=True)
    else:
        st.info("No data to export yet.")

# Add a button to clear all data (for testing)
with st.sidebar:
    st.divider()
    if st.button("Clear All Data"):
        st.session_state.meals = pd.DataFrame(columns=['Date', 'Meal', 'Protein', 'Carbs', 'Fat', 'Calories'])
        st.session_state.weights = pd.DataFrame(columns=['Date', 'Weight'])
        st.session_state.exercises = pd.DataFrame(columns=['Date', 'Activity', 'Duration', 'CaloriesBurned'])
        st.session_state.bmr = None
        if os.path.exists('calorie_tracker_data.json'):
            os.remove('calorie_tracker_data.json')
        st.success("All data cleared!")

# Footer
st.divider()
st.caption("Calorie Tracker App - Track your nutrition, exercise, and progress")
