# AI Fitness Coach 🏋️

## Overview

The AI Fitness Coach is a Streamlit web application designed to be your personal AI partner for evidence-informed fitness and nutrition guidance. It leverages the power of Large Language Models (LLMs) via the Groq API to provide tailored advice, generate workout schedules, and help you track your fitness journey. Users can create multiple profiles, each with personalized goals, biometrics, and preferences, allowing for a customized experience.

## Features

*   **Profile Management:**
    *   Create, select, update, and delete user profiles.
    *   Store individual details per profile:
        *   Fitness goals (e.g., weight loss, muscle gain)
        *   Experience level (Beginner, Intermediate, Advanced)
        *   Biometrics (age, sex, height, weight)
        *   Activity level
        *   Dietary preferences/notes
        *   Available equipment
        *   General notes
*   **AI-Powered Chat Interface:**
    *   Engage in conversations with an AI Fitness Coach (powered by Groq - `meta-llama/llama-4-maverick-17b-128e-instruct`).
    *   Receive guidance on:
        *   Proper exercise form and common mistakes.
        *   Workout principles and programming (HIIT, LISS, strength, hypertrophy).
        *   Nutrition advice, macronutrients, meal ideas, and hydration.
        *   Motivation, goal setting, and overcoming plateaus.
*   **Personalized 4-Week Fitness Schedule Generation:**
    *   Automatically generates a 4-week fitness schedule based on the active profile's details.
    *   Option to manually regenerate schedule suggestions.
*   **Activity & Biometric Logging:**
    *   Log workouts with specific notes.
    *   Log daily weight (in kg).
    *   Log general notes or observations.
*   **Progress Tracking:**
    *   View recent log entries.
    *   Visualize weight history with an interactive chart.
    *   Calculate and display BMI with category.
*   **Persistent Data Storage:**
    *   Uses SQLite to store profile information, chat history, and log entries.
*   **User-Friendly Interface:**
    *   Built with Streamlit for an interactive and easy-to-navigate web UI.
    *   Responsive design with a sidebar for settings and profile management.

## Technologies Used

*   **Backend:** Python
*   **Web Framework:** Streamlit
*   **AI Integration:** Groq API (with `meta-llama/llama-4-maverick-17b-128e-instruct` model)
*   **Database:** SQLite
*   **Data Handling:** Pandas
*   **Charting:** Altair
*   **Environment Variables:** python-dotenv

## Setup and Installation

Follow these steps to set up and run the AI Fitness Coach locally:

1.  **Prerequisites:**
    *   Python 3.8 or higher.
    *   `pip` (Python package installer).
    *   Git (for cloning the repository).

2.  **Clone the Repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd aifitnessProj # Or your project directory name
    ```

3.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

4.  **Install Dependencies:**
    Install all required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables:**
    The application requires a Groq API key to interact with the AI model.
    *   Create a file named `.env` in the root directory of the project (`aifitnessProj/`).
    *   Add your Groq API key to the `.env` file:
        ```env
        GROQ_API_KEY="your_actual_groq_api_key"
        ```
    *   You can obtain a Groq API key from the [Groq Console](https://console.groq.com/keys).

6.  **Database Initialization:**
    The SQLite database (`fitness_data.db`) and its necessary tables will be automatically created (if they don't exist) when you first run the application, thanks to the `init_db()` function.

## Running the Application

Once the setup is complete, you can run the Streamlit application:

```bash
streamlit run ai_fitness.py
```

This will typically open the application in your default web browser (e.g., at `http://localhost:8501`).

## Usage

### 1. Profile Management

*   **Creating a New Profile:**
    *   In the sidebar, expand the "Create New Profile" section.
    *   Enter a name for the new profile and click "Create Profile".
    *   The new profile will be created and automatically selected. You can then update its details.
*   **Selecting an Active Profile:**
    *   Use the "Active Profile" dropdown in the sidebar to switch between existing profiles.
    *   The chat history, logs, and settings will update to reflect the selected profile.
*   **Updating Profile Settings:**
    *   Once a profile is active, its settings will be displayed in the sidebar under "Settings for '<Profile Name>'".
    *   Modify fields like "Primary Goal," "Experience Level," "Age," "Sex," "Height (cm)," "Weight (kg)," "Activity Level," "Dietary Preferences," "Available Equipment," and "General Notes."
    *   Changes are saved automatically when you interact with other UI elements or when the "Save Profile Details" button (if explicitly added for a save action) is clicked.
*   **Deleting a Profile:**
    *   Expand the "Delete Active Profile" section in the sidebar.
    *   Click the "Delete <Profile Name>" button. A confirmation might be required.
    *   Note: You cannot delete the last remaining profile.

### 2. Interacting with the AI Coach

*   The main area of the application features a chat interface.
*   Type your fitness, nutrition, or motivation-related questions into the input box at the bottom ("Ask about exercise form, healthy meals, motivation...") and press Enter.
*   The AI will respond based on its `SYSTEM_PROMPT` and the context of your current profile (if applicable to the query).
*   Chat history is saved and loaded per profile.

### 3. Logging Activities and Weigh-ins

*   Below the main chat interface, find the "📝 Log Activity / Weigh-in" section.
*   **Log Type:** Choose "Workout," "Weight," or "General Note."
*   **Notes:** Enter details about your workout, any specific observations, or general thoughts.
*   **Weight (kg):** If logging a "Weight" entry, provide your current weight. This field is hidden for other log types.
*   Click "Log Entry" to save the record.

### 4. Viewing Progress

*   **Recent Logs:** The "Recent Activity & Notes" section displays your latest log entries for the active profile.
*   **Weight Chart:** The "Weight Progress (kg)" section shows an interactive line chart of your logged weights over time for the active profile.
*   **BMI:** If height and weight are provided in the profile, your BMI will be calculated and displayed in the "Biometrics" section of the sidebar.

### 5. Generating Fitness Schedules

*   The application can generate a 4-week fitness schedule tailored to your profile. This may happen automatically upon profile creation/update or by clicking the "🔄 Regenerate Schedule Suggestion" button in the sidebar.
*   The generated schedule will appear as a message from the AI in the chat interface.

## Database

*   The application uses an SQLite database named `fitness_data.db` stored in the project's root directory.
*   This database stores:
    *   `profiles`: User profile information (ID, name, goals, biometrics, preferences, etc.).
    *   `chat_history`: Messages exchanged with the AI coach, linked to specific profiles.
    *   `logs`: Workout, weight, and general note entries, linked to specific profiles.
*   The database is automatically initialized if it doesn't exist on startup.

## AI Integration

*   The AI coaching capabilities are provided by the Groq API, utilizing the `meta-llama/llama-4-maverick-17b-128e-instruct` model (or as configured in `GROQ_MODEL`).
*   A detailed `SYSTEM_PROMPT` (defined in `ai_fitness.py`) guides the AI's persona, capabilities, and response style, ensuring it acts as a knowledgeable, encouraging, and safe fitness coach.
*   The Groq client is cached for efficiency.

## Project Structure

```
aifitnessProj/
├── .env                  # For environment variables (user-created)
├── ai_fitness.py         # Main Streamlit application script
├── fitness_data.db       # SQLite database (auto-created)
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── env/                  # Virtual environment directory (if created as per instructions)
```

## Future Enhancements (Ideas)

*   More detailed analytics and visualizations of workout data.
*   Direct integration with fitness trackers or health apps.
*   User authentication for enhanced privacy if deployed publicly.
*   More granular exercise library with video demonstrations.
*   Advanced periodization options for workout plans.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue or submit a pull request.

---

*Let's get started on your fitness journey!* 💪
