"use client";
import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    listCountdowns,
    startCountdown,
    pauseCountdown,
    createCountdown,
    deleteCountdown
} from "@/lib/api";
import type { CountdownResponse } from "@/lib/api";

interface DialProps {
    label: string;
    value: number | string;
    editable?: boolean;
    onChange?: (val: string) => void;
    onInc?: () => void;
    onDec?: () => void;
}

function Dial({ label, value, editable, onChange, onInc, onDec }: DialProps) {
    return (
        <div className="countdown-dial">
            <style dangerouslySetInnerHTML={{
                __html: `
                input[type=number]::-webkit-inner-spin-button, 
                input[type=number]::-webkit-outer-spin-button { 
                    -webkit-appearance: none; 
                    margin: 0; 
                }
                input[type=number] {
                    -moz-appearance: textfield;
                }
            `}} />
            <span className="countdown-dial-label">{label}</span>
            <div className="countdown-dial-circle" style={{ position: "relative" }}>
                {editable ? (
                    <input
                        type="number"
                        value={value}
                        onChange={(e) => onChange?.(e.target.value)}
                        onFocus={(e) => e.target.select()}
                        style={{
                            width: "100%",
                            height: "100%",
                            background: "transparent",
                            border: "none",
                            outline: "none",
                            color: "#fff",
                            textAlign: "center",
                            fontSize: "1rem",
                            fontWeight: "700",
                            fontFamily: "inherit",
                            margin: 0
                        }}
                    />
                ) : (
                    String(value).padStart(2, "0")
                )}
            </div>
            {editable && (
                <div style={{ display: "flex", gap: "4px", marginTop: "6px" }}>
                    <button
                        onClick={onDec}
                        style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "#fff", borderRadius: "4px", width: "18px", height: "18px", cursor: "pointer", fontSize: "0.8rem", display: "flex", alignItems: "center", justifyContent: "center" }}
                    >
                        −
                    </button>
                    <button
                        onClick={onInc}
                        style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "#fff", borderRadius: "4px", width: "18px", height: "18px", cursor: "pointer", fontSize: "0.8rem", display: "flex", alignItems: "center", justifyContent: "center" }}
                    >
                        +
                    </button>
                </div>
            )}
        </div>
    );
}

function CountdownCard({
    timer: initialTimer,
    onDelete
}: {
    timer: CountdownResponse;
    onDelete: () => void;
}) {
    const [timer, setTimer] = useState(initialTimer);
    const [localRemaining, setLocalRemaining] = useState(initialTimer.remaining_seconds);
    const [isDeleting, setIsDeleting] = useState(false);
    const tickRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        setTimer(initialTimer);
        setLocalRemaining(initialTimer.remaining_seconds);
    }, [initialTimer]);

    useEffect(() => {
        if (timer.is_running && localRemaining > 0) {
            tickRef.current = setInterval(() => {
                setLocalRemaining(prev => Math.max(0, prev - 1));
            }, 1000);
        } else {
            if (tickRef.current) clearInterval(tickRef.current);
            tickRef.current = null;
        }
        return () => { if (tickRef.current) clearInterval(tickRef.current); };
    }, [timer.is_running]);

    const handleToggle = async () => {
        try {
            const res = timer.is_running
                ? await pauseCountdown(timer.id)
                : await startCountdown(timer.id);
            setTimer(res);
            setLocalRemaining(res.remaining_seconds);
        } catch (err) {
            console.error("CountdownCard: toggle failed", err);
        }
    };

    const confirmDelete = async () => {
        try {
            await deleteCountdown(timer.id);
            onDelete();
        } catch (err) {
            console.error("CountdownCard: delete failed", err);
            setIsDeleting(false);
        }
    };

    const progress = Math.min(100, Math.round((localRemaining / timer.total_seconds) * 10000) / 100);
    const dd = Math.floor(localRemaining / 86400);
    const hh = Math.floor((localRemaining % 86400) / 3600);
    const mm = Math.floor((localRemaining % 3600) / 60);
    const ss = Math.floor(localRemaining % 60);

    return (
        <div className="countdown-card" style={{ position: "relative", overflow: "hidden" }}>
            {isDeleting && (
                <div style={{
                    position: "absolute",
                    inset: 0,
                    zIndex: 10,
                    background: "rgba(0, 0, 0, 0.7)",
                    backdropFilter: "blur(4px)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "1rem",
                    textAlign: "center"
                }}>
                    <div style={{ fontSize: "0.85rem", color: "#fff", marginBottom: "12px", fontWeight: 700 }}>Delete this goal?</div>
                    <div style={{ display: "flex", gap: "8px", width: "100%" }}>
                        <button
                            onClick={() => setIsDeleting(false)}
                            style={{ flex: 1, background: "rgba(255,255,255,0.15)", border: "none", borderRadius: "20px", color: "#fff", padding: "8px", fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={confirmDelete}
                            style={{ flex: 1, background: "#ef4444", border: "none", borderRadius: "20px", color: "#fff", padding: "8px", fontSize: "0.75rem", cursor: "pointer", fontWeight: 600 }}
                        >
                            Delete
                        </button>
                    </div>
                </div>
            )}

            <div className="countdown-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <div className="countdown-title" style={{ margin: 0, fontSize: "0.9rem", opacity: 0.9 }}>{timer.name}</div>
                <div style={{ display: "flex", gap: "8px" }}>
                    <button
                        onClick={handleToggle}
                        style={{ background: "none", border: "none", cursor: "pointer", color: "var(--teal)", fontSize: "1rem", padding: 0 }}
                        title={timer.is_running ? "Pause" : "Start"}
                    >
                        {timer.is_running ? "⏸" : "▶"}
                    </button>
                    <button
                        onClick={() => setIsDeleting(true)}
                        style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", padding: 4, display: "flex", alignItems: "center", justifyContent: "center" }}
                        title="Delete"
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div className="countdown-bar">
                <div className="countdown-bar-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="countdown-dials">
                <Dial label="DD" value={dd} />
                <Dial label="HH" value={hh} />
                <Dial label="MM" value={mm} />
                <Dial label="SS" value={ss} />
            </div>
        </div>
    );
}

export default function Sidebar() {
    const pathname = usePathname();
    const [timers, setTimers] = useState<CountdownResponse[]>([]);
    const [showAdd, setShowAdd] = useState(false);

    // Form state
    const [newName, setNewName] = useState("");
    const [newDays, setNewDays] = useState("0");
    const [newHours, setNewHours] = useState("0");
    const [newMins, setNewMins] = useState("0");
    const [newSecs, setNewSecs] = useState("0");

    const [mounted, setMounted] = useState(false);

    const loadTimers = async () => {
        try {
            const list = await listCountdowns();
            setTimers(list);
        } catch (err) {
            console.error("Sidebar: failed to load timers", err);
        }
    };

    useEffect(() => {
        setMounted(true);
        loadTimers();
    }, []);

    const handleCreate = async () => {
        const d = parseInt(newDays) || 0;
        const h = parseInt(newHours) || 0;
        const m = parseInt(newMins) || 0;
        const s = parseInt(newSecs) || 0;

        const totalSeconds = (d * 86400) + (h * 3600) + (m * 60) + s;
        if (totalSeconds <= 0) return;

        let finalName = newName.trim();
        if (!finalName) {
            finalName = `Timer ${timers.length + 1} Countdown`;
        }

        try {
            const res = await createCountdown(finalName, totalSeconds);
            // Auto-start the timer immediately
            await startCountdown(res.id);

            setNewName("");
            setNewDays("0");
            setNewHours("0");
            setNewMins("0");
            setNewSecs("0");
            setShowAdd(false);
            loadTimers();
        } catch (err) {
            alert("Failed to create timer. Name might already exist.");
        }
    };

    const adjust = (setter: React.Dispatch<React.SetStateAction<string>>, amount: number) => {
        setter(prev => String(Math.max(0, (parseInt(prev) || 0) + amount)));
    };

    if (!mounted) return null;

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <span>⊙</span>
                <span>MindOS</span>
            </div>

            <Link href="/" className={`nav-link${pathname === "/" ? " active" : ""}`}>🏠 Home</Link>
            <Link href="/dashboard" className={`nav-link${pathname === "/dashboard" ? " active" : ""}`}>📊 Dashboard</Link>

            <hr className="nav-divider" />

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "0 4px", marginBottom: "16px" }}>
                <div style={{ display: "flex", gap: "8px" }}>
                    <button
                        onClick={() => setShowAdd(!showAdd)}
                        className="action-btn"
                        style={{
                            flex: 1,
                            padding: "10px",
                            fontSize: "0.85rem",
                            fontWeight: 700,
                            borderRadius: "50px",
                            background: showAdd ? "rgba(255,255,255,0.1)" : "var(--teal)",
                            border: "none",
                            boxShadow: "none",
                            outline: "none",
                            color: "#fff",
                            cursor: "pointer"
                        }}
                    >
                        {showAdd ? "Cancel" : "Add Timer"}
                    </button>
                    <button
                        className="action-btn"
                        style={{
                            flex: 1,
                            padding: "10px",
                            fontSize: "0.85rem",
                            fontWeight: 700,
                            borderRadius: "50px",
                            opacity: 0.5,
                            border: "none",
                            boxShadow: "none",
                            outline: "none",
                            color: "#fff",
                            background: "rgba(0,0,0,0.1)"
                        }}
                        disabled
                    >
                        Focus Mode
                    </button>
                </div>

                {showAdd && (
                    <div className="countdown-card" style={{ marginTop: "12px", border: "1px solid var(--teal)", margin: "12px -16px 0" }}>
                        <div className="countdown-header" style={{ marginBottom: "1rem" }}>
                            <input
                                className="task-input"
                                placeholder="Goal Name..."
                                value={newName}
                                onChange={e => setNewName(e.target.value)}
                                style={{
                                    fontSize: "0.85rem",
                                    padding: "8px 12px",
                                    background: "rgba(255,255,255,0.05)",
                                    border: "none",
                                    borderRadius: "6px",
                                    color: "#fff",
                                    width: "100%"
                                }}
                                autoFocus
                            />
                        </div>
                        <div className="countdown-dials" style={{ marginBottom: "1.25rem", gap: "0.5rem" }}>
                            <Dial
                                label="DD" value={newDays} editable
                                onChange={setNewDays}
                                onInc={() => adjust(setNewDays, 1)}
                                onDec={() => adjust(setNewDays, -1)}
                            />
                            <Dial
                                label="HH" value={newHours} editable
                                onChange={setNewHours}
                                onInc={() => adjust(setNewHours, 1)}
                                onDec={() => adjust(setNewHours, -1)}
                            />
                            <Dial
                                label="MM" value={newMins} editable
                                onChange={setNewMins}
                                onInc={() => adjust(setNewMins, 1)}
                                onDec={() => adjust(setNewMins, -1)}
                            />
                            <Dial
                                label="SS" value={newSecs} editable
                                onChange={setNewSecs}
                                onInc={() => adjust(setNewSecs, 1)}
                                onDec={() => adjust(setNewSecs, -1)}
                            />
                        </div>
                        <div style={{ display: "flex", gap: "8px" }}>
                            <button
                                onClick={() => setShowAdd(false)}
                                style={{ flex: 1, background: "rgba(255,255,255,0.1)", border: "none", borderRadius: "20px", color: "#fff", padding: "10px", fontSize: "0.85rem", cursor: "pointer", fontWeight: 600 }}
                            >
                                CANCEL
                            </button>
                            <button
                                onClick={handleCreate}
                                style={{ flex: 1, background: "var(--teal)", border: "none", borderRadius: "20px", color: "#fff", padding: "10px", fontSize: "0.85rem", cursor: "pointer", fontWeight: 600 }}
                            >
                                START
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", overflowY: "auto", paddingBottom: "20px" }}>
                {timers.map(t => (
                    <CountdownCard key={t.id} timer={t} onDelete={loadTimers} />
                ))}
            </div>
        </aside>
    );
}
