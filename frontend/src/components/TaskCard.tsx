"use client";
import { useState, useEffect, useRef } from "react";
import {
    markTaskDone, markTaskUndone,
    startSession, pauseSession,
    getCurrentDuration, getTimeSpent,
} from "@/lib/api";
import { fmtSeconds, toISODate } from "@/lib/utils";
import type { CalendarEvent, TaskCompletionStatus } from "@/lib/api";

interface Props {
    event: CalendarEvent;
    status: TaskCompletionStatus | null;
    onStatusChange: () => void;
    date: string; // ISO date string (YYYY-MM-DD) for the selected day
}

export default function TaskCard({ event, status, onStatusChange, date }: Props) {
    const isDone = status?.is_done ?? false;
    const [running, setRunning] = useState(false);
    const [liveSeconds, setLiveSeconds] = useState(0); // seconds for the currently-active session
    const [daySeconds, setDaySeconds] = useState<number | null>(null); // total for the viewed day
    const [showModal, setShowModal] = useState(false);
    const [desc, setDesc] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const pollRef = useRef<NodeJS.Timeout | null>(null);

    const today = toISODate(new Date());
    const isPast = date < today;

    // On mount (and when date changes): fetch time spent for the selected day
    useEffect(() => {
        getTimeSpent(event.id, date)
            .then((r) => setDaySeconds(r.total_seconds))
            .catch(() => setDaySeconds(0));
    }, [event.id, date]);

    // Poll live duration every second (updates liveSeconds + running state)
    useEffect(() => {
        const poll = async () => {
            try {
                const r = await getCurrentDuration(event.id);
                setRunning(r.is_running);
                setLiveSeconds(r.duration_seconds ?? 0);
            } catch { /* ignore */ }
        };
        poll();
        pollRef.current = setInterval(poll, 1000);
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, [event.id]);

    const handleCheck = (checked: boolean) => {
        if (checked) { setShowModal(true); }
        else { handleUndone(); }
    };

    const handleUndone = async () => {
        try { await markTaskUndone(event.id, date); onStatusChange(); } catch { /* ignore */ }
    };

    const handleConfirmDone = async () => {
        if (!desc.trim()) return;
        setSubmitting(true);
        try {
            if (running) {
                await pauseSession(event.id);
                setRunning(false);
            }
            await markTaskDone(event.id, desc.trim(), date);
            setShowModal(false);
            setDesc("");
            onStatusChange();
            // Refresh day's total after marking done and potentially pausing
            const r = await getTimeSpent(event.id, date);
            setDaySeconds(r.total_seconds);
        } catch { /* ignore */ }
        finally { setSubmitting(false); }
    };

    const handlePlay = async () => {
        try {
            await startSession(event.id);
            setRunning(true);
        } catch { /* ignore */ }
    };
    const handlePause = async () => {
        try {
            await pauseSession(event.id);
            setRunning(false);
            // Refresh day's total after pausing
            const r = await getTimeSpent(event.id, date);
            setDaySeconds(r.total_seconds);
        } catch { /* ignore */ }
    };

    // What to display:
    // - If running: show the live ticking session duration
    // - Otherwise: show day's total (if > 0)
    const displaySeconds = running ? liveSeconds : (daySeconds ?? 0);
    const timeStr = displaySeconds > 0 ? fmtSeconds(displaySeconds) : null;

    return (
        <>
            <div className="task-row" style={{ position: "relative" }}>
                {/* Checkbox */}
                <input
                    type="checkbox"
                    className="task-checkbox"
                    checked={isDone}
                    disabled={isPast}
                    onChange={(e) => handleCheck(e.target.checked)}
                />

                {/* Task name */}
                <span className={`task-label${isDone ? " done" : ""}`}>{event.title}</span>

                {/* Time display — always visible when there is time data */}
                {timeStr && (
                    <span
                        className="task-timer-label"
                        title={running ? "Live session time" : "Total time spent today"}
                        style={{ color: running ? "var(--teal)" : undefined }}
                    >
                        {running && "▶ "}{timeStr}
                    </span>
                )}

                {/* Action buttons — only for today's tasks and pending tasks */}
                {!isDone && !isPast && (
                    running ? (
                        <>
                            <button className="btn-pause" onClick={handlePause} title="Pause">⏸</button>
                            <button className="btn-stop" onClick={() => setShowModal(true)} title="Stop & mark done">⏹</button>
                        </>
                    ) : (
                        <button className="btn-play" onClick={handlePlay}>▶</button>
                    )
                )}
            </div>

            {/* Description modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-box" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-title">✏️ What did you accomplish?</div>
                        <p style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.75rem" }}>
                            <strong>{event.title}</strong>
                        </p>
                        <textarea
                            className="modal-textarea"
                            placeholder="Describe what you completed..."
                            value={desc}
                            onChange={(e) => setDesc(e.target.value)}
                            autoFocus
                        />
                        <div className="modal-actions">
                            <button className="btn-cancel" onClick={() => { setShowModal(false); setDesc(""); }}>Cancel</button>
                            <button className="btn-confirm" onClick={handleConfirmDone} disabled={submitting || !desc.trim()}>
                                {submitting ? "Saving..." : "Mark Done ✅"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
