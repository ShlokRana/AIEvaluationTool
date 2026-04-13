import React from "react";
import "./Header.css";
import AppButton from "../common/Button/AppButton";
import { useNavigate } from "react-router-dom";
import testRun from "../../../src/assets/logo/Test-run.png"

const Header: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <div className="header-container">  
      <div className="header-content">
        <div className="header-left">
          <img src={testRun} alt="" />
          <h1 className="page-title">Test Runs</h1>
        </div>
        <div className="header-right">
          <AppButton
            label="New Test Run"
            variant="primary"
            icon="bi-plus-lg"
            size="md"
            className="new-test-run-btn"
            onClick={() => navigate('/create-test-run')}
          />
        </div>
      </div>
    </div>
  );
};

export default Header;
