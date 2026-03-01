"use client";
import { useEffect, useState } from "react";
import { getContributions } from "@/lib/api";
import { toISODate } from "@/lib/utils";

// light → dark teal gradient; COLORS[0] = empty (muted, visible on dark card)
const COLORS = ["#3a4060", "#b2ebf2", "#4dd0e1", "#0097a7", "#006064"];
function color(n: number, max: number) {
    if (!n) return COLORS[0];
    const idx = Math.round((n / max) * (COLORS.length - 2)) + 1; // 1…4
    return COLORS[Math.min(idx, COLORS.length - 1)];
}

/** Build a grid of 52 columns × 7 rows (Sun–Sat), ending on today */
function buildWeeks(): (Date | null)[][] {
    const today = new Date();
    today.setHours(23, 59, 59, 999); // treat whole of today as valid

    // Find the Sunday that starts today's week
    const dayOfWeek = today.getDay(); // 0=Sun … 6=Sat
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - dayOfWeek);
    weekStart.setHours(0, 0, 0, 0);

    // Go back 51 more weeks to get 52 total
    const gridStart = new Date(weekStart);
    gridStart.setDate(weekStart.getDate() - 51 * 7);

    const weeks: (Date | null)[][] = [];
    let cur = new Date(gridStart);

    while (weeks.length < 52) {
        const week: (Date | null)[] = [];
        for (let i = 0; i < 7; i++) {
            const d = new Date(cur);
            d.setDate(cur.getDate() + i);
            d.setHours(0, 0, 0, 0);
            week.push(d <= today ? d : null);
        }
        weeks.push(week);
        cur.setDate(cur.getDate() + 7);
    }
    return weeks;
}

export default function ContributionChart() {
    const [data, setData] = useState<Record<string, number>>({});
    const [maxCount, setMax] = useState(0);

    useEffect(() => {
        getContributions()
            .then((r) => { setData(r.contributions); setMax(r.max_count); })
            .catch((err) => {
                console.error("ContributionChart: failed to load contributions", err);
            });
    }, []);

    const weeks = buildWeeks();

    return (
        <div className="heatmap-card">
            <div className="heatmap-title">Daily Pulse</div>

            {/* Grid: 52 columns of 7 cells */}
            <div style={{ display: "flex", gap: "2px", justifyContent: "space-between", width: "100%" }}>
                {weeks.map((week, wi) => (
                    <div key={wi} style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                        {week.map((day, di) => {
                            if (!day) return <div key={di} style={{ width: 11, height: 11 }} />;
                            const key = toISODate(day);
                            const cnt = data[key] ?? 0;
                            const title = `${day.toLocaleDateString("en-US", { month: "short", day: "numeric" })}: ${cnt} task${cnt !== 1 ? "s" : ""}`;
                            return (
                                <div
                                    key={di}
                                    title={title}
                                    style={{
                                        width: 11, height: 11,
                                        borderRadius: 2,
                                        background: color(cnt, maxCount),
                                        cursor: "default",
                                    }}
                                />
                            );
                        })}
                    </div>
                ))}
            </div>

            {/* Legend */}
            <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 8 }}>
                <span style={{ fontSize: "0.65rem", color: "rgba(255,255,255,0.4)" }}>Less</span>
                {COLORS.map((c, i) => (
                    <div key={i} style={{ width: 11, height: 11, borderRadius: 2, background: c }} />
                ))}
                <span style={{ fontSize: "0.65rem", color: "rgba(255,255,255,0.4)" }}>More</span>
            </div>
        </div>
    );
}
