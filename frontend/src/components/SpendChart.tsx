"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface SpendChartProps {
  data: Array<{ timestamp: string; cost_usd: number; requests: number }>;
}

export function SpendChart({ data }: SpendChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    cost: parseFloat(d.cost_usd.toFixed(3)),
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formatted} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <defs>
            <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0c8ee7" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#0c8ee7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `$${v}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "none",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "12px",
            }}
            formatter={(value: number) => [`$${value.toFixed(4)}`, "Cost"]}
          />
          <Area
            type="monotone"
            dataKey="cost"
            stroke="#0c8ee7"
            strokeWidth={2}
            fill="url(#costGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
