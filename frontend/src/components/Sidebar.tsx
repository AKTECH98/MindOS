"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const GOAL_START = new Date("2026-02-14T00:00:00");
const GOAL_END = new Date(GOAL_START.getTime() + 90 * 24 * 3600 * 1000);

function useCountdown() {
    const [now, setNow] = useState(Date.now());
    useEffect(() => {
        const id = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(id);
    }, []);

    const remaining = Math.max(0, GOAL_END.getTime() - now);
    const total = GOAL_END.getTime() - GOAL_START.getTime();
    const progress = Math.min(100, Math.round((remaining / total) * 10000) / 100);

    const dd = Math.floor(remaining / 86400000);
    const hh = Math.floor((remaining % 86400000) / 3600000);
    const mm = Math.floor((remaining % 3600000) / 60000);
    const ss = Math.floor((remaining % 60000) / 1000);
    return { dd, hh, mm, ss, progress };
}

function Dial({ label, value }: { label: string; value: number }) {
    return (
        <div className="countdown-dial">
            <span className="countdown-dial-label">{label}</span>
            <div className="countdown-dial-circle">{String(value).padStart(2, "0")}</div>
        </div>
    );
}

export default function Sidebar() {
    const pathname = usePathname();
    const { dd, hh, mm, ss, progress } = useCountdown();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <span>⊙</span>
                <span>MindOS</span>
            </div>

            {/* Nav */}
            <Link href="/" className={`nav-link${pathname === "/" ? " active" : ""}`}>🏠 Home</Link>
            <Link href="/dashboard" className={`nav-link${pathname === "/dashboard" ? " active" : ""}`}>📊 Dashboard</Link>

            <hr className="nav-divider" />

            {/* 90-day countdown */}
            <div className="countdown-card">
                <div className="countdown-title">90-Day Countdown</div>
                {mounted ? (
                    <>
                        <div className="countdown-bar">
                            <div className="countdown-bar-fill" style={{ width: `${progress}%` }} />
                        </div>
                        <div className="countdown-dials">
                            <Dial label="DD" value={dd} />
                            <Dial label="HH" value={hh} />
                            <Dial label="MM" value={mm} />
                            <Dial label="SS" value={ss} />
                        </div>
                    </>
                ) : (
                    <>
                        <div className="countdown-bar">
                            <div className="countdown-bar-fill" style={{ width: "0%" }} />
                        </div>
                        <div className="countdown-dials">
                            <Dial label="DD" value={0} />
                            <Dial label="HH" value={0} />
                            <Dial label="MM" value={0} />
                            <Dial label="SS" value={0} />
                        </div>
                    </>
                )}
            </div>
        </aside>
    );
}
