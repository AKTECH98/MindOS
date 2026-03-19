"use client";
import XPBar from "@/components/XPBar";
import InternalTasksView from "@/components/InternalTasksView";

export default function HomePage() {
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
        <XPBar refreshKey={0} />
        <InternalTasksView compact />
      </div>
    </div>
  );
}
