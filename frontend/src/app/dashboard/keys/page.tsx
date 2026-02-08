"use client";

import { useState } from "react";

export default function KeysPage() {
  const [keys] = useState([
    { id: "key_1", name: "Production", masked: "tm_prod...x8k2", created: "2026-01-15", lastUsed: "2 min ago", scopes: ["proxy", "dashboard"] },
    { id: "key_2", name: "Staging", masked: "tm_stag...m4p1", created: "2026-01-20", lastUsed: "3 hours ago", scopes: ["proxy"] },
    { id: "key_3", name: "CI/CD", masked: "tm_cicd...n7q3", created: "2026-02-01", lastUsed: "1 day ago", scopes: ["proxy"] },
  ]);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
              <p className="text-gray-500">Manage your TokenMeter API keys</p>
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
            >
              + Create Key
            </button>
          </div>

          {showCreate && (
            <div className="bg-brand-50 rounded-2xl border border-brand-200 p-6 mb-6">
              <h3 className="font-semibold mb-3">Create New API Key</h3>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="Key name (e.g., Production)"
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm"
                />
                <button className="rounded-lg bg-brand-600 px-6 py-2 text-sm font-medium text-white hover:bg-brand-500">
                  Create
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Name</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Key</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Scopes</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Last Used</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-gray-500">Created</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr key={key.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{key.name}</td>
                    <td className="px-6 py-4">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">{key.masked}</code>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-1">
                        {key.scopes.map((s) => (
                          <span key={s} className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{s}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{key.lastUsed}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{key.created}</td>
                    <td className="px-6 py-4">
                      <button className="text-sm text-red-600 hover:text-red-800">Revoke</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
