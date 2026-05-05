"use client";

import { useState, useMemo, useCallback } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, AreaChart, Area,
} from "recharts";
import type { CellData } from "@/components/SpreadsheetGrid";
import { getCellValue } from "@/components/SpreadsheetGrid";

interface ChartPanelProps {
  data: CellData;
  onClose: () => void;
}

type ChartType = "bar" | "line" | "pie" | "scatter" | "area";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#14b8a6"];

export default function ChartPanel({ data, onClose }: ChartPanelProps) {
  const [chartType, setChartType] = useState<ChartType>("bar");
  const [labelCol, setLabelCol] = useState("A");
  const [valueCol, setValueCol] = useState("B");
  const [startRow, setStartRow] = useState(1);
  const [endRow, setEndRow] = useState(10);

  const availableCols = useMemo(() => {
    const cols = new Set<string>();
    for (const col of Object.keys(data)) cols.add(col);
    return [...cols].sort();
  }, [data]);

  const chartData = useMemo(() => {
    const items: { label: string; value: number }[] = [];
    for (let r = startRow; r <= endRow; r++) {
      const label = getCellValue(data, labelCol, r);
      const raw = getCellValue(data, valueCol, r);
      const value = parseFloat(raw);
      if (label && !isNaN(value)) {
        items.push({ label, value });
      }
    }
    return items;
  }, [data, labelCol, valueCol, startRow, endRow]);

  const renderChart = useCallback(() => {
    if (chartData.length === 0) {
      return <p className="text-gray-400 text-sm text-center mt-8">Aucune donnee a afficher</p>;
    }

    switch (chartType) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        );
      case "line":
        return (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        );
      case "area":
        return (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
            </AreaChart>
          </ResponsiveContainer>
        );
      case "pie":
        return (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={chartData} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={90} label>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      case "scatter":
        return (
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} name="Label" />
              <YAxis dataKey="value" tick={{ fontSize: 11 }} name="Valeur" />
              <Tooltip />
              <Scatter data={chartData} fill="#6366f1" />
            </ScatterChart>
          </ResponsiveContainer>
        );
    }
  }, [chartType, chartData]);

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-4 m-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">Graphique</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
      </div>

      {/* Chart type selector */}
      <div className="flex gap-1 mb-3">
        {(["bar", "line", "area", "pie", "scatter"] as ChartType[]).map((t) => (
          <button
            key={t}
            onClick={() => setChartType(t)}
            className={`text-xs px-2.5 py-1.5 rounded-md font-medium transition-colors ${
              chartType === t
                ? "bg-indigo-100 text-indigo-700"
                : "bg-gray-50 text-gray-500 hover:bg-gray-100"
            }`}
          >
            {t === "bar" ? "Barres" : t === "line" ? "Ligne" : t === "area" ? "Aire" : t === "pie" ? "Camembert" : "Nuage"}
          </button>
        ))}
      </div>

      {/* Config */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <div>
          <label className="text-[10px] text-gray-500 block mb-0.5">Labels</label>
          <select value={labelCol} onChange={(e) => setLabelCol(e.target.value)} className="w-full text-xs border rounded px-1.5 py-1">
            {availableCols.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-[10px] text-gray-500 block mb-0.5">Valeurs</label>
          <select value={valueCol} onChange={(e) => setValueCol(e.target.value)} className="w-full text-xs border rounded px-1.5 py-1">
            {availableCols.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-[10px] text-gray-500 block mb-0.5">Debut</label>
          <input type="number" value={startRow} onChange={(e) => setStartRow(parseInt(e.target.value) || 1)} min={1} className="w-full text-xs border rounded px-1.5 py-1" />
        </div>
        <div>
          <label className="text-[10px] text-gray-500 block mb-0.5">Fin</label>
          <input type="number" value={endRow} onChange={(e) => setEndRow(parseInt(e.target.value) || 10)} min={1} className="w-full text-xs border rounded px-1.5 py-1" />
        </div>
      </div>

      {renderChart()}
    </div>
  );
}
