# Telegram Bot Usage Guide

Based on the examination of the codebase, here’s a comprehensive guide on how to run the bot, pre-deployment considerations, and general guidance:

**I. How to Run the Bot (Recommended: Docker)**

The project is set up to be run using Docker and Docker Compose, which is the recommended approach as it handles dependencies and the environment consistently.

1.  **Prerequisites:**
    *   Install Docker: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
    *   Install Docker Compose: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

2.  **Configuration (`.env` file):**
    *   Create a file named `.env` in the root directory of the project.
    *   Add the following environment variables to it, replacing the placeholder values with your actual data:
        ```env
        API_TOKEN_PROD=YOUR_PRODUCTION_TELEGRAM_BOT_TOKEN
        API_TOKEN_TEST=YOUR_TEST_TELEGRAM_BOT_TOKEN
        CHANNEL_ID=YOUR_TELEGRAM_CHANNEL_ID
        # Example: CHANNEL_ID=-1001234567890
        ```
        *   `API_TOKEN_PROD`: Your main Telegram Bot's API token. The bot currently uses this token by default.
        *   `API_TOKEN_TEST`: A Telegram Bot API token for testing purposes (optional, but good practice).
        *   `CHANNEL_ID`: The ID of the Telegram channel where the bot will send general notifications (e.g., yearly score resets). This ID must be a number.

3.  **Running with Docker Compose:**
    *   The `docker-compose.yml` is configured to use a pre-built image: `image: heistcat/kosa_process:1.0`.
    *   **Option A: Using the Pre-built Image (If it exists and is up-to-date)**
        *   Open your terminal in the project's root directory.
        *   Run the command:
            ```bash
            docker-compose up -d
            ```
            The `-d` flag runs the container in detached mode (in the background).
        *   To view logs: `docker-compose logs -f app`
        *   To stop: `docker-compose down`

    *   **Option B: Building and Using a Local Image (If you've made code changes or the pre-built image is not suitable)**
        *   You'll need to modify the `docker-compose.yml` file. Change the `app` service definition from:
            ```yaml
            services:
              app:
                image: heistcat/kosa_process:1.0
                # ... other settings
            ```
            to:
            ```yaml
            services:
              app:
                build: .  # Tells Docker Compose to build from the Dockerfile in the current directory
                # ... other settings
            ```
        *   Then, build and run:
            ```bash
            docker-compose up --build -d
            ```
        *   Subsequent runs (without code changes needing a rebuild) can use `docker-compose up -d`.

4.  **Database Persistence:**
    *   The `docker-compose.yml` defines a volume `bot_db` which maps to `/app/database/` inside the container. This means your SQLite database (`database.db`) will be stored in this Docker volume and will persist even if you stop and remove the container (as long as you don't delete the volume itself).

**II. How to Run the Bot (Locally, without Docker - for development/testing)**

1.  **Prerequisites:**
    *   Python 3.11 (as specified in `Dockerfile` and `start.sh`). You might need to install it if you don't have it.
    *   `pip` (Python package installer).

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration (`.env` file):**
    *   Ensure the `.env` file (as described in the Docker section) is present in the root directory.

5.  **Run the Bot:**
    *   You can use the provided shell script:
        ```bash
        bash start.sh
        ```
    *   Or run directly:
        ```bash
        python3.11 bot.py
        ```

**III. Pre-Deployment Commands/Considerations**

*   **Environment Configuration (`.env`):** This is the most crucial pre-deployment step. Ensure `API_TOKEN_PROD` and `CHANNEL_ID` are correctly set for your production environment.
*   **Database:**
    *   If deploying for the first time, the bot will create `database/database.db` and set up default tariffs.
    *   If migrating an existing database, ensure the `database.db` file is placed in the correct location (`database/` directory for local runs, or managed by the Docker volume for Docker deployments).
*   **Building Docker Image (if not using a pre-built one):** If you're deploying with Docker and made changes, you'll need to rebuild the image (e.g., `docker-compose build app` or `docker build -t your-image-name .`).
*   **Timezone:** The bot sets its timezone to `Etc/GMT-5`. If your users or tasks operate in a different primary timezone, you might consider if this needs adjustment or if all times should be handled in UTC and converted at the display layer (though `Etc/GMT-5` is a fixed offset zone).
*   **FSM Storage:** The bot uses `MemoryStorage`. This means any active conversations or states users are in will be lost if the bot restarts. For a production environment where state persistence is critical (e.g., multi-step forms), consider switching to a persistent storage backend like `RedisStorage` or `MongoStorage` provided by Aiogram. This would require adding the respective library (e.g., `redis`) to `requirements.txt` and updating the `Dispatcher` initialization in `bot.py`.

**IV. How to Use the Code (General Guidance)**

*   **Project Structure:**
    *   `bot.py`: Main entry point, initializes the bot, dispatcher, database, and background tasks.
    *   `database.py`: Contains the `Database` class for all SQLite interactions (schema, queries).
    *   `handlers/`: Directory for Aiogram handlers.
        *   `common.py`: Handlers for common user commands (e.g., `/start`).
        *   `admin.py`: Handlers for admin-specific commands.
        *   `executor.py`: Handlers for users designated as "executors" (likely those performing tasks).
    *   `keyboards/`: Directory for Aiogram inline and reply keyboards.
        *   `inline.py`: Functions to generate inline keyboards.
        *   `reply.py`: Functions to generate reply keyboards.
    *   `utils.py`: Utility functions (e.g., `send_channel_message`).
    *   `requirements.txt`: Python dependencies.
    *   `Dockerfile`: Instructions to build the Docker image.
    *   `docker-compose.yml`: Defines how to run the application using Docker Compose.
    *   `.env`: For environment variables (API tokens, channel ID). **This file should be in `.gitignore` and not committed to version control.**
    *   `start.sh`: Simple script to run `bot.py` locally.

*   **Adding Features:**
    1.  **Define Handlers:** If adding new commands or interactions, you'll likely add new functions in the appropriate file within the `handlers/` directory. Register these handlers with a router.
    2.  **Update Keyboards (if needed):** If new interactions require new buttons, modify or add functions in `keyboards/`.
    3.  **Database Changes (if needed):** If the feature requires storing new data, update `database.py` with new table structures or queries. Be mindful of database migrations if you have existing data.
    4.  **Configuration (if needed):** If new settings are required, consider adding them to the `.env` file and loading them in `bot.py` or relevant modules.

*   **Background Tasks:**
    *   `check_deadlines` in `bot.py` is responsible for sending task reminders. You can adjust its timing or logic there.
    *   `reset_scores_yearly` in `bot.py` handles the annual score reset.

*   **Error Handling:** The `check_deadlines` function has basic `try-except` blocks for sending messages. Robust error handling and logging would be beneficial for a production bot.

*   **Dependencies:** Manage Python dependencies in `requirements.txt`. After adding a new library, run `pip freeze > requirements.txt` (within your virtual environment) to update it.

This guidance should provide a solid starting point for running, deploying, and understanding the bot.
