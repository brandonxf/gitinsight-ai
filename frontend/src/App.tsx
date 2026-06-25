import { Route, Routes } from "react-router-dom";

import Analysis from "./routes/Analysis";
import Home from "./routes/Home";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/analysis/:jobId" element={<Analysis />} />
    </Routes>
  );
}
