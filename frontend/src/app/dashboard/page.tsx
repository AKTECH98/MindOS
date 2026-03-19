"use client";
import XPBar from "@/components/XPBar";
import ContributionChart from "@/components/ContributionChart";
import StatsPanel from "@/components/StatsPanel";
import InternalTasksView from "@/components/InternalTasksView";

export default function DashboardPage() {
    return (
        <div>
            {/* Top row: XPBar + Heatmap | Stats */}
            <div className="dash-top">
                {/* Centre: XP progress bar above Daily Pulse heatmap */}
                <div className="dash-center">
                    <XPBar refreshKey={0} />
                    <ContributionChart />
                </div>

                {/* Right: Stats */}
                <StatsPanel />
            </div>

            {/* Divider */}
            <hr style={{ border: "none", borderTop: "1px solid #d8dce8", margin: "0.5rem 0 1.5rem" }} />

            {/* Task management section */}
            <InternalTasksView />
        </div>
    );
}
