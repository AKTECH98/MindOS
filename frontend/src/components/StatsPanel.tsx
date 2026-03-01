"use client";
import { useEffect, useState } from "react";
import { getStatsOverview } from "@/lib/api";

export default function StatsPanel() {
    const [stats, setStats] = useState<{
        total_completed: number; completed_today: number;
        completed_this_week: number; current_streak_days: number;
    } | null>(null);

    useEffect(() => {
        getStatsOverview()
            .then(setStats)
            .catch((err) => {
                console.error("StatsPanel: failed to load stats", err);
            });
    }, []);

    const totalDays = stats ? Math.ceil(stats.total_completed / Math.max(1, stats.completed_this_week / 7)) : 0;
    const avgPerDay = stats && totalDays > 0 ? (stats.total_completed / Math.max(50, totalDays)).toFixed(1) : "0.0";

    return (
        <div className="stats-card">
            <div className="stats-card-title">Stats</div>
            <div className="stats-item">
                <div className="stats-value">{stats?.total_completed ?? "—"}</div>
                <div className="stats-label">Tasks</div>
            </div>
            <div className="stats-item">
                <div className="stats-value">{stats?.current_streak_days ?? "—"}</div>
                <div className="stats-label">Active Days</div>
            </div>
            <div className="stats-item">
                <div className="stats-value">{avgPerDay}</div>
                <div className="stats-label">Avg / Day</div>
            </div>
        </div>
    );
}
