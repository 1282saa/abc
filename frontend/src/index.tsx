import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router } from "react-router-dom";
import App from "./App";
import "./styles/index.css";

// React 앱의 루트 요소 생성
const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

// 앱 렌더링
root.render(
  <React.StrictMode>
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <App />
    </Router>
  </React.StrictMode>
);
