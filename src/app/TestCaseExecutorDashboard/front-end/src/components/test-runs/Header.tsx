import React from "react";
import "./Header.css";
import { Play, Plus } from "lucide-react";
import AppButton from "../common/Button/AppButton";
const Header: React.FC = () => {
  return (
    <div className="header">
      <h1>Test Runs</h1>
      
      <div className="header-buttons">
        <AppButton
          label="Continue"
          variant="warning"
          icon="bi-play-fill" // using bootstrap icon class if needed
          size="md"
          
        />

        {/* New Test Run Button */}
        <AppButton
          label="New Test Run"
          variant="primary"
          icon="bi-plus-lg" // using bootstrap icon class if needed
          size="md"
          
        />
      </div>
    </div>
  );
};

export default Header;
