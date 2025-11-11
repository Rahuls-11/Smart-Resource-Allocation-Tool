import React from "react"
import ReactDOM from "react-dom/client"
import { createBrowserRouter, RouterProvider } from "react-router-dom"
import "./index.css"
import App from "./App"
import Home from "./pages/Home"
import Employees from "./pages/Employees"
import Projects from "./pages/Projects"
import Match from "./pages/Match"
import "./index.css";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "employees", element: <Employees /> },
      { path: "projects", element: <Projects /> },
      { path: "match", element: <Match /> },
    ],
  },
])

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
