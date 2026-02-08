/**
 * TokenMeter API client for the frontend dashboard.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class TokenMeterAPI {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
    this.token = "";
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(options.headers as Record<string, string>) || {},
    };

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: response.statusText } }));
      throw new Error(error.error?.message || `API error: ${response.status}`);
    }

    return response.json();
  }

  // Dashboard
  async getDashboard(period: string = "24h") {
    return this.request<any>(`/api/dashboard/overview?period=${period}`);
  }

  async getCostTrend(period: string = "7d", granularity: string = "day") {
    return this.request<any>(`/api/dashboard/cost-trend?period=${period}&granularity=${granularity}`);
  }

  async getModelBreakdown(period: string = "24h") {
    return this.request<any>(`/api/dashboard/model-breakdown?period=${period}`);
  }

  async getProviderStatus() {
    return this.request<any>(`/api/dashboard/providers`);
  }

  // Budgets
  async getBudgets() {
    return this.request<any>(`/api/budgets/`);
  }

  async createBudget(data: any) {
    return this.request<any>(`/api/budgets/`, { method: "POST", body: JSON.stringify(data) });
  }

  async getBudgetStatus(budgetId: string) {
    return this.request<any>(`/api/budgets/${budgetId}`);
  }

  async deleteBudget(budgetId: string) {
    return this.request<any>(`/api/budgets/${budgetId}`, { method: "DELETE" });
  }

  // Routing
  async getRoutingConfig() {
    return this.request<any>(`/api/routing/config`);
  }

  async updateRoutingConfig(data: any) {
    return this.request<any>(`/api/routing/config`, { method: "PUT", body: JSON.stringify(data) });
  }

  async getRoutingRules() {
    return this.request<any>(`/api/routing/rules`);
  }

  async createRoutingRule(data: any) {
    return this.request<any>(`/api/routing/rules`, { method: "POST", body: JSON.stringify(data) });
  }

  async getAvailableModels() {
    return this.request<any>(`/api/routing/models`);
  }

  // API Keys
  async getApiKeys() {
    return this.request<any>(`/api/keys/`);
  }

  async createApiKey(data: { name: string; scopes?: string[] }) {
    return this.request<any>(`/api/keys/`, { method: "POST", body: JSON.stringify(data) });
  }

  async revokeApiKey(keyId: string) {
    return this.request<any>(`/api/keys/${keyId}`, { method: "DELETE" });
  }

  // Billing
  async getPlans() {
    return this.request<any>(`/api/billing/plans`);
  }

  async createCheckout(data: { plan: string; billing_period: string }) {
    return this.request<any>(`/api/billing/checkout`, { method: "POST", body: JSON.stringify(data) });
  }

  // Health
  async getHealth() {
    return this.request<any>(`/health`);
  }
}

export const api = new TokenMeterAPI();
