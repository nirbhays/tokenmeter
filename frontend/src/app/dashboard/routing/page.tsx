"use client";

import { useState } from "react";

const routingModes = [
  {
    id: "cost-optimized",
    name: "Cost Optimized",
    description: "Route to the cheapest model that can handle the task complexity",
    icon: "💰",
  },
  {
    id: "latency-optimized",
    name: "Latency Optimized",
    description: "Route to the fastest model that meets quality thresholds",
    icon: "⚡",
  },
  {
    id: "quality-optimized",
    name: "Quality Optimized",
    description: "Route to the highest-quality model within budget constraints",
    icon: "✨",
  },
];

export default function RoutingPage() {
  const [mode, setMode] = useState("cost-optimized");
  const [enabled, setEnabled] = useState(true);
  const [rules, setRules] = useState([
    { id: "1", name: "Simple → Nano", source: "gpt-4.1", complexity: "simple", target: "gpt-4.1-nano", enabled: true },
    { id: "2", name: "Search team → Flash", source: "*", team: "search", target: "gemini-2.5-flash", enabled: true },
    { id: "3", name: "Complex → GPT-5", source: "gpt-4.1", complexity: "complex", target: "gpt-5", enabled: false },
  ]);

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <div className="flex-1 p-8">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Smart Routing</h1>
          <p className="text-gray-500 mb-8">Configure how requests are automatically routed to optimize cost, speed, or quality.</p>

          {/* Enable toggle */}
          <div className="bg-white rounded-2xl border p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Smart Routing</h3>
                <p className="text-sm text-gray-500">When enabled, requests are automatically routed based on complexity analysis</p>
              </div>
              <button
                onClick={() => setEnabled(!enabled)}
                className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                  enabled ? "bg-brand-600" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                    enabled ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Routing mode selector */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {routingModes.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`rounded-2xl border-2 p-6 text-left transition-all ${
                  mode === m.id
                    ? "border-brand-600 bg-brand-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <span className="text-3xl">{m.icon}</span>
                <h3 className="mt-3 font-semibold text-gray-900">{m.name}</h3>
                <p className="mt-1 text-sm text-gray-500">{m.description}</p>
              </button>
            ))}
          </div>

          {/* Routing rules */}
          <div className="bg-white rounded-2xl border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Custom Rules</h3>
              <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500">
                + Add Rule
              </button>
            </div>
            <div className="space-y-3">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className="flex items-center justify-between rounded-xl border p-4"
                >
                  <div className="flex items-center gap-4">
                    <span className={`h-2 w-2 rounded-full ${rule.enabled ? "bg-green-500" : "bg-gray-300"}`} />
                    <div>
                      <p className="font-medium text-gray-900">{rule.name}</p>
                      <p className="text-sm text-gray-500">
                        {rule.source} → {rule.target}
                        {rule.complexity && ` (${rule.complexity})`}
                        {rule.team && ` [team: ${rule.team}]`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="rounded-lg px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100">Edit</button>
                    <button className="rounded-lg px-3 py-1.5 text-sm text-red-600 hover:bg-red-50">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
