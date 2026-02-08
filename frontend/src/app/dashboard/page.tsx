"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SpendChart } from "@/components/SpendChart";
import { ModelBreakdown } from "@/components/ModelBreakdown";
import { UsageTable } from "@/components/UsageTable";
import { BudgetGauge } from "@/components/BudgetGauge";
import { ProviderStatus } from "@/components/ProviderStatus";
import { api } from "@/lib/api";

interface DashboardData {
  summary: {
    total_requests: number;
    total_tokens: number;
    total_cost_usd: number;
    avg_latency_ms: number;
    error_rate: number;
    cache_hit_rate: number;
  };
  cost_trend: Array<{ timestamp: string; cost_usd: number; requests: number }>;
  by_model: Array<{
    model: string;
    provider: string;
    total_requests: number;
    total_cost_usd: number;
  }>;
  by_team: Array<{ team: string; total_cost_usd: number }>;
}

const navItems = [
  { href: "/dashboard", label: "Overview", icon: "📊" },
  { href: "/dashboard/usage", label: "Usage", icon: "📈" },
  { href: "/dashboard/routing", label: "Routing", icon: "🧠" },
  { href: "/dashboard/budgets", label: "Budgets", icon: "💰" },
  { href: "/dashboard/keys", label: "API Keys", icon: "🔑" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [period, setPeriod] = useState("24h");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, [period]);

  async function loadDashboard() {
    setLoading(true);
    try {
      const result = await api.getDashboard(period);
      setData(result);
    } catch (e) {
      console.error("Failed to load dashboard:", e);
    }
    setLoading(false);
  }

  // Placeholder data for demo
  const demoData: DashboardData = {
    summary: {
      total_requests: 12_847,
      total_tokens: 4_532_100,
      total_cost_usd: 23.47,
      avg_latency_ms: 342,
      error_rate: 0.002,
      cache_hit_rate: 0.18,
    },
    cost_trend: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
      cost_usd: Math.random() * 2 + 0.5,
      requests: Math.floor(Math.random() * 800 + 200),
    })),
    by_model: [
      { model: "gpt-4.1-nano", provider: "openai", total_requests: 5200, total_cost_usd: 1.82 },
      { model: "gpt-4.1-mini", provider: "openai", total_requests: 3100, total_cost_usd: 4.96 },
      { model: "gpt-4.1", provider: "openai", total_requests: 2100, total_cost_usd: 8.40 },
      { model: "claude-sonnet-4.5", provider: "anthropic", total_requests: 1200, total_cost_usd: 5.40 },
      { model: "gemini-2.5-flash", provider: "google", total_requests: 1247, total_cost_usd: 2.89 },
    ],
    by_team: [
      { team: "search", total_cost_usd: 9.20 },
      { team: "chatbot", total_cost_usd: 7.15 },
      { team: "analytics", total_cost_usd: 4.32 },
      { team: "internal", total_cost_usd: 2.80 },
    ],
  };

  const display = data || demoData;

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 bg-gray-50/50 p-4">
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            Dashboard
          </h2>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-500">Real-time AI spend overview</p>
            </div>
            <div className="flex gap-2">
              {["1h", "24h", "7d", "30d"].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    period === p
                      ? "bg-brand-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Stats cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              label="Total Spend"
              value={`$${display.summary.total_cost_usd.toFixed(2)}`}
              subtitle="this period"
              color="brand"
            />
            <StatCard
              label="Requests"
              value={display.summary.total_requests.toLocaleString()}
              subtitle={`${display.summary.total_tokens.toLocaleString()} tokens`}
              color="blue"
            />
            <StatCard
              label="Avg Latency"
              value={`${display.summary.avg_latency_ms.toFixed(0)}ms`}
              subtitle={`${(display.summary.error_rate * 100).toFixed(1)}% error rate`}
              color="green"
            />
            <StatCard
              label="Cache Hit Rate"
              value={`${(display.summary.cache_hit_rate * 100).toFixed(0)}%`}
              subtitle="responses served from cache"
              color="purple"
            />
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Cost Trend</h3>
              <SpendChart data={display.cost_trend} />
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">By Model</h3>
              <ModelBreakdown data={display.by_model} />
            </div>
          </div>

          {/* Bottom row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Budget Status</h3>
              <BudgetGauge spent={display.summary.total_cost_usd} budget={100} />
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Provider Health</h3>
              <ProviderStatus />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  subtitle,
  color,
}: {
  label: string;
  value: string;
  subtitle: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    brand: "bg-brand-50 border-brand-200",
    blue: "bg-blue-50 border-blue-200",
    green: "bg-green-50 border-green-200",
    purple: "bg-purple-50 border-purple-200",
  };

  return (
    <div
      className={`rounded-2xl border p-6 ${colorMap[color] || "bg-gray-50 border-gray-200"}`}
    >
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  );
}
