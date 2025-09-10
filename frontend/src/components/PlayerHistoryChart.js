import React from "react";
import { Line } from "react-chartjs-2";
import { humanizeNumber } from "../utils";

const chartColors = [
  "#4bc0c0",
  "#36a2eb",
  "#9966ff",
  "#ff6384",
  "#ff9f40",
  "#e7e9ed",
  "#b0a89d"
];

function PlayerHistoryChart({ historyData, selectedSkill }) {
  if (!historyData || !historyData.datasets || historyData.datasets.length === 0) return null;

  const allDatesSet = new Set();
  historyData.datasets.forEach(ds => ds.data.forEach(point => allDatesSet.add(point.x)));
  const allDates = Array.from(allDatesSet).sort();

  const alignedDatasets = historyData.datasets.map((ds, i) => {
    const xyMap = new Map(ds.data.map(point => [point.x, point.y]));
    let lastY = null;
    const yValues = allDates.map(date => {
      if (xyMap.has(date)) {
        lastY = xyMap.get(date);
        return lastY;
      } else {
        return null;
      }
    });
    return {
      ...ds,
      label: ds.label,
      data: yValues,
      borderColor: chartColors[i % chartColors.length],
      backgroundColor: chartColors[i % chartColors.length] + "33",
      tension: 0.2,
      borderWidth: 3,
    };
  });

  return (
    <div className="history-container">
      <div className="chart-card" style={{ background: '#3f3e3a', border: '1px solid #7c7365', borderRadius: '8px', padding: '20px', boxSizing: 'border-box', width: '100%', maxWidth: '1000px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)' }}>
        <h1 style={{ color: '#ffd700', fontSize: '2.8rem', margin: '0 0 10px 0', fontWeight: 'bold' }}>{selectedSkill.charAt(0).toUpperCase() + selectedSkill.slice(1)} XP Over Time</h1>
        <div className="chart-container">
          <Line
            data={{
              labels: allDates.map(date => {
                const d = new Date(date);
                return d.toLocaleString('en-US', { month: 'short', day: 'numeric' });
              }),
              datasets: alignedDatasets,
            }}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  display: true,
                  labels: {
                    color: '#fff',
                    font: { size: 18, weight: 'bold' },
                    boxWidth: 30,
                    padding: 20,
                  },
                },
                title: {
                  display: false,
                },
              },
              scales: {
                x: {
                  title: {
                    display: true,
                    text: 'Date',
                    color: '#fff',
                    font: { size: 18, weight: 'bold' },
                  },
                  ticks: {
                    color: '#fff',
                    font: { size: 14 },
                  },
                  grid: {
                    color: '#444',
                  },
                },
                y: {
                  title: {
                    display: true,
                    text: 'XP',
                    color: '#fff',
                    font: { size: 18, weight: 'bold' },
                  },
                  ticks: {
                    color: '#fff',
                    font: { size: 14 },
                    callback: function(value) {
                      return humanizeNumber(value);
                    }
                  },
                  grid: {
                    color: '#444',
                  },
                },
              },
              interaction: { mode: 'nearest', intersect: false },
              elements: { point: { radius: 0, hoverRadius: 0 } },
              spanGaps: true,
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default PlayerHistoryChart;
