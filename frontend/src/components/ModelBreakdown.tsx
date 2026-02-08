"use client";

interface ModelData {
  model: string;
  provider: string;
  total_requests: number;
  total_cost_usd: number;
}

interface ModelBreakdownProps {
  data: ModelData[];
}

const providerColors: Record<string, string> = {
  openai: "#10b981",
  anthropic: "#f59e0b",
  google: "#3b82f6",
};

const modelColors = [
  "#0c8ee7", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#ec4899", "#14b8a6",
];

export function ModelBreakdown({ data }: ModelBreakdownProps) {
  const totalCost = data.reduce((sum, d) => sum + d.total_cost_usd, 0);

  return (
    <div className="space-y-4">
      {/* Simple visual breakdown */}
      <div className="flex h-4 rounded-full overflow-hidden bg-gray-100">
        {data.map((d, i) => {
          const pct = totalCost > 0 ? (d.total_cost_usd / totalCost) * 100 : 0;
          return (
            <div
              key={d.model}
              className="h-full transition-all duration-500"
              style={{
                width: `${pct}%`,
                backgroundColor: modelColors[i % modelColors.length],
              }}
              title={`${d.model}: $${d.total_cost_usd.toFixed(4)} (${pct.toFixed(1)}%)`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="space-y-2">
        {data.map((d, i) => {
          const pct = totalCost > 0 ? (d.total_cost_usd / totalCost) * 100 : 0;
          return (
            <div key={d.model} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: modelColors[i % modelColors.length] }}
                />
                <span className="text-sm text-gray-700">{d.model}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium">${d.total_cost_usd.toFixed(2)}</span>
                <span className="text-xs text-gray-400 ml-2">{pct.toFixed(0)}%</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Total */}
      <div className="flex items-center justify-between pt-3 border-t">
        <span className="text-sm font-semibold text-gray-900">Total</span>
        <span className="text-sm font-bold">${totalCost.toFixed(2)}</span>
      </div>
    </div>
  );
}
