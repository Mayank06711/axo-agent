const GRADE_COLORS: Record<string, { stroke: string; text: string }> = {
  A: { stroke: "stroke-emerald-500", text: "text-emerald-400" },
  B: { stroke: "stroke-blue-500", text: "text-blue-400" },
  C: { stroke: "stroke-amber-500", text: "text-amber-400" },
  D: { stroke: "stroke-orange-500", text: "text-orange-400" },
  F: { stroke: "stroke-red-500", text: "text-red-400" },
};

export function ScoreGauge({ score, grade }: { score: number; grade: string }) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const colors = GRADE_COLORS[grade] || GRADE_COLORS.F;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="180" height="180" className="-rotate-90">
        <circle
          cx="90" cy="90" r={radius}
          className="stroke-gray-800" fill="none" strokeWidth="10"
        />
        <circle
          cx="90" cy="90" r={radius}
          className={`${colors.stroke} transition-all duration-1000 ease-out`}
          fill="none" strokeWidth="10" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold font-mono ${colors.text}`}>
          {Math.round(score)}
        </span>
        <span className="text-xs text-gray-500 mt-1">/ 100</span>
      </div>
    </div>
  );
}
