import { useState } from "react";
import { localIsoMinute, toDatetimeLocal } from "../utils";

const SAMPLE = {
  current_location: "Chicago, IL",
  pickup_location: "Indianapolis, IN",
  dropoff_location: "Atlanta, GA",
  current_cycle_used: "18.5",
  departure_time: toDatetimeLocal(),
};

export default function TripForm({ loading, onSubmit }) {
  const [form, setForm] = useState(SAMPLE);

  const update = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const submit = (event) => {
    event.preventDefault();
    const departure = new Date(form.departure_time);
    onSubmit({
      ...form,
      current_cycle_used: Number(form.current_cycle_used),
      departure_time: Number.isNaN(departure.getTime()) ? localIsoMinute() : localIsoMinute(departure),
    });
  };

  return (
    <form className="trip-form" onSubmit={submit}>
      <div className="form-heading">
        <div>
          <span className="eyebrow">New dispatch</span>
          <h2>Plan a compliant run</h2>
        </div>
        <span className="rule-badge"><i />70 hr / 8 day</span>
      </div>

      <div className="location-stack">
        <label>
          <span><b className="dot dot-start" />Current location</span>
          <input name="current_location" value={form.current_location} onChange={update} required placeholder="City, state or address" />
        </label>
        <label>
          <span><b className="dot dot-pickup" />Pickup</span>
          <input name="pickup_location" value={form.pickup_location} onChange={update} required placeholder="Pickup city or address" />
        </label>
        <label>
          <span><b className="dot dot-drop" />Drop-off</span>
          <input name="dropoff_location" value={form.dropoff_location} onChange={update} required placeholder="Drop-off city or address" />
        </label>
      </div>

      <div className="form-grid">
        <label>
          <span>Cycle used</span>
          <div className="input-suffix">
            <input name="current_cycle_used" type="number" min="0" max="70" step="0.25" value={form.current_cycle_used} onChange={update} required />
            <em>hours</em>
          </div>
        </label>
        <label>
          <span>Departure</span>
          <input name="departure_time" type="datetime-local" value={form.departure_time} onChange={update} required />
        </label>
      </div>

      <button className="primary-button" disabled={loading} type="submit">
        {loading ? <><span className="spinner" />Building route…</> : <>Build trip plan <span aria-hidden="true">→</span></>}
      </button>
      <p className="form-note">Uses OpenStreetMap routing and conservative FMCSA planning assumptions.</p>
    </form>
  );
}

