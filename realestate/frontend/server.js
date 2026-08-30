import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();

const backendHost = process.env.BACKEND_HOST;
const backendUrl = backendHost ? `https://${backendHost}` : (process.env.BACKEND_URL || "http://localhost:8001");

app.use(createProxyMiddleware({ target: backendUrl, changeOrigin: true, pathFilter: "/api/**" }));

const distDir = path.join(__dirname, "dist");
app.use(express.static(distDir));
app.get("*", (req, res) => {
  res.sendFile(path.join(distDir, "index.html"));
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Curb frontend listening on port ${port}, proxying /api to ${backendUrl}`));
