import axios from "axios";

const api = axios.create({
  // Your Flask server is running on port 5001 per your log
  baseURL: "http://localhost:5001",
  withCredentials: false,
});

export default api;
