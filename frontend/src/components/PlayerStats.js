import React, { useEffect, useState } from "react";
import { humanizeNumber } from "../utils";
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
import { getData, getHistoryData } from '../api';
import axios from 'axios';
import PlayerHistoryChart from "./PlayerHistoryChart";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);


const BACKEND_URL = process.env.REACT_APP_API_BASE_URL
  ? process.env.REACT_APP_API_BASE_URL.replace(/\/api\/?$/, "")
  : "";

function PlayerStats() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [historyData, setHistoryData] = useState(null);
  const [selectedSkill, setSelectedSkill] = useState("overall");

  useEffect(() => {
    getData()
      .then((data) => {
        setPlayers(Array.isArray(data.players) ? data.players : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);
  
  useEffect(() => {
    if (players.length > 0 && selectedSkill) {
      const playerNames = players.map((p) => p.player_name).join(",");
      getHistoryData(selectedSkill, playerNames)
        .then((data) => setHistoryData(data));
    }
  }, [players, selectedSkill]);

  if (loading) return <div>Loading...</div>;
  if (!Array.isArray(players) || players.length === 0) {
    return (
      <p>
        No player data could be retrieved. Please check your internet connection or if players have been added to the database.
      </p>
    );
  }

  const skillIcon = (skill) =>
    BACKEND_URL
      ? `${BACKEND_URL}/static/images/${skill.toLowerCase()}.png`
      : `/static/images/${skill.toLowerCase()}.png`;

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
                  <div
                    key={skill_name}
                    className="skill-item"
                    data-xp={humanizeNumber(skill_data.xp)}
                    onClick={() => setSelectedSkill(skill_name)}
                    style={{ cursor: "pointer" }}
                  >
                    <img
                      className="skill-icon"
                      src={skillIcon(skill_name)}
                      alt={skill_name}
                    />
                    <span className="skill-level">{skill_data.level}</span>
                  </div>
                ) : null
              )}

              <div
                className="overall-stats"
                onClick={() => setSelectedSkill("overall")}
                style={{ cursor: "pointer" }}
              >
                <div className="overall-stats-text" data-xp={humanizeNumber(player.skills.overall.xp)}>
                  <span className="overall-label">Total level:</span>
                  <span className="overall-value">{player.skills.overall.level}</span>
                </div>
              </div>
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
      {/* Centered graph for all players' selected skill XP */}
      <PlayerHistoryChart historyData={historyData} selectedSkill={selectedSkill} />
    </>
  );
}

export default PlayerStats;