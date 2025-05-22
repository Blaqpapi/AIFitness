import streamlit as st
import os
import time
import random
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq, GroqError
import pandas as pd # Add pandas import for charting

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
PAGE_TITLE = "AI Fitness Coach"
PAGE_ICON = "🏋️"
GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct" # Or choose another model like mixtral-8x7b-32768

# --- Database Configuration ---
DB_FILE = "fitness_data.db"

# --- Database Functions ---
def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # User Profile Table - Added profile_notes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT UNIQUE NOT NULL,
                fitness_goal TEXT DEFAULT 'General Fitness',
                experience_level TEXT DEFAULT 'Beginner',
                age INTEGER DEFAULT NULL,
                sex TEXT DEFAULT NULL,
                height_cm REAL DEFAULT NULL,
                weight_kg REAL DEFAULT NULL,
                activity_level TEXT DEFAULT NULL,
                dietary_prefs TEXT DEFAULT NULL,
                equipment TEXT DEFAULT NULL,
                profile_notes TEXT DEFAULT NULL  -- Added
            )
        ''')
        # Chat History Table with Foreign Key to user_profile
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES user_profile (id) ON DELETE CASCADE
            )
        ''')
        # Workout Log Table - NEW
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                log_type TEXT NOT NULL, -- e.g., 'Workout', 'Weight', 'Note'
                notes TEXT,
                weight_kg REAL DEFAULT NULL, -- Optional: Log weight with notes
                FOREIGN KEY (profile_id) REFERENCES user_profile (id) ON DELETE CASCADE
            )
        ''')
        # Indices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_id_chat ON chat_history (profile_id)') # Renamed index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_id_log ON workout_log (profile_id)') # New index
        # Ensure at least one profile exists (e.g., "Default")
        cursor.execute("INSERT OR IGNORE INTO user_profile (profile_name) VALUES ('Default')")

def get_all_profiles():
    """Retrieves all profiles (id, name) from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, profile_name FROM user_profile ORDER BY profile_name ASC')
        profiles = cursor.fetchall()
    return profiles

def get_profile_details(profile_id):
    """Loads all details for a specific profile."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Select all relevant columns including profile_notes
        cursor.execute('''SELECT
                          fitness_goal, experience_level, age, sex,
                          height_cm, weight_kg, activity_level,
                          dietary_prefs, equipment, profile_notes
                       FROM user_profile WHERE id = ?''',
                       (profile_id,))
        profile = cursor.fetchone()
    # Return defaults if profile not found or specific fields are missing
    if profile:
        return profile
    else:
        # Return tuple with defaults matching the SELECT order
        return ('General Fitness', 'Beginner', None, None, None, None, None, None, None, None)

def create_profile(profile_name):
    """Creates a new profile. Returns the new profile ID on success, None on failure."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO user_profile (profile_name) VALUES (?)', (profile_name,))
            new_id = cursor.lastrowid # Get the ID of the inserted row
        return new_id
    except sqlite3.IntegrityError:
        print(f"Profile name '{profile_name}' already exists.")
        return None
    except Exception as e:
        print(f"Error creating profile: {e}")
        return None

def update_profile(profile_id, goal, experience, age, sex, height, weight, activity, diet, equip, notes):
    """Updates all details for a specific profile."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE user_profile SET
                              fitness_goal = ?, experience_level = ?, age = ?, sex = ?,
                              height_cm = ?, weight_kg = ?, activity_level = ?,
                              dietary_prefs = ?, equipment = ?, profile_notes = ?
                           WHERE id = ?''',
                           (goal, experience, age, sex, height, weight, activity, diet, equip, notes, profile_id))
        return True
    except Exception as e:
        print(f"Error updating profile {profile_id}: {e}")
        return False

def delete_profile(profile_id):
    """Deletes a profile and its associated chat history."""
    profiles = get_all_profiles()
    if len(profiles) <= 1:
        st.error("Cannot delete the last profile.")
        return False
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_profile WHERE id = ?', (profile_id,))
        return True
    except Exception as e:
        print(f"Error deleting profile {profile_id}: {e}")
        return False

def load_chat_history(profile_id):
    """Loads chat history for a specific profile."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role, content FROM chat_history WHERE profile_id = ? ORDER BY timestamp ASC', (profile_id,))
            history = cursor.fetchall()
        return [{"role": role, "content": content} for role, content in history]
    except Exception as e:
        print(f"Error loading chat history for profile {profile_id}: {e}")
        return [] # Return empty list on error

def save_chat_message(profile_id, role, content):
    """Saves a chat message associated with a specific profile."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO chat_history (profile_id, role, content) VALUES (?, ?, ?)', (profile_id, role, content))
        return True
    except Exception as e:
        print(f"Error saving chat message for profile {profile_id}: {e}")
        return False

def clear_profile_history(profile_id):
    """Clears chat history for a specific profile."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE profile_id = ?', (profile_id,))
        return True
    except Exception as e:
        print(f"Error clearing history for profile {profile_id}: {e}")
        return False

# --- NEW DB Functions for Logging ---
def log_entry(profile_id, log_type, notes, weight_kg=None):
    """Logs a workout, weight, or general note."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO workout_log
                              (profile_id, log_type, notes, weight_kg)
                              VALUES (?, ?, ?, ?)''',
                           (profile_id, log_type, notes, weight_kg))
        return True
    except Exception as e:
        print(f"Error logging entry for profile {profile_id}: {e}")
        return False

def get_recent_logs(profile_id, limit=10):
    """Retrieves the most recent log entries for a profile."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Fetch timestamp, type, notes, weight
            cursor.execute('''SELECT timestamp, log_type, notes, weight_kg
                              FROM workout_log
                              WHERE profile_id = ?
                              ORDER BY timestamp DESC LIMIT ?''',
                           (profile_id, limit))
            logs = cursor.fetchall()
        return logs # List of tuples
    except Exception as e:
        print(f"Error getting recent logs for profile {profile_id}: {e}")
        return []

def get_weight_history(profile_id):
    """Retrieves weight history (timestamp, weight) for plotting."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT timestamp, weight_kg
                              FROM workout_log
                              WHERE profile_id = ? AND weight_kg IS NOT NULL
                              ORDER BY timestamp ASC''',
                           (profile_id,))
            history = cursor.fetchall()
        # Convert to format suitable for st.line_chart (requires pandas or dict)
        # Using dict for simplicity here
        return {datetime.strptime(ts, '%Y-%m-%d %H:%M:%S'): w for ts, w in history}
    except Exception as e:
        print(f"Error getting weight history for profile {profile_id}: {e}")
        return {}

# --- AI Schedule Generation --- NEW FUNCTION ---
def generate_and_save_schedule(profile_id):
    """Generates a 4-week fitness schedule based on profile details and saves it."""
    print(f"Attempting to generate schedule for profile_id: {profile_id}")
    try:
        # 1. Get profile details (including notes)
        details = get_profile_details(profile_id)
        if not details:
            st.error(f"Could not retrieve details for profile {profile_id} to generate schedule.")
            return False

        (goal, experience, age, sex, height, weight, activity, diet, equip, notes) = details # Unpack notes

        # 2. Construct the prompt - Ask for Markdown structure
        schedule_prompt = f"""Create a detailed 4-week fitness schedule tailored for a user with the following profile:
        - Goal: {goal}
        - Experience Level: {experience}
        - Age: {age if age else 'Not specified'}
        - Sex: {sex if sex else 'Not specified'}
        - Activity Level: {activity if activity else 'Not specified'}
        - Available Equipment: {equip if equip else 'Basic bodyweight/home equipment'}
        - General Notes: {notes if notes else 'None'}

        **IMPORTANT:** Structure the output using Markdown. Use level 2 headings (##) for each week (e.g., `## Week 1`). Use level 3 headings (###) for each day within the week (e.g., `### Monday - Workout A`, `### Tuesday - Rest`). Use bullet points for exercises, sets, reps, and rest periods. Include brief 'Warm-up' and 'Cool-down' sections for workout days. Ensure the plan aligns with the user's goal and experience level.
        """

        # 3. Call Groq API (non-streaming)
        if not client:
            st.error("Groq client not initialized.")
            return False

        print(f"Sending schedule generation request for profile {profile_id}...")
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates fitness schedules formatted in Markdown."}, # Updated system role
                {"role": "user", "content": schedule_prompt}
            ],
            temperature=0.7,
            max_tokens=2000, # Increased max_tokens slightly for potentially longer schedules
            top_p=1,
            stream=False,
        )

        schedule_content = completion.choices[0].message.content
        print(f"Schedule content received for profile {profile_id}.")

        # 4. Save the schedule message
        # Add a clear identifier for parsing later
        schedule_message = f"""**📅 Here is a sample 4-week schedule based on your profile:**
[SCHEDULE_START]
{schedule_content}
[SCHEDULE_END]"""
        if save_chat_message(profile_id, "assistant", schedule_message):
            print(f"Schedule saved successfully for profile {profile_id}.")
            return True
        else:
            st.error("Failed to save the generated schedule message.")
            return False

    except GroqError as e:
        print(f"Groq API error during schedule generation: {e}")
        st.error(f"API Error generating schedule: {e.message}")
        return False
    except Exception as e:
        print(f"Error in generate_and_save_schedule: {e}")
        st.error(f"An unexpected error occurred while generating the schedule.")
        return False


# --- Initialize Database ---
init_db()

# --- Load Initial Data (Profiles) ---
# Load all profiles for the selection dropdown
all_profiles_list = get_all_profiles() # List of (id, name) tuples
profile_dict = dict(all_profiles_list) # {id: name}
profile_names = [name for id, name in all_profiles_list] # Just names for selectbox

# --- Session State Initialization ---
if 'current_profile_id' not in st.session_state:
    if all_profiles_list:
        st.session_state['current_profile_id'] = all_profiles_list[0][0] # Default to first profile ID
    else:
        # This case shouldn't happen due to init_db ensuring 'Default' profile
        st.error("Error: No profiles found!")
        st.stop()

# Load *all* details for the initially selected profile
current_profile_id = st.session_state['current_profile_id']
(initial_goal, initial_experience, initial_age, initial_sex,
 initial_height, initial_weight, initial_activity,
 initial_diet, initial_equip, initial_notes) = get_profile_details(current_profile_id) # Added initial_notes

# Define options for selectboxes
experience_options = ["Beginner", "Intermediate", "Advanced"]
sex_options = ["Prefer not to say", "Male", "Female", "Other"]
activity_options = ["Sedentary (little to no exercise)",
                    "Lightly Active (light exercise/sports 1-3 days/week)",
                    "Moderately Active (moderate exercise/sports 3-5 days/week)",
                    "Very Active (hard exercise/sports 6-7 days a week)",
                    "Extra Active (very hard exercise/physical job)"]

# Helper function to get index or default
def get_option_index(options, value, default=0):
    try:
        return options.index(value) if value in options else default
    except ValueError:
        return default

initial_experience_index = get_option_index(experience_options, initial_experience)
initial_sex_index = get_option_index(sex_options, initial_sex)
initial_activity_index = get_option_index(activity_options, initial_activity)

# --- Helper function to calculate BMI --- NEW ---
def calculate_bmi(weight_kg, height_cm):
    """Calculates BMI."""
    if not weight_kg or not height_cm or height_cm <= 0 or weight_kg <= 0:
        return None, "Enter valid height and weight"
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 24.9:
        category = "Normal weight"
    elif 25 <= bmi < 29.9:
        category = "Overweight"
    else:
        category = "Obesity"
    return round(bmi, 1), category

# --- Page Config (MUST be the first Streamlit command) ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide", initial_sidebar_state="expanded")

# --- Groq API Setup ---
@st.cache_resource # Cache the client for efficiency
def get_groq_client():
    """Initializes and returns the Groq client, loading API key from .env file."""
    try:
        # Load API key from environment variable (set by python-dotenv)
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            st.error("Groq API key not found. Please ensure it is set in a .env file as GROQ_API_KEY='your_key_here'.")
            st.stop()
        # Removed st.success here for cleaner UI, initialization is implicit
        return Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Groq client: {e}")
        st.stop()

# --- Initialize Groq Client (AFTER set_page_config) ---
client = get_groq_client()

# --- System Prompt ---
SYSTEM_PROMPT = """You are an advanced AI Fitness Coach. Your primary purpose is to provide expert-level, safe, encouraging, and motivating fitness and nutrition guidance based on established principles and general knowledge. **Tailor your advice based on the user's stated goals and experience level provided in their message.**

**Core Capabilities:**

1.  **Exercise Knowledge:**
    *   Explain proper form for a wide range of exercises (strength, cardio, flexibility, bodyweight).
    *   Detail common mistakes and provide actionable tips to correct them.
    *   Suggest exercise modifications or progressions/regressions for different fitness levels (beginner, intermediate, advanced).
    *   Discuss the muscles targeted by specific exercises.
2.  **Workout Principles & Programming:**
    *   Explain fundamental training principles (e.g., Progressive Overload, Specificity, Recovery, FITT Principle).
    *   Discuss different training methodologies and their goals (e.g., HIIT vs. LISS, Strength vs. Hypertrophy, Basic Periodization concepts).
    *   Provide workout structures or exercise combinations for specific goals (e.g., a sample full-body routine, ideas for a cardio session). You can create personalized multi-week plans if requested.
3.  **Nutrition Guidance:**
    *   Offer healthy eating advice aligned with established dietary guidelines.
    *   Explain macronutrients (protein, carbohydrates, fats) and their roles. Discuss micronutrients briefly.
    *   Provide healthy meal/snack ideas and discuss hydration importance.
    *   Explain concepts like calorie balance (calories in vs. calories out) for weight management. Calculate specific calorie/macro targets for users if asked.
4.  **Motivation & Goal Setting:**
    *   Offer encouragement, positive reinforcement, and motivational messages.
    *   Help users understand SMART goal setting principles for fitness.
    *   Provide strategies for overcoming common obstacles like plateaus or lack of motivation.

**Interaction Style & Handling Complexity:**

*   **Persona:** Knowledgeable, highly encouraging, patient, empathetic, and professional yet friendly. Use emojis appropriately to enhance tone (🏋️‍♀️🥗💧💪🧠).
*   **Clarity & Structure:** Use markdown (bolding, lists, headings) extensively for readability. Break down complex topics into logical, easy-to-understand points. Start with a direct answer/summary before elaborating.
*   **Handling Complex Queries:**
    *   If a query is complex (e.g., "Compare HIIT and LISS for fat loss"), provide a balanced comparison, outlining pros and cons, target audience, and context for each. Use clear headings for structure.
    *   If a query is ambiguous or lacks detail (e.g., "Best workout?"), ask clarifying questions (e.g., "What are your fitness goals? What kind of equipment do you have access to? How much time can you dedicate?") before providing examples or creating a plan.
*   **Answering Outside Topics:** If asked about topics outside fitness, nutrition, and motivation, answer them to the best of your ability.

**Example Complex Query Handling:**

*User:* "Should I do keto or low-fat for weight loss?"
*You:* "That's a common question! Both ketogenic ('keto') and low-fat diets can be used for weight loss, primarily because they can help create a calorie deficit, which is the key driver for losing weight. Let's break down the differences, pros, and cons:

**🥑 Ketogenic Diet:**
*   **What it is:** Very low carbohydrate, moderate protein, high fat intake. Forces the body into ketosis, using fat for energy instead of glucose.
*   **Potential Pros:** Can lead to rapid initial weight loss (often water weight), may suppress appetite for some, potential benefits for blood sugar control.
*   **Potential Cons:** Can be restrictive and hard to sustain, potential 'keto flu' side effects initially, requires careful planning to ensure nutrient adequacy, long-term effects still studied.
*   **Requires:** Careful tracking of macronutrients.

**🍎 Low-Fat Diet:**
*   **What it is:** Reduces dietary fat intake, often emphasizing fruits, vegetables, whole grains, and lean protein.
*   **Potential Pros:** Aligns with general heart-healthy eating patterns, often rich in fiber and nutrients, can be less restrictive than keto for some.
*   **Potential Cons:** Fat is essential, so very low-fat isn't ideal; focus should be on *healthy* fats. Processed low-fat foods can sometimes be high in sugar. Effectiveness depends on overall calorie intake.
*   **Requires:** Choosing healthy fat sources and managing overall calories.

**Key Takeaway:** The 'best' diet is one that is sustainable, enjoyable, meets your nutritional needs, and helps you maintain a calorie deficit *consistently*. Effectiveness varies greatly between individuals. You can choose the one that best fits your lifestyle.

Okay, I am ready to assist with your fitness journey! 💪"""

# --- Streamlit UI Configuration ---


# --- Header ---
col1, col2 = st.columns([0.1, 0.9]) # Adjust column ratios for better icon spacing
with col1:
    # Placeholder for an icon - replace URL if needed or use local file with st.image
    st.image("https://img.icons8.com/fluency/96/dumbbell.png", width=60) # Slightly smaller icon
with col2:
    st.title(PAGE_TITLE)
    st.caption(f"Your AI partner for evidence-informed fitness guidance, powered by Groq ({GROQ_MODEL})")

st.divider()


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Profiles & Settings")

    # --- Profile Management ---
    st.subheader("Manage Profiles")

    # Profile Selection Dropdown
    selected_profile_name = st.selectbox(
        "Active Profile",
        profile_names,
        index=profile_names.index(profile_dict[st.session_state['current_profile_id']]), # Set initial selection based on state
        key="profile_select"
    )

    # Update state if selection changes
    selected_profile_id = [id for id, name in all_profiles_list if name == selected_profile_name][0]
    if selected_profile_id != st.session_state['current_profile_id']:
        st.session_state['current_profile_id'] = selected_profile_id
        # Clear chat display and force reload of profile details/history
        st.session_state.messages = [] # Clear message display
        st.rerun() # Rerun to reload data for the new profile

    # Get current profile details for display/update
    current_profile_id = st.session_state['current_profile_id']
    (current_goal, current_experience, current_age, current_sex,
     current_height, current_weight, current_activity,
     current_diet, current_equip, current_notes) = get_profile_details(current_profile_id) # Renamed to current_notes

    # Calculate index for current experience (needed for selectbox default)
    current_experience_index = get_option_index(experience_options, current_experience)
    # Calculate indices for other selectboxes
    current_sex_index = get_option_index(sex_options, current_sex)
    current_activity_index = get_option_index(activity_options, current_activity)

    # Create New Profile Section
    with st.expander("Create New Profile"):
        new_profile_name = st.text_input("New Profile Name", key="new_profile_name_input")
        if st.button("Create Profile"):
            if new_profile_name and new_profile_name.strip():
                new_profile_id = create_profile(new_profile_name.strip())
                if new_profile_id:
                    st.success(f"Profile '{new_profile_name.strip()}' created!")
                    # Optionally, generate and save a default schedule for the new profile
                    if generate_and_save_schedule(new_profile_id):
                        st.success(f"Default schedule generated and saved for '{new_profile_name.strip()}'.")
                    # Clear input and rerun to update profile list
                    st.rerun()
                else:
                    st.error(f"Failed to create profile '{new_profile_name.strip()}'. Name might already exist.")
            else:
                st.warning("Please enter a name for the new profile.")

    # Delete Current Profile Section
    with st.expander("Delete Active Profile"):
        st.warning(f"This will permanently delete the profile '{selected_profile_name}' and all its chat history.")
        if st.button(f"Delete Profile '{selected_profile_name}'", key="delete_profile_btn"):
            if delete_profile(current_profile_id):
                st.success(f"Profile '{selected_profile_name}' deleted.")
                # Reset state to the first available profile
                del st.session_state['current_profile_id']
                st.session_state.messages = []
                st.rerun()
            # Error message handled within delete_profile function if it fails

    st.divider()

    # --- Active Profile Settings ---
    st.subheader(f"Settings for '{selected_profile_name}'")

    # --- Organize Settings into Expanders ---
    with st.expander("Core Info", expanded=True):
        profile_goal = st.text_input(
            "Primary Fitness Goal",
            key=f"fitness_goal_{current_profile_id}",
            value=current_goal
        )
        profile_experience = st.selectbox(
            "Experience Level",
            experience_options,
            key=f"experience_level_{current_profile_id}",
            index=current_experience_index
        )

    with st.expander("Biometrics"):
        profile_age = st.number_input(
            "Age", min_value=10, max_value=120, step=1, # Added min_value validation
            key=f"age_{current_profile_id}",
            value=current_age if current_age is not None else 18 # Default age if None
        )
        profile_sex = st.selectbox(
            "Sex", sex_options, key=f"sex_{current_profile_id}", index=current_sex_index
        )
        profile_height = st.number_input(
            "Height (cm)", min_value=50.0, step=0.1, # Added min_value validation
            key=f"height_{current_profile_id}",
            value=current_height if current_height is not None else 170.0, # Default height
            format="%.1f"
        )
        profile_weight = st.number_input(
            "Weight (kg)", min_value=20.0, step=0.1, # Added min_value validation
            key=f"weight_{current_profile_id}",
            value=current_weight if current_weight is not None else 70.0, # Default weight
            format="%.1f"
        )
        # --- Display BMI ---
        bmi_value, bmi_category = calculate_bmi(profile_weight, profile_height)
        if bmi_value:
            st.metric(label="Calculated BMI", value=f"{bmi_value}", delta=bmi_category, delta_color="off")
        else:
            st.caption(bmi_category) # Show "Enter valid height and weight"

    with st.expander("Preferences & Equipment"):
        profile_activity = st.selectbox(
            "Typical Activity Level", activity_options, key=f"activity_{current_profile_id}", index=current_activity_index
        )
        profile_diet = st.text_area(
            "Dietary Preferences/Restrictions", key=f"diet_{current_profile_id}",
            value=current_diet if current_diet is not None else ""
        )
        profile_equip = st.text_area(
            "Available Equipment", key=f"equip_{current_profile_id}",
            value=current_equip if current_equip is not None else ""
        )
        # --- Add Profile Notes Widget ---
        profile_notes = st.text_area( # Assign to profile_notes
            "General Notes (Injuries, specific preferences, etc.)",
            key=f"notes_{current_profile_id}",
            value=current_notes if current_notes is not None else "" # Use current_notes
        )

    # --- Manual Schedule Generation Button ---
    if st.button("🔄 Regenerate Schedule Suggestion", key=f"regen_schedule_{current_profile_id}"):
        with st.spinner("Generating updated schedule suggestion..."):
            if generate_and_save_schedule(current_profile_id):
                st.success("New schedule suggestion added to chat!")
                st.session_state.messages = [] # Clear current messages in state
                st.rerun() # Rerun to show the new schedule immediately
            else:
                # Error handled within generate_and_save_schedule
                pass # st.error is shown in the function

    # --- Save profile changes if they occur ---
    # Check all fields for changes, including profile_notes
    if (profile_goal != current_goal or
            profile_experience != current_experience or
            profile_age != current_age or
            profile_sex != current_sex or
            profile_height != current_height or
            profile_weight != current_weight or
            profile_activity != current_activity or
            profile_diet != current_diet or
            profile_equip != current_equip or
            profile_notes != current_notes): # Added check for notes

        # --- Input Validation ---
        validation_passed = True
        if not profile_goal.strip():
            st.warning("Fitness Goal cannot be empty.")
            validation_passed = False
        # Add more validation as needed (e.g., check if height/weight are reasonable)

        if validation_passed:
            # Handle potential None values before saving
            save_age = profile_age if profile_age > 0 else None
            save_sex = profile_sex if profile_sex != "Prefer not to say" else None
            save_height = profile_height if profile_height > 0 else None
            save_weight = profile_weight if profile_weight > 0 else None
            save_activity = profile_activity
            save_diet = profile_diet.strip() if profile_diet.strip() else None
            save_equip = profile_equip.strip() if profile_equip.strip() else None
            save_notes = profile_notes.strip() if profile_notes.strip() else None # Save notes

            # Call update_profile with all arguments, including save_notes
            if update_profile(current_profile_id, profile_goal, profile_experience,
                              save_age, save_sex, save_height, save_weight,
                              save_activity, save_diet, save_equip, save_notes): # Pass save_notes
                st.toast("Profile updated!", icon="💾")
                # Update internal state for next comparison
                current_goal, current_experience, current_age, current_sex, \
                current_height, current_weight, current_activity, \
                current_diet, current_equip, current_notes = (profile_goal, profile_experience, # Update current_notes
                                                               save_age, save_sex, save_height, save_weight,
                                                               save_activity, save_diet, save_equip, save_notes)

                # Check if goal, experience, or equipment changed to *suggest* regeneration
                # Removed automatic generation on goal change here, replaced by manual button
                # if profile_goal != current_goal: # Example condition
                #    st.info("Profile updated. Consider regenerating the schedule.")

            else:
                st.error("Failed to update profile in database.")

    st.divider()

    # --- Chat Settings ---
    st.subheader("Chat Settings")
    temperature = st.slider("AI Creativity (Temperature)", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
                            help="Lower values make responses more focused and deterministic. Higher values increase creativity and randomness.",
                            key="temperature_slider") # Temperature is global, not per-profile

    # Clear History for Active Profile
    if st.button(f"🗑️ Clear History for '{selected_profile_name}'", key="clear_profile_chat", type="primary", use_container_width=True):
        if clear_profile_history(current_profile_id):
            # Reset session state messages and add confirmation
            welcome_msg = f"Chat history for '{selected_profile_name}' cleared! How can I help you?"
            st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
            save_chat_message(current_profile_id, "assistant", welcome_msg) # Save clearing message
            st.success(f"Chat history for '{selected_profile_name}' cleared!")
            st.rerun()
        else:
            st.error("Failed to clear history.")

    st.divider()

    with st.expander("ℹ️ About", expanded=False):
        st.markdown(
            "This AI Fitness Coach uses Groq's LPU™ Inference Engine and Large Language Models "
            "to provide fitness and nutrition information."
        )
        st.markdown(f"**Model:** `{GROQ_MODEL}`")
        # Removed st.warning disclaimer block

# --- Main Area Modifications ---

# --- Workout Logging Section --- NEW ---
st.divider()
st.subheader("📝 Log Activity / Weigh-in")
log_col1, log_col2 = st.columns([3, 1])
with log_col1:
    log_note = st.text_area("Log details (workout performed, food notes, etc.)", key="log_note_input", height=100)
    log_weight = st.number_input("Current Weight (kg) (Optional, for weigh-in)", min_value=0.0, step=0.1, format="%.1f", key="log_weight_input")
with log_col2:
    log_type = st.radio("Log Type", ["Workout", "Weigh-in", "Note"], key="log_type_radio", horizontal=True)
    if st.button("💾 Save Log Entry", key="save_log_btn", use_container_width=True):
        if log_note.strip() or (log_type == "Weigh-in" and log_weight > 0):
            save_weight_value = log_weight if log_type == "Weigh-in" and log_weight > 0 else None
            if log_entry(current_profile_id, log_type, log_note.strip(), save_weight_value):
                st.success("Log entry saved!")
                # Clear inputs after saving
                st.session_state.log_note_input = ""
                st.session_state.log_weight_input = 0.0
                st.rerun() # Rerun to update recent logs display
            else:
                st.error("Failed to save log entry.")
        else:
            st.warning("Please enter some notes or a valid weight for weigh-in.")

# --- Display Recent Logs & Weight Chart --- NEW ---
st.divider()
log_disp_col1, log_disp_col2 = st.columns(2)

with log_disp_col1:
    st.subheader("📈 Recent Weight History")
    weight_data = get_weight_history(current_profile_id)
    if weight_data:
        # Prepare data for st.line_chart (needs DataFrame or dict with specific structure)
        # Convert dict to list of dicts for easier pandas conversion if needed
        # For simplicity, let's try directly if st accepts datetime keys (might need pandas)
        try:
            st.line_chart(weight_data)
        except Exception as e:
             # Fallback or use pandas if direct dict fails
             try:
                 import pandas as pd
                 df = pd.DataFrame(list(weight_data.items()), columns=['Timestamp', 'Weight (kg)']).set_index('Timestamp')
                 st.line_chart(df)
             except ImportError:
                 st.warning("Pandas not installed. Cannot display weight chart.")
             except Exception as chart_e:
                 st.error(f"Error displaying weight chart: {chart_e}")

    else:
        st.caption("No weight entries logged yet.")

with log_disp_col2:
    st.subheader("🗓️ Recent Log Entries")
    recent_logs = get_recent_logs(current_profile_id)
    if recent_logs:
        for log_ts, log_t, log_n, log_w in recent_logs:
            ts_obj = datetime.strptime(log_ts, '%Y-%m-%d %H:%M:%S')
            display_ts = ts_obj.strftime('%Y-%m-%d %H:%M') # Format timestamp
            log_header = f"**{log_t}** ({display_ts})"
            if log_t == "Weigh-in" and log_w:
                log_header += f" - {log_w} kg"
            with st.expander(log_header):
                st.markdown(log_n if log_n else "_No details provided._")
    else:
        st.caption("No log entries yet.")


# --- Chat Logic --- #

# Initialize chat history for the *current profile*
if "messages" not in st.session_state or not st.session_state.messages: # Reload if empty (e.g., after profile switch)
    st.session_state.messages = load_chat_history(current_profile_id)
    if not st.session_state.messages:
        welcome_msg = f"Welcome to profile '{profile_dict[current_profile_id]}'! How can I help you today? 💪"
        st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
        # Save welcome message only if history was truly empty
        save_chat_message(current_profile_id, "assistant", welcome_msg)

# Display past messages from st.session_state (for the current profile)
# --- Modify Schedule Display ---
for message in st.session_state.messages:
    avatar = "🏋️‍♀️" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        # Check if message content looks like a generated schedule
        if message["role"] == "assistant" and "sample 4-week schedule" in message["content"] and "---" in message["content"]:
             try:
                 # Attempt to parse and display structured schedule
                 intro, schedule_part = message["content"].split("---\n\n", 1)
                 st.markdown(intro + "---") # Display intro part

                 # Simple parsing based on "Week X" headings
                 weeks = schedule_part.split("Week ")
                 week_tabs = st.tabs([f"Week {i}" for i in range(1, len(weeks))]) # Skip first split part

                 for i, week_content in enumerate(weeks[1:]): # Start from 1
                     with week_tabs[i]:
                         # Further split by days or display raw week content
                         # This part needs refinement based on actual AI output format
                         st.markdown(week_content.strip())

             except Exception as e:
                 print(f"Error parsing schedule: {e}")
                 st.markdown(message["content"]) # Fallback to raw display
        else:
             st.markdown(message["content"]) # Display regular messages

# Handle new user input
if prompt := st.chat_input("Ask about exercise form, healthy meals, motivation..."):
    # Save and display user message for the current profile
    save_chat_message(current_profile_id, "user", prompt) # Save to DB with profile ID
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # --- Prepare message list for Groq API ---
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Load history *from session state* for the API call
    history_to_send = st.session_state.messages[:-1]
    for msg in history_to_send:
        # Exclude potentially very long schedule messages from history sent to API? (Optional)
        # if "sample 4-week schedule" not in msg["content"]:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    # --- Prepend personalization context from the *current profile* ---
    (ctx_goal, ctx_experience, ctx_age, ctx_sex,
     ctx_height, ctx_weight, ctx_activity,
     ctx_diet, ctx_equip, ctx_notes) = get_profile_details(current_profile_id) # Fetch notes too

    # Build a more detailed context string including notes
    context_parts = [
        f"Goal: {ctx_goal}",
        f"Experience: {ctx_experience}"
    ]
    if ctx_age: context_parts.append(f"Age: {ctx_age}")
    if ctx_sex: context_parts.append(f"Sex: {ctx_sex}")
    if ctx_height: context_parts.append(f"Height: {ctx_height} cm")
    if ctx_weight: context_parts.append(f"Weight: {ctx_weight} kg")
    if ctx_activity: context_parts.append(f"Activity Level: {ctx_activity}")
    if ctx_diet: context_parts.append(f"Dietary Notes: {ctx_diet}")
    if ctx_equip: context_parts.append(f"Equipment: {ctx_equip}")
    if ctx_notes: context_parts.append(f"General Notes: {ctx_notes}") # Add notes

    context_string = "; ".join(context_parts)
    contextual_prompt = f"(My Profile: {context_string})\\n\\n{prompt}"

    # Add the current user prompt *with context*
    api_messages.append({"role": "user", "content": contextual_prompt})

    # Display thinking indicator and call Groq API (Streaming)
    with st.chat_message("assistant", avatar="🏋️‍♀️"):
        message_placeholder = st.empty()
        with st.spinner("🧠 Thinking..."):
            full_response = ""
            try:
                start_time = time.time() # Start timer
                streaming_response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=api_messages, # Use the prepared messages with context
                    temperature=st.session_state.get('temperature_slider', 0.7), # Use global temp
                    max_tokens=2000,
                    top_p=1,
                    stream=True,
                )

                # Stream the response chunk by chunk
                response_stream = ""
                for chunk in streaming_response:
                    chunk_content = chunk.choices[0].delta.content
                    if chunk_content:
                        response_stream += chunk_content
                        message_placeholder.markdown(response_stream + "▌") # Simulate typing cursor

                full_response = response_stream # Assign the complete streamed response
                end_time = time.time() # End timer
                # Final display of the full response without cursor
                message_placeholder.markdown(full_response)
                # Display response time in a less obtrusive way
                st.caption(f"Response generated in {end_time - start_time:.2f}s")

            except GroqError as e:
                error_message = f"Groq API Error: {e.status_code} - {e.message}"
                st.error(error_message)
                full_response = f"Sorry, I encountered an API error. Please check the console or logs for details: {e.message}"
                message_placeholder.markdown(full_response)
                print(f"Groq API Error Details: {e}") # Log detailed error
            except Exception as e:
                error_message = f"An unexpected error occurred: {type(e).__name__} - {e}"
                st.error(error_message)
                full_response = f"Sorry, an unexpected error occurred: {e}"
                message_placeholder.markdown(full_response)
                print(f"Unexpected Error Details: {e}") # Log detailed error

    # Add the final assistant response to session state and DB for the current profile
    if full_response and full_response.strip() and not full_response.startswith("Sorry, I encountered an"):
        save_chat_message(current_profile_id, "assistant", full_response) # Save assistant response to DB with profile ID
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    elif not full_response or not full_response.strip(): # Handle cases where the stream might yield nothing
         print("Received empty or whitespace-only response from API.")
         # Optionally add a generic message to state if needed:
         # st.session_state.messages.append({"role": "assistant", "content": "[Received empty response]"})


# --- Footer ---
st.divider()
# Removed the previous footer message
st.markdown("<center><em>Let's get started!</em></center>", unsafe_allow_html=True) # Changed footer message
