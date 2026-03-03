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
    // liveSeconds = base elapsed seconds from server + client-side ticks since start
    const [liveSeconds, setLiveSeconds] = useState(0);
    const [daySeconds, setDaySeconds] = useState<number | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [desc, setDesc] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const tickRef = useRef<NodeJS.Timeout | null>(null);
    // Timestamp (Date.now()) when the current local tick started, so we can compute elapsed without polling
    const tickStartRef = useRef<number | null>(null);
    // Server-confirmed base seconds at tick start
    const baseSecondsRef = useRef<number>(0);

    const today = toISODate(new Date());
    const isPast = date < today;

    const startTicking = (baseSeconds: number) => {
        stopTicking();
        baseSecondsRef.current = baseSeconds;
        tickStartRef.current = Date.now();
        setLiveSeconds(baseSeconds);
        tickRef.current = setInterval(() => {
            const elapsed = Math.floor((Date.now() - (tickStartRef.current ?? Date.now())) / 1000);
            setLiveSeconds(baseSecondsRef.current + elapsed);
        }, 1000);
    };

    const stopTicking = () => {
        if (tickRef.current) {
            clearInterval(tickRef.current);
            tickRef.current = null;
        }
        tickStartRef.current = null;
    };

    // On mount (and when event/date changes): init state from server
    useEffect(() => {
        const init = async () => {
            try {
                // Fetch both: total time spent today AND if a session is running right now
                const [timeRes, durRes] = await Promise.all([
                    getTimeSpent(event.id, date),
                    getCurrentDuration(event.id)
                ]);

                setDaySeconds(timeRes.total_seconds);

                if (durRes.is_running) {
                    setRunning(true);
                    // Start ticking from the full day total (which includes the running session)
                    startTicking(timeRes.total_seconds);
                }
            } catch (err) {
                setDaySeconds(0);
            }
        };

        init();
        return () => stopTicking();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [event.id, date]);

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
                stopTicking();
                setRunning(false);
            }
            await markTaskDone(event.id, desc.trim(), date);
            setShowModal(false);
            setDesc("");
            onStatusChange();
            const r = await getTimeSpent(event.id, date);
            setDaySeconds(r.total_seconds);
        } catch { /* ignore */ }
        finally { setSubmitting(false); }
    };

    const handlePlay = async () => {
        try {
            const r = await startSession(event.id);
            if (r.success) {
                setRunning(true);
                // Start ticking from current daySeconds as the base (server accumulates on top)
                startTicking(daySeconds ?? 0);
            }
        } catch { /* ignore */ }
    };

    const handlePause = async () => {
        // Optimistically stop the tick so the UI freezes immediately
        const frozenSeconds = liveSeconds;
        stopTicking();
        setRunning(false);
        try {
            await pauseSession(event.id);
            // Refresh day total from server (source of truth after pause)
            const r = await getTimeSpent(event.id, date);
            setDaySeconds(r.total_seconds);
        } catch {
            // Rollback: server is unreachable — resume ticking from where we froze
            setRunning(true);
            startTicking(frozenSeconds);
        }
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

