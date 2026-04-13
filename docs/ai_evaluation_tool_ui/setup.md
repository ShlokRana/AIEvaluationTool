# UI Setup

Use this page to start the Test Case Execution Dashboard locally.

The dashboard has two parts:

- a frontend application for interaction and visualization
- a backend service for run management, data access, and execution support

Both services should be running for the full experience.

## Start The Frontend Application

Navigate to the dashboard application directory:

```bash
cd src/app/TestCaseExecutorDashboard
```

Then start the frontend:

```bash
cd front-end
npm install
npm start
```

After the command starts successfully, open the URL shown in the terminal, typically `http://localhost:3000`.

![Dashboard frontend startup](../../screenshots/TRDB_without_back_end.png)

## Start The Backend Application

Start the backend in a separate terminal:

```bash
cd src/app/TestCaseExecutorDashboard/back-end
python main.py
```

If needed, update the backend configuration file so it matches your database and service port settings before starting the service.

## Setup Notes

- ensure required Python and Node.js dependencies are installed
- make sure the backend and frontend can both access the expected database
- if the frontend loads but shows incomplete run data, verify that the backend is running correctly

