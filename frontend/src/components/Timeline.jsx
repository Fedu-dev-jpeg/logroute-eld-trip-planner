import { formatDateTime, formatDuration } from "../utils";

const LABELS = {
  driving: "Driving",
  pickup: "Pickup",
  dropoff: "Drop-off",
  fuel: "Fuel",
  break: "DOT break",
  daily_rest: "10-hour reset",
  cycle_restart: "34-hour restart",
};

export default function Timeline({ events }) {
  return (
    <div className="timeline">
      {events.map((event, index) => (
        <article className={`timeline-item kind-${event.kind}`} key={`${event.start}-${index}`}>
          <div className="timeline-rail"><i /></div>
          <div className="timeline-time">{formatDateTime(event.start)}</div>
          <div className="timeline-body">
            <div><span className="event-tag">{LABELS[event.kind]}</span><span className="event-duration">{formatDuration(event.duration_hours)}</span></div>
            <h4>{event.title}</h4>
            {event.miles > 0 && <p>{event.miles.toLocaleString("en-US")} miles scheduled</p>}
          </div>
        </article>
      ))}
    </div>
  );
}
