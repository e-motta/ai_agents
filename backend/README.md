# backend/README.md

# Backend Documentation

This directory contains the FastAPI backend for the agents application.

## Setup Instructions

1. **Clone the repository:**

   ```
   git clone <repository-url>
   cd backend
   ```

2. **Create a virtual environment (optional but recommended):**

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**

   ```
   pip install -r requirements.txt
   ```

4. **Run the FastAPI application:**

   ```
   uvicorn app.main:app --reload
   ```

5. **Access the API:**
   Open your browser and navigate to `http://127.0.0.1:8000/` to see the "Hello, World!" message.

## API Endpoints

- `GET /`: Returns a simple greeting message.

## Additional Information

For more details on FastAPI, visit the [FastAPI documentation](https://fastapi.tiangolo.com/).
