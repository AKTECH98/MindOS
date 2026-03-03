"use client";
import { useState, useCallback } from "react";
import XPBar from "@/components/XPBar";
import CalendarEventsView from "@/components/CalendarEventsView";

export default function HomePage() {
  const [xpRefreshKey, setXpRefreshKey] = useState(0);
  const handleXPChange = useCallback(() => setXpRefreshKey((k) => k + 1), []);

  return (
    <div className="home-grid">
      {/* Centre: title + subtitle + input */}
      <div className="home-center">
        <h1 className="home-title">MindOS</h1>
        <p className="home-subtitle">What&apos;s on Your Mind Today</p>
        <input className="home-input" placeholder="Type here..." />
      </div>

      {/* Right: Level + XP bar + Tasks directly below */}
      <div className="side-panel">
        <XPBar refreshKey={xpRefreshKey} />
        <CalendarEventsView compact onXPChange={handleXPChange} />
      </div>
    </div>
  );
}
