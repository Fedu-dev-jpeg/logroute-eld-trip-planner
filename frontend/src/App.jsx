import { useState } from "react";
import { createTripPlan } from "./api";
import LogSheet from "./components/LogSheet";
import RouteMap from "./components/RouteMap";
import SummaryCards from "./components/SummaryCards";
import Timeline from "./components/Timeline";
import TripForm from "./components/TripForm";

export default function App() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeLog, setActiveLog] = useState(0);

  const planTrip = async (payload) => {
    setLoading(true);
    setError("");
    try {
      const result = await createTripPlan(payload);
      setPlan(result);
      setActiveLog(0);
      requestAnimationFrame(() => document.getElementById("trip-results")?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top"><span className="brand-mark">LR</span><span>LogRoute<small>ELD trip planner</small></span></a>
        <div className="topbar-meta"><span className="live-dot" />FMCSA property carrier rules</div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">Dispatch with confidence</span>
            <h1>A route your driver<br /><em>can actually run.</em></h1>
            <p>Turn pickup details into a mapped, hours-of-service-aware plan and ready-to-review daily ELD logs.</p>
            <div className="trust-row"><span>✓ 11-hour driving limit</span><span>✓ 30-minute breaks</span><span>✓ 70-hour cycle</span></div>
          </div>
          <TripForm loading={loading} onSubmit={planTrip} />
        </section>

        {error && <div className="error-banner" role="alert"><strong>We hit a routing issue.</strong><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss">×</button></div>}

        {plan && (
          <section id="trip-results" className="results">
            <div className="section-heading"><div><span className="eyebrow">Dispatch overview</span><h2>Your compliant trip plan</h2></div><span className="plan-status">Plan ready</span></div>
            <SummaryCards plan={plan} />

            <div className="dashboard-grid">
              <article className="panel map-panel">
                <div className="panel-heading"><div><span className="eyebrow">Route</span><h3>{plan.locations.current.label.split(",")[0]} → {plan.locations.dropoff.label.split(",")[0]}</h3></div><span>{plan.stops.length} compliance stop{plan.stops.length === 1 ? "" : "s"}</span></div>
                <RouteMap plan={plan} />
              </article>
              <article className="panel schedule-panel">
                <div className="panel-heading"><div><span className="eyebrow">Schedule</span><h3>Driver timeline</h3></div><span>{plan.schedule.length} events</span></div>
                <Timeline events={plan.schedule} />
              </article>
            </div>

            <article className="compliance-callout">
              <div className="shield">✓</div>
              <div><span className="eyebrow">Planning note</span><h3>Conservative by design</h3><p>{plan.compliance.assumption}</p></div>
              <div className="cycle-meter"><span>Ending cycle</span><strong>{plan.summary.ending_cycle_used_hours} / 70h</strong><div><i style={{ width: `${Math.min(100, (plan.summary.ending_cycle_used_hours / 70) * 100)}%` }} /></div></div>
            </article>

            <section className="logs-section">
              <div className="section-heading"><div><span className="eyebrow">Generated records</span><h2>Daily log sheets</h2></div><span className="sheet-count">{plan.daily_logs.length} sheets</span></div>
              <div className="log-tabs" role="tablist">
                {plan.daily_logs.map((log, index) => <button role="tab" aria-selected={activeLog === index} className={activeLog === index ? "active" : ""} onClick={() => setActiveLog(index)} key={log.date}>Day {index + 1}<small>{new Date(`${log.date}T12:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</small></button>)}
              </div>
              <LogSheet log={plan.daily_logs[activeLog]} plan={plan} />
            </section>
          </section>
        )}
      </main>
      <footer><span>LogRoute assessment build</span><span>Routing data © OpenStreetMap contributors</span></footer>
    </div>
  );
}
