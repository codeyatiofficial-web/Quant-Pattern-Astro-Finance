'use client';
import React, { useState, useEffect, useRef } from "react";

const API = '';

// ── Sectors ──────────────────────────────────────────────────────────────────
const SECTORS = ["Banking", "IT", "Energy", "FMCG", "Auto", "Finance", "Pharma", "Metals", "Infra", "Cement", "Consumer", "Telecom", "Insurance", "Healthcare"];

const SECTOR_COLORS: Record<string, string> = {
  Banking: "#3b82f6", IT: "#8b5cf6", Energy: "#f59e0b",
  FMCG: "#10b981", Auto: "#f97316", Finance: "#06b6d4",
  Pharma: "#ec4899", Metals: "#6b7280", Infra: "#84cc16",
  Cement: "#a78bfa", Consumer: "#fb7185", Telecom: "#34d399",
  Insurance: "#60a5fa", Healthcare: "#f472b6"
};

// ── Color scale ──────────────────────────────────────────────────────────────
function getColor(value: number, mode = "dma") {
  if (mode === "dma") {
    if (value <= -20) return { bg: "#064e3b", text: "#4ade80", border: "#059669" };
    if (value < -5) return { bg: "#166534", text: "#86efac", border: "#22c55e" };
    if (value <= 10) return { bg: "#334155", text: "#94a3b8", border: "#475569" };
    if (value <= 20) return { bg: "#991b1b", text: "#fca5a5", border: "#ef4444" };
    return { bg: "#450a0a", text: "#fecdd3", border: "#b91c1c" };
  }
  if (mode === "change") {
    if (value > 3) return { bg: "#14532d", text: "#4ade80", border: "#16a34a" };
    if (value > 1.5) return { bg: "#166534", text: "#86efac", border: "#22c55e" };
    if (value > 0.5) return { bg: "#15803d", text: "#bbf7d0", border: "#4ade80" };
    if (value > 0) return { bg: "#1a3a2a", text: "#6ee7b7", border: "#34d399" };
    if (value > -0.5) return { bg: "#3b1a1a", text: "#fca5a5", border: "#f87171" };
    if (value > -1.5) return { bg: "#7f1d1d", text: "#fecaca", border: "#ef4444" };
    if (value > -3) return { bg: "#991b1b", text: "#fee2e2", border: "#dc2626" };
    return { bg: "#450a0a", text: "#fecdd3", border: "#b91c1c" };
  }
  if (mode === "volume") {
    const intensity = Math.min(value / 5000000, 1);
    const b = Math.floor(50 + intensity * 150);
    return { bg: `rgb(20, 30, ${b})`, text: "#e2e8f0", border: `rgb(30, 40, ${Math.min(b + 30, 255)})` };
  }
  if (mode === "iv") {
    if (value > 40) return { bg: "#450a0a", text: "#fecdd3", border: "#b91c1c" };
    if (value > 30) return { bg: "#7c2d12", text: "#fed7aa", border: "#ea580c" };
    if (value > 20) return { bg: "#713f12", text: "#fef3c7", border: "#d97706" };
    return { bg: "#1a3a2a", text: "#6ee7b7", border: "#34d399" };
  }
  return { bg: "#1e293b", text: "#94a3b8", border: "#334155" };
}

function formatDisplayValue(stock: any, mode: string) {
  if (mode === "dma") return `${stock.dma >= 0 ? "+" : ""}${stock.dma}%`;
  if (mode === "volume") return `${(stock.volume / 100000).toFixed(1)}L`;
  if (mode === "iv") return `${stock.iv}%`;
  return `${stock.change >= 0 ? "+" : ""}${stock.change}%`;
}

// ── Main Component ───────────────────────────────────────────────────────────
export default function NiftyHeatmap() {
  const [data, setData] = useState<any[]>([]);
  const [heatmapMode, setHeatmapMode] = useState("dma");
  const [viewMode, setViewMode] = useState("treemap"); // treemap | grid | sector
  const [sortBy, setSortBy] = useState("dma");
  const [selectedStock, setSelectedStock] = useState<any>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [animating, setAnimating] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<any>(null);

  const fetchHeatmapData = async () => {
    try {
      const res = await fetch(`${API}/api/nifty50/heatmap`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to fetch' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const json = await res.json();
      if (json.success && json.stocks) {
        setData(json.stocks);
        setLastUpdate(new Date());
        setError(null);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to load heatmap data');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch + auto-refresh every 60s
  useEffect(() => {
    setIsMounted(true);
    fetchHeatmapData();

    intervalRef.current = setInterval(() => {
      setAnimating(true);
      setTimeout(() => {
        fetchHeatmapData();
        setAnimating(false);
      }, 300);
    }, 60000);
    return () => clearInterval(intervalRef.current);
  }, []);

  const refreshData = () => {
    setAnimating(true);
    setTimeout(() => {
      fetchHeatmapData();
      setAnimating(false);
    }, 300);
  };

  if (!isMounted) return null;

  if (loading && data.length === 0) {
    return (
      <div style={{
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        background: "#060b14", color: "#e2e8f0", padding: "40px",
        borderRadius: "16px", border: "1px solid #1e3a5f", marginBottom: "24px",
        textAlign: "center"
      }}>
        <div style={{ fontSize: "14px", color: "#64748b", marginBottom: "8px" }}>Loading Nifty 50 Heatmap...</div>
        <div style={{ fontSize: "11px", color: "#475569" }}>Fetching real market data for 50 stocks (may take 15-30s on first load)</div>
      </div>
    );
  }

  if (error && data.length === 0) {
    return (
      <div style={{
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        background: "#060b14", color: "#f87171", padding: "40px",
        borderRadius: "16px", border: "1px solid #7f1d1d", marginBottom: "24px",
        textAlign: "center"
      }}>
        <div style={{ fontSize: "14px", marginBottom: "8px" }}>Heatmap Error</div>
        <div style={{ fontSize: "11px", color: "#94a3b8" }}>{error}</div>
        <button onClick={refreshData} style={{
          marginTop: 12, padding: '6px 16px', fontSize: 11, fontWeight: 700,
          background: '#1e293b', border: '1px solid #334155', borderRadius: 6,
          color: '#f8fafc', cursor: 'pointer'
        }}>Retry</button>
      </div>
    );
  }

  const sortedData = [...data].sort((a, b) => {
    if (sortBy === "weight") return b.weight - a.weight;
    if (sortBy === "dma") return a.dma - b.dma; // Deep value first
    if (sortBy === "change") return b.change - a.change;
    if (sortBy === "volume") return b.volume - a.volume;
    if (sortBy === "iv") return b.iv - a.iv;
    return 0;
  });

  const advancers = data.filter(d => d.change > 0).length;
  const decliners = data.filter(d => d.change < 0).length;
  const niftyChange = data.reduce((sum, d) => sum + (d.change * d.weight / 100), 0);

  // Sector aggregation
  const sectorData = SECTORS.map(sector => {
    const stocks = data.filter(s => s.sector === sector);
    if (!stocks.length) return null;
    const avgChange = stocks.reduce((s, d) => s + d.change, 0) / stocks.length;
    const avgDma = stocks.reduce((s, d) => s + d.dma, 0) / stocks.length;
    const avgVolume = stocks.reduce((s, d) => s + d.volume, 0) / stocks.length;
    const avgIv = stocks.reduce((s, d) => s + d.iv, 0) / stocks.length;
    const totalWeight = stocks.reduce((s, d) => s + d.weight, 0);
    return { 
      sector, 
      avgChange: parseFloat(avgChange.toFixed(2)), 
      avgDma: parseFloat(avgDma.toFixed(1)), 
      avgVolume,
      avgIv: parseFloat(avgIv.toFixed(1)),
      stocks, 
      totalWeight, 
      count: stocks.length 
    };
  }).filter(Boolean);

  const bestBuyToday = [...data].sort((a, b) => b.score - a.score)[0];
  const bestSellToday = [...data].sort((a, b) => a.score - b.score)[0];
  const bestBuyLongTerm = [...data].sort((a, b) => a.dma - b.dma)[0];
  const bestSellLongTerm = [...data].sort((a, b) => b.dma - a.dma)[0];

  return (
    <div style={{
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      background: "#060b14",
      color: "#e2e8f0",
      padding: "0",
      borderRadius: "16px",
      overflow: "hidden",
      border: "1px solid #1e3a5f",
      marginBottom: "24px"
    }}>
      {/* Header */}
      <div style={{
        background: "#0d1b2e",
        borderBottom: "1px solid #1e3a5f",
        padding: "16px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div>
            <div style={{ fontSize: "10px", color: "#64748b", letterSpacing: "3px", textTransform: "uppercase" }}>NSE INDEX</div>
            <div style={{ fontSize: "22px", fontWeight: "700", letterSpacing: "-0.5px", color: "#f1f5f9" }}>
              NIFTY 50 <span style={{ fontSize: "11px", color: "#64748b", fontWeight: "400" }}>HEATMAP</span>
            </div>
          </div>
          <div style={{
            background: niftyChange >= 0 ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)",
            border: `1px solid ${niftyChange >= 0 ? "#22c55e" : "#ef4444"}`,
            borderRadius: "8px",
            padding: "8px 16px",
            textAlign: "center"
          }}>
            <div style={{ fontSize: "9px", color: "#64748b", letterSpacing: "2px" }}>INDEX CHANGE</div>
            <div style={{ fontSize: "20px", fontWeight: "700", color: niftyChange >= 0 ? "#4ade80" : "#f87171" }}>
              {niftyChange >= 0 ? "+" : ""}{niftyChange.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
          {[
            { label: "ADVANCES", value: advancers, color: "#4ade80" },
            { label: "DECLINES", value: decliners, color: "#f87171" },
            { label: "UNCHANGED", value: 50 - advancers - decliners, color: "#64748b" },
          ].map(stat => (
            <div key={stat.label} style={{ textAlign: "center" }}>
              <div style={{ fontSize: "9px", color: "#64748b", letterSpacing: "2px" }}>{stat.label}</div>
              <div style={{ fontSize: "20px", fontWeight: "700", color: stat.color }}>{stat.value}</div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ fontSize: "9px", color: "#475569" }}>
            UPDATED {lastUpdate ? lastUpdate.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "..."}
          </div>
          <button onClick={refreshData} style={{
            background: "rgba(59,130,246,0.2)", border: "1px solid #3b82f6",
            borderRadius: "6px", padding: "6px 12px", color: "#60a5fa",
            cursor: "pointer", fontSize: "10px", letterSpacing: "1px",
            transition: "all 0.2s"
          }}>
            ⟳ REFRESH
          </button>
        </div>
      </div>

      {/* Top Picks Insights */}
      {data.length > 0 && (
        <div style={{
          display: "flex", gap: "24px", padding: "12px 24px",
          background: "rgba(15,23,42,0.8)", borderBottom: "1px solid #1e2d40",
          flexWrap: "wrap", alignItems: "center", justifyContent: "space-between"
        }}>
          <div style={{ display: "flex", gap: "32px", flexWrap: "wrap", width: "100%" }}>
            {/* Short Term */}
            <div style={{ display: "flex", gap: "16px", flex: 1, minWidth: "250px", borderRight: "1px solid #1e3a5f", paddingRight: "16px" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "9px", color: "#64748b", letterSpacing: "1px", marginBottom: "4px" }}>TODAY'S BEST BUY (SCORE)</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                  <span style={{ fontSize: "15px", fontWeight: "700", color: "#4ade80" }}>{bestBuyToday?.symbol}</span>
                  <span style={{ fontSize: "11px", color: "#94a3b8" }}>{bestBuyToday?.score}</span>
                </div>
              </div>
              <div style={{ width: "1px", height: "30px", background: "#1e3a5f", margin: "auto 0" }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "9px", color: "#64748b", letterSpacing: "1px", marginBottom: "4px" }}>TODAY'S TOP SELL (SCORE)</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                  <span style={{ fontSize: "15px", fontWeight: "700", color: "#f87171" }}>{bestSellToday?.symbol}</span>
                  <span style={{ fontSize: "11px", color: "#94a3b8" }}>{bestSellToday?.score}</span>
                </div>
              </div>
            </div>
            {/* Long Term */}
            <div style={{ display: "flex", gap: "16px", flex: 1, minWidth: "250px" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "9px", color: "#64748b", letterSpacing: "1px", marginBottom: "4px" }}>DEEP VALUE BUY (200 DMA)</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                  <span style={{ fontSize: "15px", fontWeight: "700", color: "#4ade80" }}>{bestBuyLongTerm?.symbol}</span>
                  <span style={{ fontSize: "11px", color: "#94a3b8" }}>{bestBuyLongTerm?.dma > 0 ? "+" : ""}{bestBuyLongTerm?.dma}%</span>
                </div>
              </div>
              <div style={{ width: "1px", height: "30px", background: "#1e3a5f", margin: "auto 0" }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "9px", color: "#64748b", letterSpacing: "1px", marginBottom: "4px" }}>STRETCHED SELL (200 DMA)</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                  <span style={{ fontSize: "15px", fontWeight: "700", color: "#f87171" }}>{bestSellLongTerm?.symbol}</span>
                  <span style={{ fontSize: "11px", color: "#94a3b8" }}>+{bestSellLongTerm?.dma}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div style={{
        display: "flex", gap: "8px", padding: "12px 24px",
        background: "#080f1c", borderBottom: "1px solid #1e2d40",
        flexWrap: "wrap", alignItems: "center"
      }}>
        <span style={{ fontSize: "9px", color: "#475569", letterSpacing: "2px", marginRight: "4px" }}>VIEW:</span>
        {[
          { id: "treemap", label: "▦ TREEMAP" },
          { id: "grid", label: "⊞ GRID" },
          { id: "sector", label: "◉ SECTOR" },
        ].map(v => (
          <button key={v.id} onClick={() => setViewMode(v.id)} style={{
            background: viewMode === v.id ? "rgba(59,130,246,0.3)" : "transparent",
            border: `1px solid ${viewMode === v.id ? "#3b82f6" : "#1e3a5f"}`,
            borderRadius: "5px", padding: "5px 12px",
            color: viewMode === v.id ? "#60a5fa" : "#475569",
            cursor: "pointer", fontSize: "10px", letterSpacing: "1px",
          }}>
            {v.label}
          </button>
        ))}

        <div style={{ width: "1px", height: "20px", background: "#1e3a5f", margin: "0 8px" }} />

        <span style={{ fontSize: "9px", color: "#475569", letterSpacing: "2px", marginRight: "4px" }}>COLOR BY:</span>
        {[
          { id: "dma", label: "200 DMA DIST" },
          { id: "change", label: "% CHANGE" },
          { id: "volume", label: "VOLUME" },
          { id: "iv", label: "IV" },
        ].map(m => (
          <button key={m.id} onClick={() => setHeatmapMode(m.id)} style={{
            background: heatmapMode === m.id ? "rgba(139,92,246,0.3)" : "transparent",
            border: `1px solid ${heatmapMode === m.id ? "#8b5cf6" : "#1e3a5f"}`,
            borderRadius: "5px", padding: "5px 12px",
            color: heatmapMode === m.id ? "#c4b5fd" : "#475569",
            cursor: "pointer", fontSize: "10px", letterSpacing: "1px",
          }}>
            {m.label}
          </button>
        ))}

        <div style={{ width: "1px", height: "20px", background: "#1e3a5f", margin: "0 8px" }} />

        <span style={{ fontSize: "9px", color: "#475569", letterSpacing: "2px", marginRight: "4px" }}>SIZE BY:</span>
        {["dma", "weight", "volume", "iv"].map(s => (
          <button key={s} onClick={() => setSortBy(s)} style={{
            background: sortBy === s ? "rgba(16,185,129,0.2)" : "transparent",
            border: `1px solid ${sortBy === s ? "#10b981" : "#1e3a5f"}`,
            borderRadius: "5px", padding: "5px 12px",
            color: sortBy === s ? "#34d399" : "#475569",
            cursor: "pointer", fontSize: "10px", letterSpacing: "1px", textTransform: "uppercase"
          }}>
            {s}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div style={{ padding: "20px 24px", opacity: animating ? 0.4 : 1, transition: "opacity 0.3s" }}>

        {/* TREEMAP VIEW */}
        {viewMode === "treemap" && (
          <div style={{
            display: "flex", flexWrap: "wrap", gap: "3px",
            background: "#0a1420", borderRadius: "12px",
            padding: "12px", border: "1px solid #1e2d40"
          }}>
            {sortedData.map(stock => {
              const colors = getColor(
                heatmapMode === "dma" ? stock.dma :
                heatmapMode === "change" ? stock.change :
                heatmapMode === "volume" ? stock.volume : stock.iv,
                heatmapMode
              );
              const size = Math.max(stock.weight * 12, 4);
              return (
                <div
                  key={stock.symbol}
                  onClick={() => setSelectedStock(selectedStock?.symbol === stock.symbol ? null : stock)}
                  style={{
                    background: colors.bg,
                    border: `1px solid ${selectedStock?.symbol === stock.symbol ? "#fff" : colors.border}`,
                    borderRadius: "6px",
                    width: `${size}%`,
                    minWidth: "60px",
                    flex: `${size} ${size} auto`,
                    minHeight: size > 8 ? "90px" : size > 5 ? "70px" : "52px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    padding: "6px 4px",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  {/* Sector color bar */}
                  <div style={{
                    position: "absolute", top: 0, left: 0, right: 0,
                    height: "2px", background: SECTOR_COLORS[stock.sector] || "#64748b"
                  }} />
                  <div style={{ fontSize: size > 8 ? "11px" : "9px", fontWeight: "700", color: colors.text, letterSpacing: "0.5px" }}>
                    {stock.symbol.length > 8 ? stock.name : stock.symbol}
                  </div>
                  <div style={{ fontSize: size > 8 ? "13px" : "10px", fontWeight: "700", color: colors.text, marginTop: "2px" }}>
                    {formatDisplayValue(stock, heatmapMode)}
                  </div>
                  {size > 6 && (
                    <div style={{ fontSize: "8px", color: colors.text, opacity: 0.7, marginTop: "2px" }}>
                      {stock.sector}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* GRID VIEW */}
        {viewMode === "grid" && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))",
            gap: "6px",
          }}>
            {sortedData.map(stock => {
              const colors = getColor(
                heatmapMode === "dma" ? stock.dma :
                heatmapMode === "change" ? stock.change :
                heatmapMode === "volume" ? stock.volume : stock.iv,
                heatmapMode
              );
              return (
                <div
                  key={stock.symbol}
                  onClick={() => setSelectedStock(selectedStock?.symbol === stock.symbol ? null : stock)}
                  style={{
                    background: colors.bg,
                    border: `1px solid ${selectedStock?.symbol === stock.symbol ? "#fff" : colors.border}`,
                    borderRadius: "8px",
                    padding: "10px 8px",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    textAlign: "center",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "2px", background: SECTOR_COLORS[stock.sector] }} />
                  <div style={{ fontSize: "10px", fontWeight: "700", color: colors.text }}>{stock.symbol}</div>
                  <div style={{ fontSize: "14px", fontWeight: "700", color: colors.text, margin: "3px 0" }}>
                    {formatDisplayValue(stock, heatmapMode)}
                  </div>
                  <div style={{ fontSize: "8px", color: colors.text, opacity: 0.6 }}>
                    RSI {stock.rsi}
                  </div>
                  <div style={{ fontSize: "8px", color: SECTOR_COLORS[stock.sector], marginTop: "2px" }}>
                    {stock.sector}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* SECTOR VIEW */}
        {viewMode === "sector" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {sectorData.sort((a, b) => {
              if (heatmapMode === "dma") return (a?.avgDma || 0) - (b?.avgDma || 0);
              if (heatmapMode === "volume") return (b?.avgVolume || 0) - (a?.avgVolume || 0);
              if (heatmapMode === "iv") return (b?.avgIv || 0) - (a?.avgIv || 0);
              return (b?.avgChange || 0) - (a?.avgChange || 0);
            }).map(sec => {
              if (!sec) return null;
              const colors = getColor(
                heatmapMode === "dma" ? sec.avgDma : 
                heatmapMode === "volume" ? sec.avgVolume :
                heatmapMode === "iv" ? sec.avgIv : sec.avgChange, 
                heatmapMode
              );
              return (
                <div key={sec.sector} style={{
                  background: "#0a1420", borderRadius: "10px",
                  border: "1px solid #1e2d40", overflow: "hidden"
                }}>
                  {/* Sector Header */}
                  <div style={{
                    display: "flex", alignItems: "center", gap: "12px",
                    padding: "10px 16px",
                    background: "#0d1b2e",
                    borderBottom: "1px solid #1e2d40"
                  }}>
                    <div style={{
                      width: "10px", height: "10px", borderRadius: "50%",
                      background: SECTOR_COLORS[sec.sector]
                    }} />
                    <span style={{ fontWeight: "700", fontSize: "12px", color: "#e2e8f0", flex: 1 }}>
                      {sec.sector.toUpperCase()}
                    </span>
                    <span style={{ fontSize: "9px", color: "#64748b" }}>{sec.count} stocks · {sec.totalWeight.toFixed(1)}% weight</span>
                    <span style={{
                      fontWeight: "700", fontSize: "14px",
                      color: colors.text, minWidth: "60px", textAlign: "right"
                    }}>
                      {heatmapMode === "dma" ? `${sec.avgDma >= 0 ? "+" : ""}${sec.avgDma}%` : 
                       heatmapMode === "volume" ? `${(sec.avgVolume / 100000).toFixed(1)}L` :
                       heatmapMode === "iv" ? `${sec.avgIv}%` :
                       `${sec.avgChange >= 0 ? "+" : ""}${sec.avgChange}%`}
                    </span>
                  </div>
                  {/* Sector Stocks */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", padding: "8px" }}>
                    {sec.stocks.map((stock: any) => {
                      const sc = getColor(
                        heatmapMode === "dma" ? stock.dma :
                        heatmapMode === "change" ? stock.change :
                        heatmapMode === "volume" ? stock.volume : stock.iv,
                        heatmapMode
                      );
                      return (
                        <div key={stock.symbol}
                          onClick={() => setSelectedStock(selectedStock?.symbol === stock.symbol ? null : stock)}
                          style={{
                            background: sc.bg, border: `1px solid ${sc.border}`,
                            borderRadius: "6px", padding: "6px 10px",
                            cursor: "pointer", minWidth: "80px", textAlign: "center"
                          }}>
                          <div style={{ fontSize: "9px", fontWeight: "700", color: sc.text }}>{stock.name}</div>
                          <div style={{ fontSize: "11px", fontWeight: "700", color: sc.text }}>
                            {formatDisplayValue(stock, heatmapMode)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Stock Detail Panel */}
      {selectedStock && (
        <div style={{
          position: "fixed", bottom: "20px", right: "20px",
          background: "#0d1b2e", border: "1px solid #1e3a5f",
          borderRadius: "14px", padding: "20px", width: "280px",
          boxShadow: "0 20px 60px rgba(0,0,0,0.8)",
          zIndex: 100
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <div>
              <div style={{ fontSize: "9px", color: SECTOR_COLORS[selectedStock.sector], letterSpacing: "2px" }}>
                {selectedStock.sector.toUpperCase()}
              </div>
              <div style={{ fontSize: "18px", fontWeight: "700", color: "#f1f5f9" }}>{selectedStock.symbol}</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>{selectedStock.name}</div>
            </div>
            <button onClick={() => setSelectedStock(null)} style={{
              background: "transparent", border: "1px solid #1e3a5f",
              borderRadius: "6px", color: "#64748b", cursor: "pointer",
              padding: "4px 8px", fontSize: "12px"
            }}>✕</button>
          </div>

          {/* Change Badge */}
          <div style={{
            background: heatmapMode === "dma" ? getColor(selectedStock.dma, "dma").bg : selectedStock.change >= 0 ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
            border: `1px solid ${heatmapMode === "dma" ? getColor(selectedStock.dma, "dma").border : selectedStock.change >= 0 ? "#22c55e" : "#ef4444"}`,
            borderRadius: "8px", padding: "10px", marginBottom: "14px", textAlign: "center"
          }}>
            <div style={{ fontSize: "28px", fontWeight: "700", color: heatmapMode === "dma" ? getColor(selectedStock.dma, "dma").text : selectedStock.change >= 0 ? "#4ade80" : "#f87171" }}>
              {heatmapMode === "dma" ? `${selectedStock.dma >= 0 ? "+" : ""}${selectedStock.dma}%` : `${selectedStock.change >= 0 ? "+" : ""}${selectedStock.change}%`}
            </div>
            <div style={{ fontSize: "9px", color: "#64748b", textTransform: "uppercase" }}>{heatmapMode === "dma" ? "200 DMA DIST" : "DAY CHANGE"}</div>
          </div>

          {/* Stats Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            {[
              { label: "LTP", value: `₹${selectedStock.ltp.toFixed(0)}` },
              { label: "WEIGHT", value: `${selectedStock.weight}%` },
              { label: "VOLUME", value: `${(selectedStock.volume / 100000).toFixed(1)}L` },
              { label: "OI", value: `${(selectedStock.oi / 100000).toFixed(1)}L` },
              { label: "IV", value: `${selectedStock.iv}%`, color: selectedStock.iv > 35 ? "#f87171" : selectedStock.iv > 25 ? "#fbbf24" : "#4ade80" },
              { label: "RSI", value: selectedStock.rsi.toFixed(0), color: selectedStock.rsi > 70 ? "#f87171" : selectedStock.rsi < 30 ? "#4ade80" : "#94a3b8" },
            ].map(stat => (
              <div key={stat.label} style={{
                background: "#060b14", borderRadius: "6px", padding: "8px",
                border: "1px solid #1e2d40"
              }}>
                <div style={{ fontSize: "8px", color: "#475569", letterSpacing: "1px" }}>{stat.label}</div>
                <div style={{ fontSize: "13px", fontWeight: "700", color: stat.color || "#e2e8f0", marginTop: "2px" }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* RSI Bar */}
          <div style={{ marginTop: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
              <span style={{ fontSize: "8px", color: "#475569" }}>RSI INDICATOR</span>
              <span style={{ fontSize: "8px", color: selectedStock.rsi > 70 ? "#f87171" : selectedStock.rsi < 30 ? "#4ade80" : "#94a3b8" }}>
                {selectedStock.rsi > 70 ? "OVERBOUGHT" : selectedStock.rsi < 30 ? "OVERSOLD" : "NEUTRAL"}
              </span>
            </div>
            <div style={{ background: "#1e2d40", borderRadius: "4px", height: "6px", position: "relative" }}>
              <div style={{
                position: "absolute", left: "30%", right: "30%", top: 0, bottom: 0,
                background: "rgba(100,116,139,0.3)"
              }} />
              <div style={{
                position: "absolute", left: `${selectedStock.rsi}%`, transform: "translateX(-50%)",
                width: "12px", height: "12px", borderRadius: "50%", top: "-3px",
                background: selectedStock.rsi > 70 ? "#ef4444" : selectedStock.rsi < 30 ? "#22c55e" : "#3b82f6",
                border: "2px solid #0d1b2e"
              }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "3px" }}>
              <span style={{ fontSize: "7px", color: "#475569" }}>0</span>
              <span style={{ fontSize: "7px", color: "#475569" }}>30</span>
              <span style={{ fontSize: "7px", color: "#475569" }}>70</span>
              <span style={{ fontSize: "7px", color: "#475569" }}>100</span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div style={{
        display: "flex", gap: "6px", padding: "12px 24px 80px",
        alignItems: "center", flexWrap: "wrap"
      }}>
        <span style={{ fontSize: "8px", color: "#475569", letterSpacing: "2px", marginRight: "4px" }}>
          {heatmapMode === "dma" ? "200 DMA DISTANCE:" : heatmapMode === "change" ? "CHANGE SCALE:" : heatmapMode === "volume" ? "VOLUME:" : "IV SCALE:"}
        </span>
        {heatmapMode === "dma" && [
          { label: "<-20% DEEP VALUE", bg: "#064e3b", text: "#4ade80" },
          { label: "-5% TO -20%", bg: "#166534", text: "#86efac" },
          { label: "-5% TO +10%", bg: "#334155", text: "#94a3b8" },
          { label: "+10% TO +20%", bg: "#991b1b", text: "#fca5a5" },
          { label: ">+20% STRETCHED", bg: "#450a0a", text: "#fecdd3" },
        ].map((l, i) => (
          <div key={i} style={{
            background: l.bg, borderRadius: "4px", padding: "3px 8px",
            fontSize: "8px", color: l.text, fontWeight: "700"
          }}>{l.label}</div>
        ))}
        {heatmapMode === "change" && [
          { label: ">3%", bg: "#14532d", text: "#4ade80" },
          { label: "1-3%", bg: "#166534", text: "#86efac" },
          { label: "0-1%", bg: "#15803d", text: "#bbf7d0" },
          { label: "0%", bg: "#1e293b", text: "#64748b" },
          { label: "0-1%", bg: "#3b1a1a", text: "#fca5a5" },
          { label: "1-3%", bg: "#7f1d1d", text: "#fecaca" },
          { label: ">3%", bg: "#450a0a", text: "#fecdd3" },
        ].map((l, i) => (
          <div key={i} style={{
            background: l.bg, borderRadius: "4px", padding: "3px 8px",
            fontSize: "8px", color: l.text, fontWeight: "700"
          }}>{l.label}</div>
        ))}
        {heatmapMode === "iv" && [
          { label: "LOW <20", bg: "#1a3a2a", text: "#6ee7b7" },
          { label: "MED 20-30", bg: "#713f12", text: "#fef3c7" },
          { label: "HIGH 30-40", bg: "#7c2d12", text: "#fed7aa" },
          { label: "VERY HIGH >40", bg: "#450a0a", text: "#fecdd3" },
        ].map((l, i) => (
          <div key={i} style={{
            background: l.bg, borderRadius: "4px", padding: "3px 8px",
            fontSize: "8px", color: l.text, fontWeight: "700"
          }}>{l.label}</div>
        ))}
        <div style={{ marginLeft: "auto", fontSize: "8px", color: "#1e3a5f" }}>
          Click any stock for details · Auto-refreshes every 30s
        </div>
      </div>
    </div>
  );
}
