import { AgentTimeline } from "./components/AgentTimeline";
import { Report } from "./components/Report";
import { UrlInput } from "./components/UrlInput";
import { useSimulation } from "./hooks/useSimulation";

function App() {
  const {
    status,
    events,
    report,
    error,
    history,
    start,
    reset,
    loadPastSimulation,
  } = useSimulation();

  return (
    <div className="min-h-screen bg-gray-950 text-gray-50 flex flex-col relative overflow-hidden">
      {/* Background grid */}
      <div className="fixed inset-0 bg-grid pointer-events-none" />

      {/* Floating orbs - visible during analyzing */}
      {status === "running" && (
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-gray-800/60 bg-gray-950/80 backdrop-blur-xl">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              </div>
              <div>
                <h1 className="text-base font-semibold tracking-tight leading-tight">AXO Agent</h1>
                <p className="text-[11px] text-gray-500">AI Agent Readiness Testing</p>
              </div>
            </div>
            {status !== "idle" && (
              <button
                onClick={reset}
                className="text-xs text-gray-400 hover:text-gray-200 transition-colors px-3 py-1.5 rounded-lg border border-gray-800 hover:border-gray-600 hover:bg-gray-800/50"
              >
                New Simulation
              </button>
            )}
          </div>
          <UrlInput onSubmit={start} disabled={status === "running"} />
        </div>

        {/* Scan line during analysis */}
        {status === "running" && (
          <div className="relative h-0 overflow-visible">
            <div className="scan-line" />
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-5xl w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6 flex-1 relative z-10">
        {/* Error state */}
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 flex items-start gap-3 animate-fade-in-up">
            <div className="flex-shrink-0 mt-0.5 h-5 w-5 rounded-full bg-red-500/10 flex items-center justify-center">
              <span className="text-red-400 text-xs">!</span>
            </div>
            <div>
              <p className="text-sm font-medium text-red-400">Simulation failed</p>
              <p className="text-xs text-red-400/70 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Running state */}
        {status === "running" && (
          <div className="space-y-4 animate-fade-in-up">
            <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 backdrop-blur-sm p-4 flex items-center gap-3">
              <svg className="h-5 w-5 animate-spin text-blue-500" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <div className="flex-1">
                <p className="text-sm text-gray-200">Simulation in progress...</p>
                <p className="text-xs text-gray-500 mt-0.5">{events.length} events captured</p>
              </div>
            </div>
            <AgentTimeline events={events} isStreaming={true} />
          </div>
        )}

        {/* Completed state */}
        {status === "completed" && report && (
          <div className="animate-fade-in-up">
            <Report report={report} />
            <details className="group mt-6">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors flex items-center gap-1.5 py-2">
                <svg className="h-3 w-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
                Agent execution log ({events.length} events)
              </summary>
              <div className="mt-2">
                <AgentTimeline events={events} isStreaming={false} />
              </div>
            </details>
          </div>
        )}

        {/* Idle state */}
        {status === "idle" && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            {/* Glowing icon */}
            <div className="relative mb-6 animate-fade-in-up">
              <div className="absolute inset-0 rounded-3xl bg-violet-500/20 blur-xl" />
              <div className="relative h-20 w-20 rounded-3xl bg-gradient-to-br from-violet-500/20 to-blue-600/20 border border-violet-500/20 flex items-center justify-center">
                <svg className="h-10 w-10 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              </div>
            </div>

            <h2 className="text-2xl font-semibold text-gray-100 mb-3 animate-fade-in-up">
              Test any website for AI agent readiness
            </h2>
            <p className="text-sm text-gray-500 max-w-lg mb-8 leading-relaxed animate-fade-in-up-delayed">
              Simulate how an AI agent navigates your website, finding pricing, features,
              documentation, and contact info. Get a readiness score with actionable recommendations.
            </p>

            {/* Feature cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl w-full mb-10">
              {[
                { title: "Agent Tasks", desc: "AI agent tries to complete real tasks on your site", color: "violet", delay: "" },
                { title: "Standards Checks", desc: "robots.txt, llms.txt, JSON-LD, agents.json, HTTPS", color: "blue", delay: "animate-fade-in-up-delayed" },
                { title: "Readiness Score", desc: "Composite score with grade, issues & recommendations", color: "emerald", delay: "animate-fade-in-up-delayed-2" },
              ].map((card) => (
                <div
                  key={card.title}
                  className={`rounded-xl border border-gray-800 bg-gray-900/50 p-4 text-left hover:border-gray-700 transition-all card-hover ${card.delay || "animate-fade-in-up"}`}
                >
                  <div className={`h-2 w-8 rounded-full mb-3 ${
                    card.color === "violet" ? "bg-violet-500" :
                    card.color === "blue" ? "bg-blue-500" : "bg-emerald-500"
                  }`} />
                  <p className="text-sm font-medium text-gray-200 mb-1">{card.title}</p>
                  <p className="text-xs text-gray-500 leading-relaxed">{card.desc}</p>
                </div>
              ))}
            </div>

            {/* Past simulations */}
            {history.length > 0 && (
              <div className="w-full max-w-2xl animate-fade-in-up-delayed-2">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3 text-left">
                  Recent Simulations
                </h3>
                <div className="space-y-1.5">
                  {history.map((simId) => (
                    <button
                      key={simId}
                      onClick={() => loadPastSimulation(simId)}
                      className="w-full flex items-center justify-between rounded-lg border border-gray-800 bg-gray-900/50 px-4 py-2.5 text-left hover:border-gray-700 hover:bg-gray-800/50 transition-colors group"
                    >
                      <span className="text-xs font-mono text-gray-400 group-hover:text-gray-200 transition-colors">
                        {simId}
                      </span>
                      <svg className="h-3.5 w-3.5 text-gray-600 group-hover:text-gray-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/40 relative z-10">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between text-[11px] text-gray-600">
          <span>AXO Agent</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
