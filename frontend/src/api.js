import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

export const getData = async () => {
  const response = await axios.get(`${API_BASE_URL}player_stats/`);
  return response.data;
};

export const getHistoryData = async (selectedSkill, playerNames) => {
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
  const response = await axios.get(`${API_BASE_URL}history_data/${selectedSkill}/?players=${playerNames}`);
  return response.data;
};
