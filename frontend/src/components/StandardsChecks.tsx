import type { StandardsCheckResult } from "../lib/types";

const CHECK_LABELS: Record<string, string> = {
  robots_txt: "robots.txt",
  llms_txt: "llms.txt",
  schema_org: "JSON-LD Schema",
  meta_tags: "Meta & Open Graph",
  agents_json: "agents.json",
  security: "HTTPS & Security",
};

function scoreColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

export function StandardsChecks({ results }: { results: StandardsCheckResult[] }) {
  if (results.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="text-sm font-medium text-gray-50 mb-4">Standards Compliance</h3>
      <div className="space-y-3">
        {results.map((check) => (
          <div key={check.check_name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-400">
                {CHECK_LABELS[check.check_name] || check.check_name}
              </span>
              <span className="text-xs font-mono text-gray-400">{check.score}</span>
            </div>
            <div className="h-1 rounded-full bg-gray-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${scoreColor(check.score)}`}
                style={{ width: `${check.score}%` }}
              />
            </div>
            {check.issues.length > 0 && (
              <p className="text-[10px] text-gray-500 mt-0.5 truncate">
                {check.issues[0]}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
