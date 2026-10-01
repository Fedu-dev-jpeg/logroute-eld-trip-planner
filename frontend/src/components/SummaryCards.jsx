import { formatDuration } from "../utils";

export default function SummaryCards({ plan }) {
  const cards = [
    { label: "Route distance", value: `${plan.route.distance_miles.toLocaleString("en-US")} mi`, note: "road miles" },
    { label: "Trip duration", value: formatDuration(plan.summary.trip_duration_hours), note: "including required rests" },
    { label: "Driving time", value: formatDuration(plan.summary.driving_hours), note: "OSRM estimate" },
    { label: "Daily logs", value: plan.daily_logs.length, note: plan.daily_logs.length === 1 ? "log sheet" : "log sheets" },
  ];
  return (
    <div className="summary-grid">
      {cards.map((card) => <article className="summary-card" key={card.label}><span>{card.label}</span><strong>{card.value}</strong><small>{card.note}</small></article>)}
    </div>
  );
}
