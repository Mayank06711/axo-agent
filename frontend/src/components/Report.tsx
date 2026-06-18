import type { SimulationReport } from "../lib/types";
import { GradeBadge } from "./GradeBadge";
import { IssuesList, RecommendationsList } from "./IssuesList";
import { ScoreGauge } from "./ScoreGauge";
import { StandardsChecks } from "./StandardsChecks";
import { TaskCard } from "./TaskCard";

interface ReportProps {
  report: SimulationReport;
}

export function Report({ report }: ReportProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
        <div className="flex flex-col lg:flex-row items-center gap-6">
          {/* Score gauge */}
          <ScoreGauge score={report.overall_score} grade={report.grade} />

          {/* Summary */}
          <div className="flex-1 text-center lg:text-left">
            <div className="flex items-center gap-3 justify-center lg:justify-start">
              <h2 className="text-xl font-semibold text-gray-50">Agent Readiness Report</h2>
              <GradeBadge grade={report.grade} size="lg" />
            </div>
            <p className="text-sm text-gray-400 mt-2 font-mono">{report.url}</p>
            <div className="flex gap-4 mt-3 text-xs text-gray-500 justify-center lg:justify-start">
              {report.duration_seconds && (
                <span>Duration: <span className="text-gray-400 font-mono">{report.duration_seconds}s</span></span>
              )}
              <span>LLM: <span className="text-gray-400 font-mono">{report.llm_provider}/{report.llm_model}</span></span>
              <span>Tasks: <span className="text-gray-400 font-mono">{report.task_results.length}</span></span>
            </div>
          </div>
        </div>
      </div>

      {/* Task results grid */}
      {report.task_results.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-50 mb-3">Agent Task Results</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {report.task_results.map((result) => (
              <TaskCard key={result.task_name} result={result} />
            ))}
          </div>
        </div>
      )}

      {/* Standards checks */}
      <StandardsChecks results={report.standards_results} />

      {/* Issues + Recommendations side by side on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <IssuesList issues={report.issues} />
        <RecommendationsList recommendations={report.recommendations} />
      </div>
    </div>
  );
}
