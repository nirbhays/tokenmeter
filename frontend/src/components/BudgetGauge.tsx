"use client";

interface BudgetGaugeProps {
  spent: number;
  budget: number;
}

export function BudgetGauge({ spent, budget }: BudgetGaugeProps) {
  const percentage = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;

  const getColor = (pct: number) => {
    if (pct >= 100) return "bg-red-500";
    if (pct >= 80) return "bg-amber-500";
    if (pct >= 50) return "bg-yellow-400";
    return "bg-green-500";
  };

  const getTextColor = (pct: number) => {
    if (pct >= 100) return "text-red-600";
    if (pct >= 80) return "text-amber-600";
    return "text-gray-900";
  };

  return (
    <div>
      <div className="flex items-end justify-between mb-2">
        <span className={`text-2xl font-bold ${getTextColor(percentage)}`}>
          ${spent.toFixed(2)}
        </span>
        <span className="text-sm text-gray-500">/ ${budget.toFixed(2)}</span>
      </div>
      <div className="h-3 rounded-full bg-gray-100 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${getColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-400">{percentage.toFixed(0)}% used</span>
        <span className="text-xs text-gray-400">
          ${Math.max(0, budget - spent).toFixed(2)} remaining
        </span>
      </div>
    </div>
  );
}
