import type { TaskResult } from "../lib/types";
import { GradeBadge } from "./GradeBadge";

const TASK_LABELS: Record<string, string> = {
  pricing: "Pricing",
  features: "Features",
  documentation: "Documentation",
  contact: "Contact & Support",
};

function taskGrade(score: number): string {
  if (score >= 90) return "A";
  if (score >= 75) return "B";
  if (score >= 60) return "C";
  if (score >= 40) return "D";
  return "F";
}

export function TaskCard({ result }: { result: TaskResult }) {
  const grade = taskGrade(result.score);
  const label = TASK_LABELS[result.task_name] || result.task_name;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 hover:border-gray-700 transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-50">{label}</span>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-md ${
            result.found
              ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20"
              : "bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20"
          }`}>
            {result.found ? "Found" : "Not Found"}
          </span>
          <GradeBadge grade={grade} size="sm" />
        </div>
      </div>

      {/* Score bar */}
      <div className="h-1.5 rounded-full bg-gray-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            result.score >= 75 ? "bg-emerald-500" :
            result.score >= 50 ? "bg-amber-500" : "bg-red-500"
          }`}
          style={{ width: `${result.score}%` }}
        />
      </div>

      {/* Details */}
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-gray-500">
        <div>
          <span className="text-gray-400 font-mono">{result.score}</span>
          <span className="ml-1">score</span>
        </div>
        <div>
          <span className="text-gray-400 font-mono">{result.steps_taken}</span>
          <span className="ml-1">steps</span>
        </div>
        <div>
          <span className="text-gray-400 font-mono">{result.issues.length}</span>
          <span className="ml-1">issues</span>
        </div>
      </div>

      {/* Findings */}
      {result.findings.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-500 mb-1">Findings:</p>
          {result.findings.slice(0, 2).map((f, i) => (
            <p key={i} className="text-xs text-gray-400 truncate">{f}</p>
          ))}
        </div>
      )}
    </div>
  );
}
