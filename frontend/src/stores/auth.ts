import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { authApi } from "@/services/api";
import type { User } from "@/types/auth";

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref<string | null>(null);
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value));

  function persistToken(token: string | null): void {
    accessToken.value = token;
    authApi.setAccessToken?.(token);
  }

  async function login(email: string, password: string): Promise<void> {
    const response = await authApi.login(email, password);
    persistToken(response.access_token);
    user.value = response.user;
  }

  async function restore(): Promise<void> {
    try {
      if (accessToken.value) {
        user.value = await authApi.me(accessToken.value);
        return;
      }
      const response = await authApi.refresh();
      persistToken(response.access_token);
      user.value = response.user;
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
