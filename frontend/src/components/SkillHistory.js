import React, { useEffect, useState } from "react";

function SkillHistory() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("/api/history_data/attack/?players=Player1,Player2")
      .then((response) => response.json())
      .then((json) => setData(json));
  }, []);

  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <h2>Skill History Data</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

export default SkillHistory;