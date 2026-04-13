"use client";
import { WS_BASE_URL, WS_ENDPOINTS, API_BASE_URL, API_ENDPOINTS } from "../../config/api";
import React, { useEffect, useState } from "react";

/* =========================
   Types
========================= */

type Config = {
  db: {
    engine: string;
    file: string;
  };
  port: {
    "back-end": string;
    "interface-manager": string;
  };
};

/* =========================
   Component
========================= */

const DevConfigPage: React.FC = () => {
  const [config, setConfig] = useState<Config | null>(null);

  /* =========================
     Fetch config on load
  ========================= */

  useEffect(() => {
    fetch(`${API_ENDPOINTS.DEV_Config}`)
      .then((res) => res.json())
      .then((data: Config) => setConfig(data));
  }, []);

  /* =========================
     Generic change handler
  ========================= */

  const handleChange = (
    section: keyof Config,
    key: string,
    value: string
  ) => {
    if (!config) return;

    setConfig({
      ...config,
      [section]: {
        ...config[section],
        [key]: value,
      },
    });
  };

  /* =========================
     Submit
  ========================= */

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await fetch(API_ENDPOINTS.DEV_Config, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });

    alert("Config saved");
  };

  if (!config) return <p>Loading...</p>;

  return (
    <div className="container mt-4">
      <h3>Dev Configuration</h3>

      <form onSubmit={handleSubmit}>
        {/* ================= Database ================= */}
        <h5 className="mt-4">Database</h5>

        <div className="mb-3">
          <label className="form-label">Engine</label>
          <input
            className="form-control"
            value={config.db.engine}
            onChange={(e) =>
              handleChange("db", "engine", e.target.value)
            }
          />
        </div>

        <div className="mb-3">
          <label className="form-label">File</label>
          <input
            className="form-control"
            value={config.db.file}
            onChange={(e) =>
              handleChange("db", "file", e.target.value)
            }
          />
        </div>

        {/* ================= Ports ================= */}
        <h5 className="mt-4">Ports</h5>

        <div className="mb-3">
          <label className="form-label">Back-end</label>
          <input
            className="form-control"
            value={config.port["back-end"]}
            onChange={(e) =>
              handleChange("port", "back-end", e.target.value)
            }
          />
        </div>

        {/* <div className="mb-3">
          <label className="form-label">Interface Manager</label>
          <input
            className="form-control"
            value={config.port["interface-manager"]}
            onChange={(e) =>
              handleChange(
                "port",
                "interface-manager",
                e.target.value
              )
            }
          />
        </div> */}

        <button type="submit" className="btn btn-primary">
          Save
        </button>
      </form>
    </div>
  );
};

export default DevConfigPage;
