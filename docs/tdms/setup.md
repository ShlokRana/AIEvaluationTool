# TDMS Setup

Use this page to set up the TDMS backend and frontend locally.

TDMS provides the web-based interface for managing evaluation data, testcases, prompts, and related metadata. The setup is split into two parts: the backend service and the frontend application.

## Backend Setup

Update `src/app/TDMS/back-end/database/config.json` based on the database you want to use.

SQLite example:

```json
{
  "db": {
    "engine_type": "sqlite",
    "file": "TDMS.db"
  }
}
```

MariaDB example:

```json
{
  "db": {
    "engine_type": "mariadb",
    "host": "localhost",
    "port": 3306,
    "user": "your_username",
    "password": "your_password",
    "database": "tdms_db"
  }
}
```

Start the backend:

```bash
cd src/app/TDMS/back-end
source venv/bin/activate
python main.py
```

The backend typically starts on `http://localhost:8000`.

![TDMS backend running](../../screenshots/backEnd.png)

## Frontend Setup

Install dependencies and start the frontend:

```bash
cd src/app/TDMS/front-end
npm install
npm run dev
```

Open the frontend URL shown in the terminal after startup.

The frontend typically starts on `http://localhost:8080`, or another port if `8080` is already in use.

![TDMS frontend running](../../screenshots/frontEnd.png)

## Access The Application

After both services are running:

- Open your browser.
- Navigate to the frontend URL shown in the terminal.
- Confirm that the TDMS login or landing page is visible.

![TDMS home page](../../screenshots/tdms_home.png)
