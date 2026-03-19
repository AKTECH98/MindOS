"use client";
import { useState, useEffect, useCallback } from "react";
import { Task, listTasks, createTask, updateTask, deleteTask } from "@/lib/api";

/**
 * Formats seconds into a human-readable string like '2h 30m' or '45m'.
 */
function formatSeconds(totalSeconds: number | null | undefined): string {
    if (totalSeconds == null || totalSeconds <= 0) return "";
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    return parts.length > 0 ? parts.join(" ") : "0m";
}

/**
 * Parses a time string like '1h 30m', '2h', or '45m' into total seconds.
 */
function parseTimeToSeconds(input: string): number | null {
    if (!input) return null;
    const timeStr = input.toLowerCase().trim();
    if (!timeStr) return null;

    let totalSeconds = 0;
    const hMatch = timeStr.match(/(\d+)\s*h/);
    const mMatch = timeStr.match(/(\d+)\s*m/);

    if (hMatch) totalSeconds += parseInt(hMatch[1], 10) * 3600;
    if (mMatch) totalSeconds += parseInt(mMatch[1], 10) * 60;

    // Fallback: if no h/m but starts with number, assume minutes
    if (!hMatch && !mMatch && /^\d+$/.test(timeStr)) {
        totalSeconds = parseInt(timeStr, 10) * 60;
    }

    return totalSeconds > 0 ? totalSeconds : null;
}

interface Props {
    compact?: boolean;
    onXPChange?: () => void;
}

interface TaskRowProps {
    task: Task;
    depth: number;
    onRefresh: () => void;
}

import { startSession, pauseSession, getCurrentDuration } from "@/lib/api";

function TaskRow({ task, depth, onRefresh }: TaskRowProps) {
    const [expanded, setExpanded] = useState(false);
    const [subtasks, setSubtasks] = useState<Task[]>([]);
    const [loadingChildren, setLoadingChildren] = useState(false);
    const [showAddSub, setShowAddSub] = useState(false);
    const [newSubName, setNewSubName] = useState("");
    const [editingProgress, setEditingProgress] = useState(false);
    const [progress, setProgress] = useState(task.progress);
    const [savingProgress, setSavingProgress] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [editingName, setEditingName] = useState(false);
    const [editName, setEditName] = useState(task.task_name);
    
    // Session state
    const [isRunning, setIsRunning] = useState(false);
    const [sessionSeconds, setSessionSeconds] = useState(task.time_spent);

    useEffect(() => {
        let timer: any;
        if (isRunning) {
            timer = setInterval(() => {
                setSessionSeconds(s => s + 1);
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [isRunning]);

    // Initial check for session
    useEffect(() => {
        getCurrentDuration(task.task_id).then(res => {
            if (res.is_running) {
                setIsRunning(true);
            }
        }).catch(() => {});
    }, [task.task_id]);

    const handleStart = async () => {
        try {
            await startSession(task.task_id);
            setIsRunning(true);
        } catch {}
    };

    const handlePause = async () => {
        try {
            await pauseSession(task.task_id);
            setIsRunning(false);
            onRefresh(); // Get final sync from DB
        } catch {}
    };

    const handleMarkDone = async () => {
        try {
            await updateTask(task.task_id, { progress: 100 });
            setProgress(100);
            onRefresh();
        } catch {}
    };

    const loadSubtasks = useCallback(async () => {
        setLoadingChildren(true);
        try {
            const kids = await listTasks(task.task_id);
            setSubtasks(kids);
        } catch { /* ignore */ }
        setLoadingChildren(false);
    }, [task.task_id]);

    const handleToggle = async () => {
        if (!expanded) { await loadSubtasks(); }
        setExpanded((v) => !v);
    };

    const handleAddSubtask = async () => {
        if (!newSubName.trim()) return;
        try {
            await createTask({ task_name: newSubName.trim(), parent_task_id: task.task_id });
            setNewSubName("");
            setShowAddSub(false);
            await loadSubtasks();
            if (!expanded) setExpanded(true);
        } catch { /* ignore */ }
    };

    const handleProgressSave = async () => {
        setSavingProgress(true);
        try {
            await updateTask(task.task_id, { progress });
            setEditingProgress(false);
            onRefresh();
        } catch { /* ignore */ }
        setSavingProgress(false);
    };

    const handleNameSave = async () => {
        if (!editName.trim()) { setEditingName(false); return; }
        try {
            await updateTask(task.task_id, { task_name: editName.trim() });
            setEditingName(false);
            onRefresh();
        } catch { /* ignore */ }
    };

    const handleDelete = async () => {
        try {
            await deleteTask(task.task_id);
            onRefresh();
        } catch { /* ignore */ }
    };

    const isDone = progress === 100;

    return (
        <div style={{ paddingLeft: depth === 0 ? 0 : "1.25rem" }}>
            <div
                className="task-row"
                style={{
                    borderLeft: depth > 0 ? "2px solid rgba(255,255,255,0.08)" : "none",
                    paddingLeft: depth > 0 ? "0.75rem" : 0,
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "10px 0",
                    borderBottom: "1px solid rgba(0,0,0,0.04)"
                }}
            >
                {/* Expand / collapse trigger */}
                <button onClick={handleToggle} style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(0,0,0,0.2)", fontSize: "0.7rem", padding: "0 4px", flexShrink: 0 }}>
                    {expanded ? "▼" : "▶"}
                </button>

                {/* Done Checkbox */}
                <button 
                    onClick={handleMarkDone}
                    style={{
                        width: 20, height: 20, borderRadius: 4, border: `2px solid ${isDone ? "var(--teal)" : "#ddd"}`,
                        background: isDone ? "var(--teal)" : "none", cursor: "pointer", flexShrink: 0,
                        display: "flex", alignItems: "center", justifyContent: "center", padding: 0
                    }}
                >
                    {isDone && <span style={{ color: "#fff", fontSize: "0.8rem", fontWeight: "bold" }}>✓</span>}
                </button>

                {/* Task Info & Progress Bar */}
                {editingName ? (
                    <input
                        value={editName} autoFocus
                        onChange={(e) => setEditName(e.target.value)}
                        onBlur={handleNameSave}
                        onKeyDown={(e) => { if (e.key === "Enter") handleNameSave(); if (e.key === "Escape") setEditingName(false); }}
                        style={{ flex: 1, background: "rgba(0,0,0,0.03)", border: "1px solid var(--teal)", borderRadius: 6, fontSize: "0.88rem", padding: "3px 8px" }}
                    />
                ) : (
                    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px", minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", minWidth: 0 }}>
                            <span
                                className={`task-label${isDone ? " done" : ""}`}
                                onDoubleClick={() => { setEditName(task.task_name); setEditingName(true); }}
                                style={{ cursor: "text", minWidth: 0, fontSize: "0.95rem", fontWeight: 500, color: isDone ? "#999" : "#333" }}
                            >
                                {task.task_name}
                            </span>
                            {task.expected_time && (
                                <span style={{ fontSize: "0.7rem", color: "#888", background: "#f0f0f0", padding: "1px 6px", borderRadius: 4 }}>
                                    {formatSeconds(sessionSeconds)} / {formatSeconds(task.expected_time)}
                                </span>
                            )}
                        </div>
                        
                        {/* Bordered Progress Bar with Overtime Overflow */}
                        {task.expected_time && task.expected_time > 0 && (
                            <div style={{ position: "relative", width: "100%", height: 8, marginTop: "0.2rem" }}>
                                <div style={{ 
                                    width: "100%", height: "100%", background: "#f0f0f0", 
                                    border: "1px solid #e0e0e0", borderRadius: 4, overflow: "visible",
                                    display: "flex" 
                                }}>
                                    {/* Teal: Time within budget */}
                                    <div style={{ 
                                        width: `${Math.min((sessionSeconds / task.expected_time) * 100, 100)}%`, 
                                        height: "100%", 
                                        background: isRunning ? "var(--teal)" : "#bcc6cc",
                                        borderRadius: sessionSeconds >= task.expected_time ? "4px 0 0 4px" : 4,
                                        transition: "width 0.5s ease"
                                    }} />
                                    
                                    {/* Red: Overtime part (overflows visible container) */}
                                    {sessionSeconds > task.expected_time && (
                                        <div style={{ 
                                            position: "absolute",
                                            left: "calc(100% - 1px)",
                                            top: -1, // Match border offset
                                            width: `${((sessionSeconds - task.expected_time) / task.expected_time) * 100}%`,
                                            maxWidth: "50%",
                                            height: "calc(100% + 2px)", // Match full border height
                                            background: "#ef4444",
                                            border: "1px solid #ef4444",
                                            borderLeft: "none",
                                            borderRadius: "0 4px 4px 0",
                                            transition: "width 0.5s ease"
                                        }} />
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Session Actions */}
                <div style={{ display: "flex", gap: "2px" }}>
                    {isRunning ? (
                        <button onClick={handlePause} title="Pause Session" style={{ background: "#f59e0b", border: "none", borderRadius: 4, color: "#fff", padding: "4px 8px", cursor: "pointer", fontSize: "0.7rem" }}>
                            ⏸
                        </button>
                    ) : (
                        !isDone && (
                            <button onClick={handleStart} title="Start Session" style={{ background: "#10b981", border: "none", borderRadius: 4, color: "#fff", padding: "4px 8px", cursor: "pointer", fontSize: "0.7rem" }}>
                                ▶
                            </button>
                        )
                    )}
                    <button onClick={() => setConfirmDelete(true)} title="Delete Task" style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", fontSize: "0.8rem", padding: "4px", opacity: 0.6 }}>
                        ✕
                    </button>
                </div>

                {confirmDelete && (
                    <div style={{ position: "absolute", right: 0, background: "#fff", padding: "4px", border: "1px solid #ddd", borderRadius: 6, zIndex: 10, display: "flex", gap: "4px" }}>
                        <button onClick={handleDelete} style={{ background: "#ef4444", color: "#fff", border: "none", borderRadius: 4, padding: "2px 8px" }}>Delete</button>
                        <button onClick={() => setConfirmDelete(false)}>Cancel</button>
                    </div>
                )}
            </div>

            {/* Inline progress editor (manual fallback) */}
            {editingProgress && (
                <div style={{ paddingLeft: depth > 0 ? "2rem" : "2.5rem", marginTop: "0.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <input
                        type="range" min={0} max={100} value={progress}
                        onChange={(e) => setProgress(Number(e.target.value))}
                        style={{ flex: 1, accentColor: "var(--teal)" }}
                    />
                    <span style={{ color: "var(--teal)", fontSize: "0.8rem", minWidth: 32 }}>{progress}%</span>
                    <button onClick={handleProgressSave} disabled={savingProgress}
                        style={{ background: "var(--teal)", border: "none", borderRadius: 6, color: "#fff", fontSize: "0.75rem", padding: "3px 10px", cursor: "pointer" }}>
                        {savingProgress ? "…" : "Save"}
                    </button>
                    <button onClick={() => { setProgress(task.progress); setEditingProgress(false); }}
                        style={{ background: "rgba(255,255,255,0.08)", border: "none", borderRadius: 6, color: "#fff", fontSize: "0.75rem", padding: "3px 10px", cursor: "pointer" }}>
                        Cancel
                    </button>
                </div>
            )}

            {/* Add subtask mini-form */}
            {showAddSub && (
                <div style={{ paddingLeft: depth > 0 ? "2rem" : "2.5rem", marginTop: "0.25rem", display: "flex", gap: "0.5rem" }}>
                    <input
                        placeholder="Subtask name..."
                        value={newSubName}
                        onChange={(e) => setNewSubName(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") handleAddSubtask(); if (e.key === "Escape") setShowAddSub(false); }}
                        autoFocus
                        style={{
                            flex: 1, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.15)",
                            borderRadius: 6, color: "#fff", fontSize: "0.82rem", padding: "4px 10px",
                        }}
                    />
                    <button onClick={handleAddSubtask}
                        style={{ background: "var(--teal)", border: "none", borderRadius: 6, color: "#fff", fontSize: "0.75rem", padding: "4px 12px", cursor: "pointer" }}>
                        Add
                    </button>
                    <button onClick={() => setShowAddSub(false)}
                        style={{ background: "rgba(255,255,255,0.08)", border: "none", borderRadius: 6, color: "#fff", fontSize: "0.75rem", padding: "4px 10px", cursor: "pointer" }}>
                        ✕
                    </button>
                </div>
            )}

            {/* Subtasks */}
            {expanded && (
                <div style={{ marginTop: "0.25rem" }}>
                    {loadingChildren && <p className="loading" style={{ paddingLeft: "2.5rem", fontSize: "0.8rem" }}>Loading…</p>}
                    {subtasks.map((sub) => (
                        <TaskRow key={sub.task_id} task={sub} depth={depth + 1} onRefresh={async () => { await loadSubtasks(); onRefresh(); }} />
                    ))}
                    {!loadingChildren && subtasks.length === 0 && (
                        <p style={{ paddingLeft: "2.5rem", fontSize: "0.78rem", color: "rgba(255,255,255,0.3)", margin: "0.25rem 0" }}>No subtasks yet</p>
                    )}
                </div>
            )}
        </div>
    );
}

export default function InternalTasksView({ compact = false }: Props) {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [newTaskName, setNewTaskName] = useState("");
    const [newTaskDesc, setNewTaskDesc] = useState("");
    const [newTaskExpectedTime, setNewTaskExpectedTime] = useState("");
    const [creating, setCreating] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const all = await listTasks("root");  // top-level tasks only
            setTasks(all);
        } catch (err) {
            console.error("InternalTasksView: failed to load tasks", err);
        }
        setLoading(false);
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleCreate = async () => {
        if (!newTaskName.trim()) return;
        setCreating(true);
        try {
            await createTask({ 
                task_name: newTaskName.trim(), 
                description: newTaskDesc.trim() || undefined,
                expected_time: parseTimeToSeconds(newTaskExpectedTime) || undefined
            });
            setNewTaskName("");
            setNewTaskDesc("");
            setNewTaskExpectedTime("");
            setShowAddForm(false);
            await load();
        } catch { /* ignore */ }
        setCreating(false);
    };

    const today = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD

    const pending = tasks.filter((t) => {
        const isDone = t.progress === 100;
        const isPast = t.task_date && t.task_date < today;
        return !isDone && !isPast;
    });

    const completed = tasks.filter((t) => {
        return t.progress === 100;
    });


    return (
        <>
            {/* Header row */}
            {!compact && (
                <div className="tasks-section-header">
                    <div className="tasks-date-label">📋 My Tasks</div>
                    <div className="tasks-controls">
                        <button className="btn-action" onClick={() => setShowAddForm(!showAddForm)}>
                            {showAddForm ? "Cancel" : "+ Add Task"}
                        </button>
                        <button className="btn-action" onClick={load}>🔄 Refresh</button>
                    </div>
                </div>
            )}

            {/* Add task form */}
            {showAddForm && (
                <div style={{
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 12, padding: "1rem", marginBottom: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem",
                }}>
                    <input
                        placeholder="Task name *"
                        value={newTaskName}
                        onChange={(e) => setNewTaskName(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") handleCreate(); }}
                        autoFocus
                        style={{
                            background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.15)",
                            borderRadius: 8, color: "#fff", fontSize: "0.9rem", padding: "8px 12px",
                        }}
                    />
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                        <input
                            placeholder="Description (optional)"
                            value={newTaskDesc}
                            onChange={(e) => setNewTaskDesc(e.target.value)}
                            style={{
                                flex: 2, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.15)",
                                borderRadius: 8, color: "#fff", fontSize: "0.85rem", padding: "6px 12px",
                            }}
                        />
                        <input
                            placeholder="Allotted time (e.g. 2h)"
                            value={newTaskExpectedTime}
                            onChange={(e) => setNewTaskExpectedTime(e.target.value)}
                            style={{
                                flex: 1, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.15)",
                                borderRadius: 8, color: "#fff", fontSize: "0.85rem", padding: "6px 12px",
                            }}
                        />
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                        <button onClick={() => setShowAddForm(false)}
                            style={{ background: "rgba(255,255,255,0.08)", border: "none", borderRadius: 8, color: "#fff", padding: "8px 16px", cursor: "pointer", fontSize: "0.85rem" }}>
                            Cancel
                        </button>
                        <button onClick={handleCreate} disabled={creating || !newTaskName.trim()}
                            style={{ background: "var(--teal)", border: "none", borderRadius: 8, color: "#fff", padding: "8px 20px", cursor: "pointer", fontSize: "0.85rem", fontWeight: 700 }}>
                            {creating ? "Adding…" : "Add Task"}
                        </button>
                    </div>
                </div>
            )}

            {loading && <p className="loading">Loading tasks…</p>}

            {!loading && !compact && (
                /* Two-column layout for dashboard */
                <div className="tasks-columns">
                    <div>
                        <div className="tasks-col-title">⏳ In Progress ({pending.length})</div>
                        {pending.length === 0
                            ? <p className="no-tasks">No pending tasks — add one above! ✨</p>
                            : <div className="tasks-card">
                                {pending.map((t) => (
                                    <TaskRow key={t.task_id} task={t} depth={0} onRefresh={load} />
                                ))}
                            </div>
                        }

                        {/* Compact add button below pending when no form */}
                        {!showAddForm && (
                            <button
                                onClick={() => setShowAddForm(true)}
                                style={{
                                    marginTop: "0.5rem", background: "transparent", border: "1px dashed rgba(255,255,255,0.2)",
                                    borderRadius: 8, color: "rgba(255,255,255,0.4)", width: "100%", padding: "6px",
                                    cursor: "pointer", fontSize: "0.82rem", transition: "all 0.2s",
                                }}
                                onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--teal)")}
                                onMouseOut={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)")}
                            >
                                + Add Task
                            </button>
                        )}
                    </div>
                    <div>
                        <div className="tasks-col-title">✅ Completed ({completed.length})</div>
                        {completed.length === 0
                            ? <p className="no-tasks">No completed tasks yet.</p>
                            : <div className="tasks-card">
                                {completed.map((t) => (
                                    <TaskRow key={t.task_id} task={t} depth={0} onRefresh={load} />
                                ))}
                            </div>
                        }
                    </div>
                </div>
            )}

            {!loading && compact && (
                /* Compact single-card for home page */
                <div className="tasks-card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                        <div className="tasks-card-title">Tasks</div>
                        <button onClick={() => setShowAddForm(!showAddForm)}
                            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--teal)", fontSize: "1rem", padding: 0 }}
                            title="Add task">＋</button>
                    </div>
                    {pending.length === 0
                        ? <p className="no-tasks">No active tasks. Click ＋ to add one.</p>
                        : pending.map((t) => (
                            <TaskRow key={t.task_id} task={t} depth={0} onRefresh={load} />
                        ))
                    }
                </div>
            )}
        </>
    );
}
