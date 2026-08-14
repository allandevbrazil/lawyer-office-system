import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { authApi } from "@/services/api";
import type { User } from "@/types/auth";

const tokenStorageKey = "lawfirm.access_token";

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref<string | null>(localStorage.getItem(tokenStorageKey));
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value));

  function persistToken(token: string | null): void {
    accessToken.value = token;
    if (token) localStorage.setItem(tokenStorageKey, token);
    else localStorage.removeItem(tokenStorageKey);
  }

  async function login(email: string, password: string): Promise<void> {
    const response = await authApi.login(email, password);
    persistToken(response.access_token);
    user.value = response.user;
  }

  async function restore(): Promise<void> {
    if (!accessToken.value) return;
    try {
      user.value = await authApi.me(accessToken.value);
    } catch {
      try {
        const response = await authApi.refresh();
        persistToken(response.access_token);
        user.value = response.user;
      } catch {
        persistToken(null);
        user.value = null;
      }
    }
  }

  async function logout(): Promise<void> {
    await authApi.logout();
    persistToken(null);
    user.value = null;
  }

  return { accessToken, user, isAuthenticated, login, restore, logout };
});
