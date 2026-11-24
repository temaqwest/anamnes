import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import { Tooltip } from "radix-ui"
import { App } from "../routes/app"
import "../styles/index.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Tooltip.Provider delayDuration={250}>
        <App />
      </Tooltip.Provider>
    </BrowserRouter>
  </StrictMode>,
)

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  void navigator.serviceWorker.register("/sw.js").catch(() => {
    console.warn("Не удалось включить офлайн-страницу Anamnes.")
  })
}
