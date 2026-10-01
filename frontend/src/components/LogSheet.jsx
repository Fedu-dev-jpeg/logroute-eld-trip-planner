import { useRef, useState } from "react";

const STATUS_Y = { off_duty: 192, sleeper_berth: 209, driving: 225, on_duty: 241 };
const GRID_START = 65;
const GRID_WIDTH = 389;

function linePoints(events) {
  const points = [];
  events.forEach((event, index) => {
    const startX = GRID_START + (event.start_hour / 24) * GRID_WIDTH;
    const endX = GRID_START + (event.end_hour / 24) * GRID_WIDTH;
    const y = STATUS_Y[event.status];
    if (index === 0) points.push(`${startX},${y}`);
    else {
      const previousY = STATUS_Y[events[index - 1].status];
      points.push(`${startX},${previousY}`, `${startX},${y}`);
    }
    points.push(`${endX},${y}`);
  });
  return points.join(" ");
}

export default function LogSheet({ log, plan }) {
  const svgRef = useRef(null);
  const [downloading, setDownloading] = useState(false);
  const date = new Date(`${log.date}T12:00:00`);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const year = date.getFullYear();
  const totals = log.totals;
  const remarks = log.events.filter((event) => event.kind !== "off_duty").slice(0, 4);

  const download = async () => {
    setDownloading(true);
    try {
      const svg = svgRef.current.cloneNode(true);
      const image = svg.querySelector("image");
      const blob = await fetch("/blank-paper-log.png").then((response) => response.blob());
      const dataUrl = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.readAsDataURL(blob);
      });
      image.setAttribute("href", dataUrl);
      const source = new XMLSerializer().serializeToString(svg);
      const objectUrl = URL.createObjectURL(new Blob([source], { type: "image/svg+xml" }));
      const rendered = new Image();
      rendered.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = 1026;
        canvas.height = 972;
        const context = canvas.getContext("2d");
        context.drawImage(rendered, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(objectUrl);
        const link = document.createElement("a");
        link.download = `eld-log-${log.date}.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
        setDownloading(false);
      };
      rendered.onerror = () => setDownloading(false);
      rendered.src = objectUrl;
    } catch {
      setDownloading(false);
    }
  };

  return (
    <div className="log-card">
      <div className="log-toolbar">
        <div><span className="eyebrow">Driver&apos;s daily log</span><h3>{date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</h3></div>
        <button className="secondary-button" onClick={download} disabled={downloading}>{downloading ? "Preparing…" : "Download PNG"}</button>
      </div>
      <div className="paper-wrap">
        <svg ref={svgRef} className="log-sheet" viewBox="0 0 513 486" role="img" aria-label={`Filled ELD log for ${log.date}`}>
          <image href="/blank-paper-log.png" width="513" height="486" />
          <g className="log-fill-text">
            <text x="181" y="29">{month}</text><text x="206" y="29">{day}</text><text x="232" y="29">{year}</text>
            <text x="62" y="45">{plan.locations.current.label.slice(0, 34)}</text>
            <text x="278" y="45">{plan.locations.dropoff.label.slice(0, 34)}</text>
            <text x="73" y="112">{Math.round(plan.route.distance_miles)}</text>
            <text x="289" y="90">LogRoute Demo Carrier</text>
            <text x="289" y="111">123 Safety Way, Chicago, IL</text>
            <text x="289" y="132">Chicago, IL</text>
            <text x="468" y="195">{totals.off_duty.toFixed(2)}</text>
            <text x="468" y="212">{totals.sleeper_berth.toFixed(2)}</text>
            <text x="468" y="228">{totals.driving.toFixed(2)}</text>
            <text x="468" y="245">{totals.on_duty.toFixed(2)}</text>
          </g>
          <polyline className="duty-line duty-line-shadow" points={linePoints(log.events)} />
          <polyline className="duty-line" points={linePoints(log.events)} />
          <g className="remarks-fill">
            {remarks.map((event, index) => <text key={`${event.title}-${index}`} x="25" y={288 + index * 15}>{`${event.start_hour.toFixed(2)} — ${event.title}`}</text>)}
          </g>
        </svg>
      </div>
      <div className="log-totals">
        <span><i className="status-off" />Off duty <b>{totals.off_duty.toFixed(2)}h</b></span>
        <span><i className="status-sleeper" />Sleeper <b>{totals.sleeper_berth.toFixed(2)}h</b></span>
        <span><i className="status-driving" />Driving <b>{totals.driving.toFixed(2)}h</b></span>
        <span><i className="status-duty" />On duty <b>{totals.on_duty.toFixed(2)}h</b></span>
      </div>
    </div>
  );
}

