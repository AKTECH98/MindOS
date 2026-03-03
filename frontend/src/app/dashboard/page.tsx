"use client";
import { useState, useCallback } from "react";
import XPBar from "@/components/XPBar";
import ContributionChart from "@/components/ContributionChart";
import StatsPanel from "@/components/StatsPanel";
import CalendarEventsView from "@/components/CalendarEventsView";

export default function DashboardPage() {
    const [xpRefreshKey, setXpRefreshKey] = useState(0);
    const handleXPChange = useCallback(() => setXpRefreshKey((k) => k + 1), []);

    return (
        <div>
            {/* Top row: XPBar + Heatmap | Stats */}
            <div className="dash-top">
                {/* Centre: XP progress bar above Daily Pulse heatmap */}
                <div className="dash-center">
                    <XPBar refreshKey={xpRefreshKey} />
                    <ContributionChart />
                </div>

                {/* Right: Stats */}
                <StatsPanel />
            </div>

            {/* Divider */}
            <hr style={{ border: "none", borderTop: "1px solid #d8dce8", margin: "0.5rem 0 1.5rem" }} />

            {/* Task management section */}
            <CalendarEventsView onXPChange={handleXPChange} />
        </div>
    );
}
