import streamlit as st
import cx_Oracle
import pandas as pd

# ✅ Connect to Oracle DB
try:
    conn = cx_Oracle.connect("SYSTEM", "prachita4", "localhost:1521/XE")
    cur = conn.cursor()
except cx_Oracle.DatabaseError as e:
    st.error(f"❌ Could not connect to Oracle DB: {e}")
    st.stop()

st.title("🏋️‍♀️ Fitness Tracker Dashboard")

menu = st.sidebar.radio("Navigate", [
    "Add User", "View Users", "Statistics",
    "View Workouts", "Log Workout",
    "View Meals", "Log Meal", "Goal Check"
])

# Add User
if menu == "Add User":
    st.subheader("➕ Register a New User")
    with st.form("add_user_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        age = st.number_input("Age", min_value=10, max_value=100)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0)
        weight = st.number_input("Weight (kg)", min_value=20.0, max_value=200.0)
        goal = st.selectbox("Goal", ["Lose Weight", "Gain Muscle", "Maintain"])
        submit = st.form_submit_button("Add User")
        if submit:
            try:
                cur.execute("""
                    INSERT INTO Users (user_id, name, email, password, age, gender, height, weight, goal)
                    VALUES (user_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8)
                """, (name, email, password, age, gender, height, weight, goal))
                conn.commit()
                st.success(f"✅ User '{name}' added successfully!")
            except Exception as e:
                st.error(f"❌ Error inserting user: {e}")

# View Users
elif menu == "View Users":
    st.subheader("📋 Registered Users")
    try:
        cur.execute("SELECT user_id, name, email, age, goal FROM Users")
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Error fetching user data: {e}")

# Statistics
elif menu == "Statistics":
    st.subheader("📊 Fitness Statistics Overview")
    try:
        st.markdown("### 🥗 Total Calories Consumed Per User")
        cur.execute("""
            SELECT u.name, SUM(f.calories * mi.quantity) AS total_calories
            FROM Users u
            JOIN Meals m ON u.user_id = m.user_id
            JOIN Meal_Items mi ON m.meal_id = mi.meal_id
            JOIN Food f ON mi.food_id = f.food_id
            GROUP BY u.name
            ORDER BY total_calories DESC
        """)
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        st.dataframe(df)

        st.markdown("### 🔥 Total Calories Burned Per User")
        cur.execute("""
            SELECT u.name, SUM(we.duration * e.calories_burned / 60) AS total_burned
            FROM Users u
            JOIN Workout w ON u.user_id = w.user_id
            JOIN Workout_Exercises we ON w.workout_id = we.workout_id
            JOIN Exercise e ON we.exercise_id = e.exercise_id
            GROUP BY u.name
            ORDER BY total_burned DESC
        """)
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        st.dataframe(df)

        st.markdown("### 🍕 Top 3 Most Frequently Logged Foods")
        cur.execute("""
            SELECT f.name, COUNT(*) AS times_logged
            FROM Meal_Items mi
            JOIN Food f ON mi.food_id = f.food_id
            GROUP BY f.name
            ORDER BY times_logged DESC
            FETCH FIRST 3 ROWS ONLY
        """)
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Failed to load statistics: {e}")

# View Workouts
elif menu == "View Workouts":
    st.subheader("🏃 Workout Logs")
    try:
        cur.execute("""
            SELECT w.workout_id, u.name AS user_name, w.date_logged, e.name AS exercise_name, we.duration
            FROM Workout w
            JOIN Users u ON w.user_id = u.user_id
            JOIN Workout_Exercises we ON w.workout_id = we.workout_id
            JOIN Exercise e ON we.exercise_id = e.exercise_id
            ORDER BY w.date_logged DESC
        """)
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Error fetching workout data: {e}")

# Log Workout
elif menu == "Log Workout":
    st.subheader("📝 Log a New Workout")
    try:
        cur.execute("SELECT user_id, name FROM Users")
        users = {name: uid for uid, name in cur.fetchall()}
        cur.execute("SELECT exercise_id, name FROM Exercise")
        exercises = {name: eid for eid, name in cur.fetchall()}

        with st.form("log_workout_form"):
            user_name = st.selectbox("User", list(users.keys()))
            date = st.date_input("Date")
            exercise_name = st.selectbox("Exercise", list(exercises.keys()))
            duration = st.number_input("Duration (minutes)", min_value=1.0)
            submit = st.form_submit_button("Log Workout")

            if submit:
                uid = users[user_name]
                eid = exercises[exercise_name]
                cur.execute("INSERT INTO Workout (user_id, date_logged) VALUES (:1, :2)", (uid, date))
                cur.execute("SELECT MAX(workout_id) FROM Workout WHERE user_id = :1", (uid,))
                workout_id = cur.fetchone()[0]
                cur.execute("INSERT INTO Workout_Exercises (workout_id, exercise_id, duration) VALUES (:1, :2, :3)", (workout_id, eid, duration))
                conn.commit()
                st.success("✅ Workout logged!")
    except Exception as e:
        st.error(f"❌ Could not log workout: {e}")

# View Meals
elif menu == "View Meals":
    st.subheader("🍽️ Meal Logs")
    try:
        cur.execute("""
            SELECT m.meal_id, u.name AS user_name, m.meal_type, m.date_logged, f.name AS food_name, mi.quantity
            FROM Meals m
            JOIN Users u ON m.user_id = u.user_id
            JOIN Meal_Items mi ON m.meal_id = mi.meal_id
            JOIN Food f ON mi.food_id = f.food_id
            ORDER BY m.date_logged DESC
        """)
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Error fetching meal data: {e}")

# Log Meal
elif menu == "Log Meal":
    st.subheader("📝 Log a New Meal")
    try:
        cur.execute("SELECT user_id, name FROM Users")
        users = {name: uid for uid, name in cur.fetchall()}
        cur.execute("SELECT food_id, name FROM Food")
        foods = {name: fid for fid, name in cur.fetchall()}

        with st.form("log_meal_form"):
            user_name = st.selectbox("User", list(users.keys()))
            date = st.date_input("Date")
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
            food_name = st.selectbox("Food", list(foods.keys()))
            quantity = st.number_input("Quantity", min_value=0.1)
            submit = st.form_submit_button("Log Meal")

            if submit:
                uid = users[user_name]
                fid = foods[food_name]
                cur.execute("INSERT INTO Meals (user_id, meal_type, date_logged) VALUES (:1, :2, :3)", (uid, meal_type, date))
                cur.execute("SELECT MAX(meal_id) FROM Meals WHERE user_id = :1", (uid,))
                meal_id = cur.fetchone()[0]
                cur.execute("INSERT INTO Meal_Items (meal_id, food_id, quantity) VALUES (:1, :2, :3)", (meal_id, fid, quantity))
                conn.commit()
                st.success("✅ Meal logged!")
    except Exception as e:
        st.error(f"❌ Could not log meal: {e}")

# Goal Check
elif menu == "Goal Check":
    st.subheader("🎯 Check Progress Towards Goal")
    try:
        cur.execute("SELECT user_id, name, goal FROM Users")
        user_data = cur.fetchall()
        user_dict = {name: (uid, goal) for uid, name, goal in user_data}

        user_name = st.selectbox("Select User", list(user_dict.keys()))
        uid, goal = user_dict[user_name]

        st.markdown(f"**Goal:** {goal}")

        # Total calories consumed
        cur.execute("""
            SELECT COALESCE(SUM(f.calories * mi.quantity), 0)
            FROM Meals m
            JOIN Meal_Items mi ON m.meal_id = mi.meal_id
            JOIN Food f ON mi.food_id = f.food_id
            WHERE m.user_id = :1
        """, (uid,))
        calories_in = cur.fetchone()[0]

        # Total calories burned
        cur.execute("""
            SELECT COALESCE(SUM(we.duration * e.calories_burned / 60), 0)
            FROM Workout w
            JOIN Workout_Exercises we ON w.workout_id = we.workout_id
            JOIN Exercise e ON we.exercise_id = e.exercise_id
            WHERE w.user_id = :1
        """, (uid,))
        calories_out = cur.fetchone()[0]

        net = calories_in - calories_out

        st.markdown(f"📥 **Calories Consumed:** {calories_in:.2f}")
        st.markdown(f"🔥 **Calories Burned:** {calories_out:.2f}")
        st.markdown(f"🧮 **Net Calories:** {net:.2f}")

        if goal == "Lose Weight":
            if net < 1500:
                st.success("✅ On track for weight loss!")
            else:
                st.warning("⚠️ Too many net calories for weight loss.")
        elif goal == "Gain Muscle":
            if net > 2500:
                st.success("✅ On track for muscle gain!")
            else:
                st.warning("⚠️ Increase calorie intake for gaining muscle.")
        else:
            if 1800 <= net <= 2200:
                st.success("✅ Maintaining well!")
            else:
                st.warning("⚠️ Your intake isn't aligned with maintenance.")

    except Exception as e:
        st.error(f"❌ Could not fetch goal data: {e}")
