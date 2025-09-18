# Monorepo Application

This is a monorepo project that contains a FastAPI backend and a React frontend.

## Project Structure

```
monorepo-app
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── __init__.py
│   │   └── api
│   │       └── v1
│   │           └── hello.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── README.md
├── frontend
│   ├── package.json
│   ├── public
│   │   └── index.html
│   └── src
│       ├── index.jsx
│       └── App.jsx
├── .gitignore
└── README.md
```

## Backend Setup

1. Navigate to the `backend` directory:
   ```
   cd backend
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the FastAPI application:
   ```
   uvicorn app.main:app --reload
   ```

4. Access the API at `http://localhost:8000/`.

## Frontend Setup

1. Navigate to the `frontend` directory:
   ```
   cd frontend
   ```

2. Install the required dependencies:
   ```
   npm install
   ```

3. Start the React application:
   ```
   npm start
   ```

4. Access the application at `http://localhost:3000/`.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.