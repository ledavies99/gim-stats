import React from "react";
import PlayerStats from "./components/PlayerStats";
import PlayerHistoryChart from "./components/PlayerHistoryChart";

function App() {
  return (
    <div>
      <h1 className="centered-title">Group Iron Man Stats</h1>
      <PlayerStats />
    </div>
  );
}

export default App;