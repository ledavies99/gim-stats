import React, { useEffect, useState } from "react";
import { humanizeNumber } from "../utils";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function PlayerStats() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [historyData, setHistoryData] = useState(null);

  useEffect(() => {
    fetch("/api/player_stats/")
      .then((res) => res.json())
      .then((data) => {
        setPlayers(data.players);
        setLoading(false);
      });
  }, []);

  // Fetch total XP history for all players
  useEffect(() => {
    if (players.length > 0) {
      const playerNames = players.map((p) => p.player_name).join(",");
      fetch(`/api/history_data/overall/?players=${playerNames}`)
        .then((res) => res.json())
        .then((data) => setHistoryData(data));
    }
  }, [players]);

  if (loading) return <div>Loading...</div>;

  if (!players.length) {
    return (
      <p>
        No player data could be retrieved. Please check your internet connection or if players have been added to the database.
      </p>
    );
  }

  const skillIcon = (skill) => `/static/images/${skill.toLowerCase()}.png`;

  // Generate color palette for chart lines
  const chartColors = [
    "#4bc0c0",
    "#36a2eb",
    "#9966ff",
    "#ff6384",
    "#ff9f40",
    "#e7e9ed",
    "#b0a89d"
  ];

  return (
    <>
      <main>
        {players.map((player) => (
          <section
            key={player.player_name}
            className={`player-card ${
              player.rank === 1
                ? "gold-border"
                : player.rank === 2
                ? "silver-border"
                : player.rank === 3
                ? "bronze-border"
                : ""
            }`}
          >
            <h2>{player.player_name}</h2>
            <p>Last updated: {player.timestamp}</p>

            <div className="skill-grid">
              {Object.entries(player.skills).map(([skill_name, skill_data]) =>
                skill_name !== "overall" ? (
                  <a
                    key={skill_name}
                    href={`/history/${skill_name}/?player=${player.player_name}`}
                  >
                    <div className="skill-item" data-xp={humanizeNumber(skill_data.xp)}>
                      <img
                        className="skill-icon"
                        src={skillIcon(skill_name)}
                        alt={skill_name}
                      />
                      <span className="skill-level">{skill_data.level}</span>
                    </div>
                  </a>
                ) : null
              )}

              <a href={`/history/overall/?player=${player.player_name}`}>
                <div className="overall-stats">
                  <div className="overall-stats-text" data-xp={humanizeNumber(player.skills.overall.xp)}>
                    <span className="overall-label">Total level:</span>
                    <span className="overall-value">{player.skills.overall.level}</span>
                  </div>
                </div>
              </a>
            </div>

            {/* Bosses Collapsible */}
            <details className="collapsible-section collapsible-boss-stats">
              <summary className="boss-grid-header">Bosses</summary>
              <div className="boss-grid">
                {Object.entries(player.bosses).map(
                  ([boss_name, boss_data]) =>
                    boss_data.killcount > 0 && (
                      <div className="boss-item" key={boss_name}>
                        <span className="boss-name">{boss_name}</span>
                        <span className="boss-killcount">{boss_data.killcount}</span>
                      </div>
                    )
                )}
              </div>
            </details>

            {/* XP Today Collapsible */}
            <details className="collapsible-section collapsible-xp-gained-today">
              <summary className="xp-grid-header">
                <span>XP Today</span>
                <span className="xp-amount" style={{ marginLeft: "auto" }}>
                  {humanizeNumber(player.xp_gained_today || 0)}
                </span>
                {player.top_skill_today && (
                  <img
                    className="skill-icon right-icon"
                    src={skillIcon(player.top_skill_today)}
                    alt={player.top_skill_today}
                  />
                )}
              </summary>
              <div className="xp-grid">
                {player.skill_xp_gained_today.map(([skill, xp]) => (
                  <div className="xp-item" key={skill}>
                    <span className="xp-skill">{skill}</span>
                    <span className="xp-amount">{humanizeNumber(xp)}</span>
                  </div>
                ))}
              </div>
            </details>

            {/* XP Week Collapsible */}
            <details className="collapsible-section collapsible-xp-gained-week">
              <summary className="xp-grid-header">
                <span>XP Week</span>
                <span className="xp-amount" style={{ marginLeft: "auto" }}>
                  {humanizeNumber(player.xp_gained_week || 0)}
                </span>
                {player.top_skill_week && (
                  <img
                    className="skill-icon right-icon"
                    src={skillIcon(player.top_skill_week)}
                    alt={player.top_skill_week}
                  />
                )}
              </summary>
              <div className="xp-grid">
                {player.skill_xp_gained_week.map(([skill, xp]) => (
                  <div className="xp-item" key={skill}>
                    <span className="xp-skill">{skill}</span>
                    <span className="xp-amount">{humanizeNumber(xp)}</span>
                  </div>
                ))}
              </div>
            </details>
          </section>
        ))}
      </main>
      {/* Centered graph for all players' total XP */}
      {historyData && historyData.datasets && historyData.datasets.length > 0 && (
        <div className="history-container">
          <div className="chart-card" style={{ background: '#3f3e3a', border: '1px solid #7c7365', borderRadius: '8px', padding: '20px', boxSizing: 'border-box', width: '100%', maxWidth: '1000px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)' }}>
            <h1 style={{ color: '#ffd700', fontSize: '2.8rem', margin: '0 0 10px 0', fontWeight: 'bold' }}>Total XP Over Time</h1>
            <div className="chart-container">
              {(() => {
                // Build a sorted union of all x-values (dates)
                const allDatesSet = new Set();
                historyData.datasets.forEach(ds => ds.data.forEach(point => allDatesSet.add(point.x)));
                const allDates = Array.from(allDatesSet).sort();

                // For each dataset, map y-values to the global x-values
                const alignedDatasets = historyData.datasets.map((ds, i) => {
                  // Build a map of x to y for this dataset
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
                  <Line
                    data={{
                      labels: allDates.map(date => {
                        // Format date as 'Aug 7', 'Sep 1', etc.
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
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default PlayerStats;