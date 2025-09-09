import React, { useEffect, useState } from "react";
import { humanizeNumber } from "../utils";

function PlayerStats() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  // State for synchronized dropdowns
  const [openDropdown, setOpenDropdown] = useState({ bosses: false, today: false, week: false });

  useEffect(() => {
    fetch("/api/player_stats/")
      .then((res) => res.json())
      .then((data) => {
        setPlayers(data.players);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  if (!players.length) {
    return (
      <p>
        No player data could be retrieved. Please check your internet connection or if players have been added to the database.
      </p>
    );
  }

  // Helper for skill icon path
  const skillIcon = (skill) => `/static/images/${skill.toLowerCase()}.png`;

  // Handlers for synchronized dropdowns
  const handleDropdown = (type) => {
    setOpenDropdown((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  return (
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
          <details
            className="collapsible-section collapsible-boss-stats"
            open={openDropdown.bosses}
            onClick={(e) => {
              e.preventDefault();
              handleDropdown("bosses");
            }}
          >
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
          <details
            className="collapsible-section collapsible-xp-gained-today"
            open={openDropdown.today}
            onClick={(e) => {
              e.preventDefault();
              handleDropdown("today");
            }}
          >
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
          <details
            className="collapsible-section collapsible-xp-gained-week"
            open={openDropdown.week}
            onClick={(e) => {
              e.preventDefault();
              handleDropdown("week");
            }}
          >
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
  );
}

export default PlayerStats;