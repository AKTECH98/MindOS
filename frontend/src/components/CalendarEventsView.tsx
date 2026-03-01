"use client";
import { useCallback, useEffect, useState } from "react";
import {
    CalendarEvent, TaskCompletionStatus,
    getCalendarStatus, getCalendarEvents, getBatchCompletionStatus,
} from "@/lib/api";
import { toISODate } from "@/lib/utils";
import TaskCard from "./TaskCard";

interface Props {
    compact?: boolean; // true = compact task list (Home), false = two-column (Dashboard)
}

export default function CalendarEventsView({ compact = false }: Props) {
    const [authenticated, setAuthenticated] = useState<boolean | null>(null);
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [statuses, setStatuses] = useState<Record<string, TaskCompletionStatus>>({});
    const [selectedDate, setSelectedDate] = useState(toISODate(new Date()));
    const [loading, setLoading] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const { authenticated: auth } = await getCalendarStatus();
            setAuthenticated(auth);
            if (!auth) { setLoading(false); return; }
            const evts = await getCalendarEvents(selectedDate);
            setEvents(evts);
            if (evts.length) {
                const ids = evts.map((e) => e.id);
                const { statuses: s } = await getBatchCompletionStatus(ids, selectedDate);
                setStatuses(s);
            } else { setStatuses({}); }
        } catch (err) {
            console.error("CalendarEventsView: failed to load", err);
        }
        setLoading(false);
    }, [selectedDate]);

    useEffect(() => { load(); }, [load]);

    const pending = events.filter((e) => !statuses[e.id]?.is_done);
    const done = events.filter((e) => statuses[e.id]?.is_done);

    const dateLabel = new Date(selectedDate + "T12:00:00").toLocaleDateString("en-US", {
        month: "long", day: "2-digit", year: "numeric",
    });

    if (authenticated === false) {
        return (
            <div style={{ color: "#888", padding: "1rem 0", fontSize: "0.9rem" }}>
                🔒 Google Calendar not authenticated. Authenticate via{" "}
                <a href="http://localhost:8501" target="_blank" rel="noopener" style={{ color: "var(--teal)" }}>the backend CLI</a>{" "}
                first, then refresh.
            </div>
        );
    }

    return (
        <>
            {/* Date + controls row — only on Dashboard */}
            {!compact && (
                <div className="tasks-section-header">
                    <div className="tasks-date-label">{dateLabel} - Tasks</div>
                    <div className="tasks-controls">
                        <input
                            type="date"
                            className="tasks-date-input"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                        />
                        <button className="btn-action" onClick={load}>🔄 Refresh</button>
                    </div>
                </div>
            )}

            {loading && <p className="loading">Loading events...</p>}

            {!loading && (
                compact ? (
                    /* ── Home compact: single task list in a card ── */
                    <div className="tasks-card">
                        <div className="tasks-card-title">Tasks</div>
                        {events.length === 0
                            ? <p className="no-tasks">No events for this date.</p>
                            : events.map((ev) => (
                                <TaskCard
                                    key={ev.id}
                                    event={ev}
                                    status={statuses[ev.id] ?? null}
                                    onStatusChange={load}
                                    date={selectedDate}
                                />
                            ))}
                    </div>
                ) : (
                    /* ── Dashboard: two-column pending | done ── */
                    <div className="tasks-columns">
                        <div>
                            <div className="tasks-col-title">⏳ Pending Tasks ({pending.length})</div>
                            {pending.length === 0
                                ? <p className="no-tasks">All done! 🎉</p>
                                : <div className="tasks-card">
                                    {pending.map((ev) => (
                                        <TaskCard key={ev.id} event={ev} status={statuses[ev.id] ?? null} onStatusChange={load} date={selectedDate} />
                                    ))}
                                </div>}
                        </div>
                        <div>
                            <div className="tasks-col-title">✅ Done Tasks ({done.length})</div>
                            {done.length === 0
                                ? <p className="no-tasks">No completed tasks yet.</p>
                                : <div className="tasks-card">
                                    {done.map((ev) => (
                                        <TaskCard key={ev.id} event={ev} status={statuses[ev.id] ?? null} onStatusChange={load} date={selectedDate} />
                                    ))}
                                </div>}
                        </div>
                    </div>
                )
            )}
        </>
    );
}
