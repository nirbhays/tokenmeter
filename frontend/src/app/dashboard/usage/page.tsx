"use client";

import { useState } from "react";
import { UsageTable } from "@/components/UsageTable";

export default function UsagePage() {
  const [period, setPeriod] = useState("24h");
  const [filterModel, setFilterModel] = useState("");
  const [filterTeam, setFilterTeam] = useState("");

  const demoRecords = Array.from({ length: 50 }, (_, i) => ({
    id: `req_${i}`,
    timestamp: new Date(Date.now() - i * 120000).toISOString(),
    model: ["gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1", "claude-sonnet-4.5", "gemini-2.5-flash"][i % 5],
    provider: ["openai", "openai", "openai", "anthropic", "google"][i % 5],
    team: ["search", "chatbot", "analytics", "internal"][i % 4],
    feature: ["autocomplete", "chat", "summarize", "classify"][i % 4],
    prompt_tokens: Math.floor(Math.random() * 2000 + 100),
    completion_tokens: Math.floor(Math.random() * 1000 + 50),
    cost_usd: parseFloat((Math.random() * 0.05).toFixed(5)),
    latency_ms: Math.floor(Math.random() * 800 + 100),
    status: i % 20 === 0 ? "error" : "success",
    cached: i % 7 === 0,
  }));

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Usage Analytics</h1>
              <p className="text-gray-500">Detailed request logs and cost breakdown</p>
            </div>
            <div className="flex gap-4">
              <select
                value={filterModel}
                onChange={(e) => setFilterModel(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">All Models</option>
                <option value="gpt-4.1-nano">GPT-4.1 Nano</option>
                <option value="gpt-4.1-mini">GPT-4.1 Mini</option>
                <option value="gpt-4.1">GPT-4.1</option>
                <option value="claude-sonnet-4.5">Claude Sonnet 4.5</option>
                <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
              </select>
              <select
                value={filterTeam}
                onChange={(e) => setFilterTeam(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">All Teams</option>
                <option value="search">Search</option>
                <option value="chatbot">Chatbot</option>
                <option value="analytics">Analytics</option>
              </select>
              <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
                {["1h", "24h", "7d", "30d"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      period === p
                        ? "bg-white text-gray-900 shadow-sm"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-sm text-gray-500">Total Cost</p>
              <p className="text-2xl font-bold">$23.47</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-sm text-gray-500">Requests</p>
              <p className="text-2xl font-bold">12,847</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-sm text-gray-500">Tokens</p>
              <p className="text-2xl font-bold">4.5M</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-sm text-gray-500">Avg Cost/Request</p>
              <p className="text-2xl font-bold">$0.0018</p>
            </div>
          </div>

          {/* Request log table */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Request Log</h3>
            <UsageTable records={demoRecords} />
          </div>
        </div>
      </div>
    </div>
  );
}
