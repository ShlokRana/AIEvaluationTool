import React, { useEffect } from "react";
import { getLoginUrl } from "../../utils/auth";

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = () => {
  useEffect(() => {
    // Pass the current origin as return URL so auth service knows where to redirect back
    const returnUrl = `${window.location.origin}/`;
    const loginUrl = getLoginUrl(returnUrl);
    window.location.href = loginUrl;
  }, []);

  return (
    <div className="login-page">
      <div className="login-form">
        <h2>Redirecting to centralized login...</h2>
        <p>Please sign in using the shared authentication portal.</p>
      </div>
    </div>
  );
};

export default LoginPage;
