export function IssuesList({ issues }: { issues: string[] }) {
  if (issues.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-50">Issues Identified</h3>
        <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-0.5 rounded-md">
          {issues.length}
        </span>
      </div>
      <ul className="space-y-2">
        {issues.map((issue, i) => (
          <li key={i} className="flex gap-2 text-xs">
            <span className="flex-shrink-0 mt-0.5 h-1.5 w-1.5 rounded-full bg-amber-500" />
            <span className="text-gray-400">{issue}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RecommendationsList({ recommendations }: { recommendations: string[] }) {
  if (recommendations.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="text-sm font-medium text-gray-50 mb-3">Recommendations</h3>
      <ol className="space-y-2">
        {recommendations.map((rec, i) => (
          <li key={i} className="flex gap-2 text-xs">
            <span className="flex-shrink-0 text-blue-400 font-mono w-4 text-right">{i + 1}.</span>
            <span className="text-gray-400">{rec}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
