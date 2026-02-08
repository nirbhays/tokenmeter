"use client";

import { useState } from "react";
import { BudgetGauge } from "@/components/BudgetGauge";

export default function BudgetsPage() {
  const [budgets] = useState([
    { id: "1", name: "Monthly AI Spend", amount: 500, spent: 127.43, period: "monthly", team: null, hard_limit: false },
    { id: "2", name: "Search Team", amount: 200, spent: 89.20, period: "monthly", team: "search", hard_limit: true },
    { id: "3", name: "Chatbot Feature", amount: 100, spent: 45.15, period: "monthly", team: null, hard_limit: false },
  ]);

  const [alerts] = useState([
    { id: "1", budget: "Search Team", severity: "warning", message: "Reached 80% of budget ($89.20 / $200.00)", time: "2 hours ago" },
    { id: "2", budget: "Monthly AI Spend", severity: "info", message: "Reached 50% of budget ($127.43 / $500.00)", time: "1 day ago" },
  ]);

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <div className="flex-1 p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Budgets</h1>
              <p className="text-gray-500">Set spending limits and get alerted before you exceed them</p>
            </div>
            <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500">
              + Create Budget
            </button>
          </div>

          {/* Budget cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {budgets.map((budget) => {
              const pct = (budget.spent / budget.amount) * 100;
              return (
                <div key={budget.id} className="bg-white rounded-2xl border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900">{budget.name}</h3>
                    {budget.hard_limit && (
                      <span className="text-xs bg-red-100 text-red-700 rounded-full px-2 py-0.5">Hard Limit</span>
                    )}
                  </div>
                  <BudgetGauge spent={budget.spent} budget={budget.amount} />
                  <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                    <span>{budget.period}</span>
                    {budget.team && <span>Team: {budget.team}</span>}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recent alerts */}
          <div className="bg-white rounded-2xl border p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-start gap-3 rounded-lg border p-4">
                  <span className="text-xl">
                    {alert.severity === "critical" ? "🚨" : alert.severity === "warning" ? "⚠️" : "ℹ️"}
                  </span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{alert.budget}</p>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                  </div>
                  <span className="text-xs text-gray-400">{alert.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
