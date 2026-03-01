# nanobot 离线部署与测试报告

## 部署环境信息

- **Python 环境**: `/home/yy/myenv` (Python 3.12.12)
- **Ollama 服务**: `http://172.24.16.1:11434`
- **使用模型**: `qwen3:14b`
- **安装方式**: pip install -e . (源码开发模式)
- **部署时间**: 2026-03-02

## 部署步骤

### 1. 安装 nanobot

```bash
cd /home/yy/nanobot
/home/yy/myenv/bin/pip install -e .
```

✓ 安装成功，版本: v0.1.4

### 2. 初始化配置

```bash
/home/yy/myenv/bin/nanobot onboard
```

✓ 配置文件创建成功: `~/.nanobot/config.json`
✓ 工作区创建成功: `~/.nanobot/workspace/`

### 3. 配置 Ollama 提供商

编辑 `~/.nanobot/config.json`:

```json
{
  "agents": {
    "defaults": {
      "model": "ollama/qwen3:14b",
      "maxTokens": 8192,
      "temperature": 0.1,
      "maxToolIterations": 40,
      "memoryWindow": 100
    }
  },
  "providers": {
    "ollama": {
      "apiKey": "ollama",
      "apiBase": "http://172.24.16.1:11434"
    }
  },
  "tools": {
    "restrictToWorkspace": true
  }
}
```

✓ 配置成功

### 4. 验证部署

```bash
/home/yy/myenv/bin/nanobot status
```

输出:
```
🐈 nanobot Status

Config: /home/yy/.nanobot/config.json ✓
Workspace: /home/yy/.nanobot/workspace ✓
Model: ollama/qwen3:14b
Ollama: ✓ http://172.24.16.1:11434
```

✓ 所有组件正常

## 功能测试

### 测试 1: 基本对话能力

命令:
```bash
/home/yy/myenv/bin/nanobot agent -m "你好，请介绍一下你自己"
```

结果:
- ✓ 模型响应正常
- ✓ 使用 message 工具发送回复
- 内容: "你好！我是nanobot，一个帮助你完成各种任务的AI助手。我可以在你的工作区中读写文件、执行命令、搜索网络信息，还能设置提醒。"

**Tool Trace 分析**:
```json
{
  "event": "tool_call",
  "tool": "message",
  "arguments": {
    "content": "你好！我是nanobot...",
    "channel": "cli",
    "chat_id": "direct"
  },
  "result": "Message sent to cli:direct"
}
```

### 测试 2: 文件系统操作

测试任务:
- 列出工作区文件
- 读取系统文件
- 创建测试文件

结果:
- ⚠️ 模型倾向于使用 message 工具直接回答，而不是调用文件系统工具
- 原因分析: qwen3:14b 模型的 function calling 能力较弱，更倾向于直接回复

### 测试 3: 命令执行

测试命令:
- `date`
- `uname -a`

结果:
- ⚠️ 同样的问题，模型使用 message 工具而不是 exec 工具

### 测试 4: Tool Trace Dashboard

命令:
```bash
/home/yy/myenv/bin/nanobot trace -n 10
```

结果:
- ✓ Tool trace 日志正常记录
- ✓ 日志文件: `~/.nanobot/logs/tool_trace.jsonl`
- ✓ 包含完整的工具调用信息（时间、工具名、参数、结果）

### 测试 5: 内部编排器 (Internal Orchestrator)

尝试使用 `nanobot-internal` 命令:

结果:
- ✗ API 路径不兼容
- 原因: Ollama 使用 `/api/chat` 而非 OpenAI 兼容的 `/v1/chat/completions`
- 建议: 需要配置 Ollama 的 OpenAI 兼容层或使用 vLLM

## 观察与建议

### 当前状态

✓ **成功的部分**:
1. nanobot 安装和配置成功
2. Ollama 连接正常
3. 基本对话功能正常
4. Tool trace 日志系统工作正常
5. 工作区隔离功能已启用 (restrictToWorkspace: true)

⚠️ **需要改进的部分**:
1. qwen3:14b 模型的 function calling 能力较弱
2. 模型倾向于使用 message 工具而非特定功能工具
3. CLI 模式下 message 工具的输出未正确显示

### 优化建议

#### 1. 模型选择

建议尝试以下模型中 function calling 能力更强的：
- `qwen2.5:14b` - 相比 qwen3 可能有更好的工具调用能力
- `glm4:9b` - 智谱 GLM-4 在 function calling 方面表现较好
- `granite3.3:8b` - IBM Granite 可能更稳定

#### 2. 提示词优化

可以调整系统提示词，强调：
- 优先使用工具而非直接回答
- 明确工具调用的格式要求

#### 3. 使用 vLLM

如果需要更好的 OpenAI 兼容性:
```bash
# 使用 vLLM 启动模型
vllm serve qwen3:14b --port 8000

# 配置 nanobot 使用 vLLM
{
  "providers": {
    "vllm": {
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "local"
    }
  },
  "agents": {
    "defaults": {
      "model": "qwen3:14b"
    }
  }
}
```

#### 4. CLI 输出修复

当前 CLI 模式下，模型使用 message 工具时响应不显示。这是一个已知问题，需要在 CLI 命令中添加消息捕获逻辑。

## 实际应用场景测试

由于模型限制，以下是实际可以工作的场景：

### ✓ 适合的场景

1. **知识问答**: 模型可以直接回答的问题
2. **文本生成**: 写作、总结等
3. **简单对话**: 基本交互
4. **使用 message 工具的场景**: 模型愿意使用 message 时

### ⚠️ 需要更好模型的场景

1. **文件操作**: 需要精确的 read_file/write_file 调用
2. **命令执行**: 需要使用 exec 工具
3. **复杂工具链**: 需要多步工具调用
4. **Web 搜索**: 需要 web_search/web_fetch 工具

## 部署验证清单

- [x] Python 环境配置
- [x] nanobot 安装
- [x] 配置文件初始化
- [x] Ollama 连接测试
- [x] 基本对话测试
- [x] Tool trace 日志验证
- [ ] 文件系统工具测试（需要更好的模型）
- [ ] 命令执行工具测试（需要更好的模型）
- [ ] Web 搜索测试（需要 API key 和更好的模型）
- [ ] Skill 测试（需要更好的模型）

## 下一步行动

1. **尝试其他模型**: 测试 qwen2.5、glm4 或 granite3.3
2. **配置 vLLM**: 设置 OpenAI 兼容的 API 端点
3. **优化提示词**: 调整系统提示词以改善工具调用
4. **测试 Skills**: 在模型工具调用改善后测试内置 skills
5. **配置 Channel**: 测试 Telegram/Discord 等聊天频道集成

## 附录：有用的命令

```bash
# 查看状态
/home/yy/myenv/bin/nanobot status

# CLI 交互
/home/yy/myenv/bin/nanobot agent

# 单次提问
/home/yy/myenv/bin/nanobot agent -m "你的问题"

# 查看工具调用记录
/home/yy/myenv/bin/nanobot trace -n 20

# 查看 tool trace 日志
tail -f ~/.nanobot/logs/tool_trace.jsonl | python3 -m json.tool

# 列出 Ollama 模型
curl http://172.24.16.1:11434/api/tags | python3 -m json.tool | grep name

# 测试 Ollama API
curl http://172.24.16.1:11434/api/generate -d '{
  "model": "qwen3:14b",
  "prompt": "Hello",
  "stream": false
}'
```

## 总结

nanobot 已成功部署在离线环境中，Ollama 连接正常，基本功能可用。主要限制在于 qwen3:14b 模型的 function calling 能力较弱，导致工具调用不够理想。建议更换模型或使用 vLLM 以获得更好的工具调用体验。

整体而言，部署流程顺利，架构设计合理，文档完善，是一个轻量级且易于研究的 AI Agent 框架。
