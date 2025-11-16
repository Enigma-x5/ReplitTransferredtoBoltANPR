const TOKEN_KEY = 'anpr_auth_token';
const USER_KEY = 'anpr_user_info';

export const tokenStorage = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },

  clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  getUserInfo(): { email?: string; role?: 'admin' | 'clerk' } | null {
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  setUserInfo(info: { email?: string; role?: 'admin' | 'clerk' }): void {
    localStorage.setItem(USER_KEY, JSON.stringify(info));
  },
};
