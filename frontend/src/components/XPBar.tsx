"use client";
import { useEffect, useState } from "react";
import { getXPInfo } from "@/lib/api";

export default function XPBar() {
    const [info, setInfo] = useState<{ level: number; total_xp: number; current_level_xp: number; xp_for_next_level: number } | null>(null);

    useEffect(() => {
        getXPInfo()
            .then(setInfo)
            .catch((err) => {
                console.error("XPBar: failed to load XP", err);
            });
    }, []);

    if (!info) return null;

    const pct = Math.max(0, info.xp_for_next_level > 0
        ? Math.min(100, (info.current_level_xp / (info.current_level_xp + info.xp_for_next_level)) * 100)
        : 100);

    return (
        <>
            <div className="level-header">LEVEL {info.level}</div>
            <div className="xp-value">{info.total_xp < 0 ? info.total_xp : `+${info.total_xp}`} XP</div>
            <div className="xp-sub">{info.xp_for_next_level} XP to reach Level {info.level + 1}</div>
            <div className="xp-bar-track">
                <div className="xp-bar-fill" style={{ width: `${pct}%` }} />
            </div>
        </>
    );
}
