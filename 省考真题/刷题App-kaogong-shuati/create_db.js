const { DatabaseSync } = require('node:sqlite');
const AI_CONFIG_DB = './ai-config.db';
const db = new DatabaseSync(AI_CONFIG_DB);
db.exec('PRAGMA journal_mode = WAL');
db.exec("CREATE TABLE IF NOT EXISTS ai_agents (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL UNIQUE,
  description TEXT DEFAULT '',
  system_prompt TEXT NOT NULL,
  skill TEXT DEFAULT '',
  base_url TEXT NOT NULL,
  api_key TEXT DEFAULT '',
  model TEXT NOT NULL,
  temperature REAL DEFAULT 0.5,
  max_tokens INTEGER DEFAULT 1500,
  enabled INTEGER DEFAULT 0,
  updated_at TEXT DEFAULT (datetime('now','localtime'))
)");
const agents = [
  { id: 1, name: "行测解析 AI", role: "xingce-explainer", system_prompt: "你是一名资深公务员考试行测讲师...", base_url: "https://opencode.ai/zen/v1", api_key: "sk-TFZyZw2wRgLD78Ptyonc1Knm7CUM69PQWb4L4cg9OABpguQx", model: "deepseek-v4-flash-free" },
  { id: 2, name: "申论批改 AI", role: "shenlun-grader", system_prompt: "你是一名严格的公务员考试申论阅卷官...", base_url: "https://opencode.ai/zen/v1", api_key: "sk-B4Ura1jIYueXZmGkngI2WzkiyU4UBwcsUYk4q2dHoOhEOGlo", model: "deepseek-v4-flash-free" },
  { id: 4, name: "识图转写员", role: "image-reader", system_prompt: "你是一名图像识别转写助手...", base_url: "https://open.bigmodel.cn/api/paas/v4", api_key: "sk-0gxsyZkpshxGdhk5Ru3JwpZQHkDDpiuX4slariWoIJRDS9dk", model: "GLM-4.1V-Thinking-Flash" }
];
for (const a of agents) {
  const exists = db.prepare("SELECT id FROM ai_agents WHERE role = ?").get(a.role);
  if (!exists) {
    const stmt = db.prepare("INSERT INTO ai_agents (id, name, role, system_prompt, base_url, api_key, model, updated_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))");
    stmt.run(a.id, a.name, a.role, a.system_prompt || "", a.base_url, a.api_key, a.model);
    console.log("Inserted:", a.name);
  } else {
    console.log("Already exists:", a.name);
  }
}
const all = db.prepare("SELECT id, name, role, api_key FROM ai_agents").all();
console.log("Total agents:", all.length);
all.forEach(a => console.log(a.id + ":" + a.name + ":" + a.api_key.substring(0, 6) + "..."));
