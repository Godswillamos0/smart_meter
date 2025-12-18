# Smart Meter Monitoring System

This project is a backend application built with **FastAPI** designed to monitor smart meter data in real-time. It interfaces with ESP32 hardware to collect electrical metrics (Voltage, Current, Power, Energy) and broadcasts them to connected clients via **WebSockets**.

## Features

- **Real-time Data Streaming**: Uses WebSockets to push live updates to frontend clients immediately when data is received.
- **Historical Data Storage**: Persists meter readings and device information using SQLite (via SQLAlchemy).
- **Connection Management**: Efficiently handles multiple WebSocket connections per meter ID.
- **Initial State Sync**: Automatically sends the latest recorded reading to a client upon connection.

## Project Structure

```
smart meter/
├── app/
│   ├── database.py    # Database configuration (SQLite)
│   ├── main.py        # FastAPI app, WebSocket endpoints, and Connection Manager
│   ├── models.py      # SQLAlchemy database models
│   └── routers/
│       └── esp32.py   # Routes for handling incoming data from ESP32 devices
└── README.md
```

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Server**: Uvicorn

## Installation

1.  **Clone the repository** and navigate to the project folder.

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install fastapi uvicorn sqlalchemy
    ```

## Usage

1.  **Run the server**:
    Navigate to the `app` directory (or run from root adjusting the path) and start the Uvicorn server.
    ```bash
    cd app
    uvicorn main:app --reload
    ```
    The server will start at `http://127.0.0.1:8000`.

2.  **Database Creation**:
    The application automatically creates the `data.db` SQLite file and necessary tables (`smart_meter`, `meter_readings`) on the first run.

## API Endpoints

### WebSocket Endpoint

-   **URL**: `ws://127.0.0.1:8000/ws/{meter_id}`
-   **Description**: Establishes a persistent connection for a specific meter.
-   **Behavior**:
    1.  **On Connect**: The server queries the database for the most recent reading of the given `meter_id` and sends it to the client immediately.
    2.  **Live Updates**: The server keeps the connection open. When the ESP32 router receives new data, it uses the `ConnectionManager` to broadcast the new JSON payload to all clients subscribed to that `meter_id`.

### ESP32 Integration

The application includes an `esp32` router (imported in `main.py`). This router is responsible for receiving POST requests from the hardware devices, saving the data to the database, and triggering the WebSocket broadcast.

## License

This project is open source.