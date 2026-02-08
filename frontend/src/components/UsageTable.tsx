"use client";

interface UsageRecord {
  id: string;
  timestamp: string;
  model: string;
  provider: string;
  team?: string;
  feature?: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  latency_ms: number;
  status: string;
  cached?: boolean;
}

interface UsageTableProps {
  records: UsageRecord[];
}

export function UsageTable({ records }: UsageTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-2 px-3 font-medium text-gray-500">Time</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Model</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Team</th>
            <th className="text-right py-2 px-3 font-medium text-gray-500">Tokens</th>
            <th className="text-right py-2 px-3 font-medium text-gray-500">Cost</th>
            <th className="text-right py-2 px-3 font-medium text-gray-500">Latency</th>
            <th className="text-center py-2 px-3 font-medium text-gray-500">Status</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id} className="border-b hover:bg-gray-50">
              <td className="py-2 px-3 text-gray-500 font-mono text-xs">
                {new Date(record.timestamp).toLocaleTimeString()}
              </td>
              <td className="py-2 px-3">
                <span className="font-medium text-gray-900">{record.model}</span>
                {record.cached && (
                  <span className="ml-1 text-xs bg-blue-100 text-blue-700 rounded px-1">cached</span>
                )}
              </td>
              <td className="py-2 px-3 text-gray-600">{record.team || "—"}</td>
              <td className="py-2 px-3 text-right text-gray-600 font-mono">
                {(record.prompt_tokens + record.completion_tokens).toLocaleString()}
              </td>
              <td className="py-2 px-3 text-right font-mono font-medium">
                ${record.cost_usd.toFixed(5)}
              </td>
              <td className="py-2 px-3 text-right text-gray-600 font-mono">
                {record.latency_ms}ms
              </td>
              <td className="py-2 px-3 text-center">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${
                    record.status === "success" ? "bg-green-500" : "bg-red-500"
                  }`}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
