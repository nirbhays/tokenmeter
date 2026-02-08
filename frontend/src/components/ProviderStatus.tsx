"use client";

const providers = [
  { name: "OpenAI", status: "healthy", latency: 245, models: 8, color: "green" },
  { name: "Anthropic", status: "healthy", latency: 312, models: 3, color: "green" },
  { name: "Google", status: "healthy", latency: 198, models: 2, color: "green" },
];

export function ProviderStatus() {
  return (
    <div className="space-y-3">
      {providers.map((p) => (
        <div key={p.name} className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-3">
            <span className={`h-2.5 w-2.5 rounded-full ${
              p.status === "healthy" ? "bg-green-500" : p.status === "degraded" ? "bg-yellow-500" : "bg-red-500"
            }`} />
            <div>
              <p className="font-medium text-sm">{p.name}</p>
              <p className="text-xs text-gray-500">{p.models} models</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-mono">{p.latency}ms</p>
            <p className="text-xs text-gray-500 capitalize">{p.status}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
