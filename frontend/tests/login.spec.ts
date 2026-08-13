import { createPinia } from "pinia";
import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";

import LoginView from "@/views/LoginView.vue";

vi.mock("@/services/api", () => ({
  authApi: {
    login: vi.fn().mockResolvedValue({
      access_token: "test-access-token",
      token_type: "bearer",
      expires_in: 900,
      user: {
        id: "user-id",
        email: "master@example.com",
        full_name: "Master",
        role: "MASTER",
        status: "ACTIVE",
        firm_id: "firm-id",
      },
    }),
  },
}));

describe("LoginView", () => {
  it("authenticates and redirects to the private shell", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/login", component: LoginView },
        { path: "/cadastro", component: { template: "<div>register</div>" } },
        { path: "/esqueci-senha", component: { template: "<div>forgot</div>" } },
        { path: "/app", component: { template: "<div>app</div>" } },
      ],
    });
    await router.push("/login");
    await router.isReady();

    const wrapper = mount(LoginView, {
      global: { plugins: [createPinia(), router] },
    });
    await wrapper.get("#email").setValue("master@example.com");
    await wrapper.get("#password").setValue("password-password");
    await wrapper.get("form").trigger("submit");
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(router.currentRoute.value.fullPath).toBe("/app");
  });
});
