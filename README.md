# Transformer Graph RCA

基于大语言模型、因果图谱和向量检索的变压器故障根因诊断原型。系统从变压器故障资料中沉淀“原因 → 现象/结果”关系；诊断时先从用户描述中识别故障事件，再将事件映射到图谱节点，沿因果边反向追溯。当路径出现分支时，系统生成检查问题，并根据用户反馈选择后续路径，直到到达可能的根因节点，最后由大模型汇总诊断结论。

> 本项目输出用于辅助分析，不能代替现场试验、保护规程和专业人员判断。

## 核心能力

- 交互式根因分析：支持多条候选路径并行、无分支路径自动推进、分支处向用户询问。
- 图谱语义入口：使用向量检索把用户表述映射到现有图谱节点，降低同义表达带来的影响。
- 专业对话：结合检索到的因果关系和参考文献，以 SSE 流式返回推理、结论和后续建议。
- 多模态上下文：对话接口可读取 TXT、PDF、DOC/DOCX，或使用通义千问视觉模型理解图片。
- 过程留痕：按用户保存诊断历史、完整诊断过程和聊天历史。
- 参考文献管理：支持资料上传、查询、预览和删除。

## 实现原理

### 1. 知识与索引

当前仓库已经包含处理后的知识资产：

- `static/references/`：原始变压器故障参考资料。
- `graph/transformer_docs/`：从资料中抽取的句子及 `cause-effect` 因果对。
- `graph/graph.json`：合并后的因果图。每项包含 `id`、`effect` 和 `cause[]`；内存中建立从结果节点指向原因节点的边，以便从故障现象反向追根。
- `vectorbase/dbs/Chroma/graph/`：图节点索引，用于把用户事件映射到最相似的 `effect` 节点。
- `vectorbase/dbs/Chroma/transformers_with_title_qwen/`：带文献标题、原句和因果对元数据的资料索引，用于对话 RAG。

仓库当前的 `graph.json` 约含 2,894 个结果条目、5,235 个去重节点。该统计仅描述当前提交的数据快照，后续重新抽取或合并后会变化。

图中的关系方向可以表示为：

```text
用户观察到的现象（effect）
          │
          ▼ 反向追溯
候选原因（cause） ──► 更深层原因 ──► 根因
```

向量库的配置保存在各库目录下的 `config.json`。主流程目前使用阿里云百炼的 `text-embedding-v4`（1024 维）；代码也保留了 Ollama `bge-m3` 的本地嵌入实现。创建索引的示例位于 `vectorbase/Chroma_method.py` 的 `__main__` 区域，属于离线维护操作，正常启动服务无需重建索引。

### 2. 交互式诊断

诊断由 `graph.py` 中的 `FaultAnalyseAgent` 编排：

1. `EventIdentifyAgent` 调用 `qwen-plus`，从用户故障描述中抽取 `<event>` 事件。
2. `InitFaultNodeAgent` 在 `graph` 向量库中为每个事件检索 Top-1 相似节点。
3. 每个入口节点创建一条 `ReasonPath`。`ReasonPath.explore()` 会沿唯一原因自动前进，直到叶节点或分支节点。
4. 遇到多个原因时，`GenerateChoiceAgent` 根据当前路径和候选节点生成可由用户确认的检查问题。
5. 用户提交反馈后，`DecideNextAgent` 综合路径、候选节点和反馈，选出最可能的下一节点。
6. 多条路径采用轮转方式继续搜索；所有路径到达叶节点后，`FinalAnalyseAgent` 生成最终分析，并写入历史文件。

`ReasonPath` 的字符串形式为 `现象<-原因<-更深层原因`。这里的箭头表示诊断追溯方向，并非知识抽取时自然语言中的因果方向。

### 3. 专业对话与 RAG

`ChatAgent` 维护多轮消息，并通过 `qwen-plus` 流式回答：

1. 接收文本问题以及可选的上传文件。
2. 文档通过 `utils/file_utils.py` 提取文本；图片通过 `qwen3-vl-plus` 转成描述。
3. `DecideIfReferenceAgent` 判断问题是否需要资料支撑。
4. 如需要，则在 `transformers_with_title_qwen` 中检索 Top-3 相关句子，将标题与因果对加入模型上下文。
5. 通过 SSE 依次发送 `begin`、多个 `chunk` 和 `end` 事件，并保存聊天历史。

模型被要求以 `<PHASE:REASONING>`、`<PHASE:CONCLUSION>`、`<PHASE:NEXT_ACTIONS>` 三阶段组织领域回答。

## 项目结构

```text
graph_rca/
├─ api.py                     # Flask HTTP/SSE 服务，当前主要启动入口
├─ graph.py                   # 因果图加载与 FaultAnalyseAgent 编排
├─ fault_node.py              # 图节点
├─ reason_path.py             # 诊断路径与自动游走逻辑
├─ agent/                     # 事件抽取、提问、选路、总结、对话等 Agent
├─ llm/                       # Qwen/OpenAI 兼容接口与 Ollama 封装
├─ embedding/                 # 嵌入模型封装
├─ vectorbase/                # Chroma 封装及持久化向量库
├─ dataLoader/                # 因果数据到 LangChain Document 的加载器
├─ graph/                     # 因果图、抽取结果及辅助数据
├─ static/references/         # 可检索/预览的原始参考文献
├─ history/                   # 用户、聊天、诊断结果和诊断过程（运行数据）
├─ temp/                      # 对话附件的临时上传目录
├─ web/                       # Vue 3 + Vite 早期演示前端
├─ user/、mysite/、manage.py   # 未接入当前 Flask 主链路的 Django 用户模块骨架
└─ environment_utf8.yml       # Conda 环境快照
```

`path.py`、`reason_path.py`、`show_path.py`、`pairwise_causality.json`、`graded_causality.json` 等文件主要用于图谱构建、整理或实验，不参与 Flask 服务的常规请求链路。

## 环境要求

- Python：环境文件锁定为 3.13.7。
- Conda（推荐用于复现完整 Python 环境）。
- Node.js：`^20.19.0` 或 `>=22.12.0`（仅运行 `web/` 时需要）。
- 阿里云百炼 API Key：文本模型、视觉模型及当前 Qwen 向量库查询均需要。
- 网络可访问阿里云百炼服务。

配置密钥：

```powershell
$env:QWEN_KEY = "你的百炼 API Key"
```

Linux/macOS：

```bash
export QWEN_KEY="你的百炼 API Key"
```

代码会将该值同时用于 OpenAI 兼容接口和 LangChain `ChatTongyi`。不要把真实密钥写入仓库。

## 安装与启动

### 后端

```bash
conda env create -f environment_utf8.yml
conda activate TransformerGraphRAG
python api.py
```

默认监听 `http://127.0.0.1:5007`。可用以下请求检查：

```bash
curl http://127.0.0.1:5007/test
```

Linux 后台运行示例：

```bash
nohup python api.py > output.log 2>&1 &
```

注意：`api.py` 当前使用 Flask 开发服务器且 `debug=True`，只适合开发调试。生产部署应关闭调试模式、固定 `secret_key`，并使用合适的 WSGI 服务和反向代理；SSE 代理需关闭响应缓冲。

### 前端演示

```bash
cd web
npm install
npm run dev
```

当前 `web/src/App.vue` 是早期演示页面，接口地址仍写为 `localhost:5000`，且没有先调用 `/start` 建立 Flask Session；直接连接当前后端前，需要将地址改为 `http://localhost:5007`，启用跨域凭证并补齐会话初始化。完整产品前端应以本文的接口约定为准。

## API 使用流程

服务通过 Flask Session Cookie 关联内存中的 Agent。调用方必须在同一个 Cookie 会话中依次请求 `/start` 和后续 `/action/*`；浏览器跨域请求需携带 credentials，脚本调用可使用 Cookie Jar。内存 Agent 两小时无活动会在后续 `/start` 时惰性清理，服务重启后未完成会话也会丢失。

### 1. 创建会话

```bash
curl -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo-user"}' \
  http://127.0.0.1:5007/start
```

### 2. 发起根因分析

```bash
curl -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"context":"主变温度异常升高，并伴随油位下降"}' \
  http://127.0.0.1:5007/action/generate_graph
```

未结束时返回类似：

```json
{
  "is_final": false,
  "reason_paths": ["温度异常<-冷却系统异常"],
  "choices": ["冷却器是否停止运行？", "负荷是否超过额定值？"],
  "analyse_id": "..."
}
```

### 3. 提交用户反馈并继续游走

`choices` 是用户对上一轮问题的反馈，可传字符串或前端组织后的文本；它会作为整体交给大模型判断下一节点。

```bash
curl -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"choices":"冷却器运行正常，但负荷明显超过额定值"}' \
  http://127.0.0.1:5007/action/root_cause_analyse
```

重复该请求直到 `is_final` 为 `true`，最终响应包含 `reason_paths`、`final_summary` 和 `analyse_id`。

### 4. 流式专业对话

```bash
curl -N -c cookies.txt -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"query":"变压器油中乙炔升高通常说明什么？"}' \
  http://127.0.0.1:5007/action/chat
```

SSE 数据类型：

- `begin`：返回当前 `chat_id`。
- `chunk`：模型增量文本。
- `end`：本轮生成完成。

如需附件，先调用 `POST /upload`（multipart 字段名为 `file`），再在聊天 JSON 中附加返回的 `filename`。

### 其他接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/status` | 查询当前会话 Agent 状态（当前实现引用了未定义的 `state`，需修复后使用） |
| GET | `/end` | 结束会话并移除内存 Agent |
| POST | `/upload` | 上传聊天附件到 `temp/` |
| GET | `/files?q=关键词` | 列出或搜索参考文献 |
| POST | `/upload_reference` | 上传参考文献 |
| GET | `/files/<filename>` | 预览参考文献 |
| DELETE | `/delete/<filename>` | 删除参考文献 |
| POST | `/action/new_analyse` | 清空并新建诊断 |
| POST | `/action/new_chat` | 清空并新建对话 |
| POST | `/action/get_analyse_history` | 获取用户诊断历史列表 |
| POST | `/action/read_analyse_history` | 读取指定诊断结果 |
| POST | `/action/get_chat_history` | 获取用户聊天历史列表 |
| POST | `/action/read_chat_history` | 读取指定聊天历史 |
| POST | `/action/get_chat_ref_latest` | 获取最近一轮对话引用资料 |
| POST | `/action/get_chat_ref` | 获取当前对话累计引用资料 |
| POST | `/action/read_chat_ref` | 读取指定参考文献正文 |
| POST | `/action/get_node` | 查询图节点及其直接原因节点 |

除 `/action/chat` 外，`/action/<action_name>` 使用 JSON 请求和 JSON 响应。历史类接口中的 `user_id` 会由服务端从 Session 注入。

## 历史数据

- `history/users/<user_id>.json`：用户与聊天/分析记录的索引。
- `history/chats/<id>.json`：逐轮聊天消息。
- `history/analyses/<id>.json`：最终路径和总结。
- `history/process/<id>.json`：初始输入、每轮候选问题、用户反馈和路径状态。

这些文件是运行数据。部署时应保证目录可写，并根据隐私、容量和保留周期制定清理策略。当前实现没有数据库事务或并发写保护，不建议多个进程共享同一 `history/` 目录。

## 已知限制与维护注意事项

- 根因诊断依赖模型严格按标签、JSON或节点名输出；模型格式漂移可能导致解析失败或图节点查找异常。
- 初始节点采用 Top-1 语义匹配，没有相似度阈值；超出图谱覆盖范围的输入也可能被强制映射到某个节点。
- 图和 Agent 保存在进程内存中，不支持跨进程会话共享；生产环境需要外部会话/状态存储。
- `FaultGraph.graph` 是类级字典，多次实例化会复用节点；当前加载时会去重直接邻接节点，但维护时应留意共享状态。
- 上传和参考文献管理接口仍需加强鉴权、文件名校验、大小限制和清理机制后再暴露到公网。
- `environment_utf8.yml` 未显式列出 `python-docx`、`PyPDF2` 等全部可选文档解析依赖；相应格式不可读时，请按 `utils/file_utils.py` 的报错安装至少一种解析库。
- 上传参考文献只保存原文件，不会自动执行因果抽取、图合并或向量库增量更新；知识更新目前是独立的离线流程。
- `mysite/` 的 Django 配置仍引用仓库中不存在的 `rootCauseAnalyse` 应用，且未接入 Flask 主服务；不要将 `python manage.py runserver` 视为当前项目启动方式。

## 二次开发入口

- 修改诊断策略或响应格式：`graph.py`、`reason_path.py`。
- 修改模型提示词：`agent/prompt.py` 和 `agent/ChatAgent.py`。
- 切换大模型：`llm/` 以及各 Agent 的 `generate()`。
- 切换嵌入模型或重建索引：`embedding/`、`vectorbase/`。
- 修改因果数据格式：`dataLoader/JsonLoader.py` 与 `graph/graph.json`。
- 修改文件解析：`utils/file_utils.py`。
