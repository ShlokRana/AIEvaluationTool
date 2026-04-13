import { AUTH_PAGE_URL } from "../config/api";

export const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem("access_token");
  return token
    ? {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      }
    : {
        "Content-Type": "application/json",
      };
};

export const clearSession = (): void => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_name");
  localStorage.removeItem("role");
};

export const getLoginUrl = (returnUrl?: string): string => {
  // const target = returnUrl || window.location.href;
  // const encodedTarget = encodeURIComponent(target);
  return `${AUTH_PAGE_URL}`;
};

export const redirectToLogin = (returnUrl?: string): void => {
  clearSession();
  window.location.replace(getLoginUrl(returnUrl));
};
