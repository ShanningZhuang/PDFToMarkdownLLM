
# 项目概览：PDF 上传 + Markdown 转换 + 大模型清洗

该项目实现一个前后端分离的服务，用于将用户上传的 PDF 文档转换为 Markdown 格式，并调用本地部署的大语言模型（通过 vLLM）对 Markdown 内容进行清洗、纠错，最终返回给用户。

---

## 📁 项目结构

```
repo-root/
├── backend/               # 后端服务：FastAPI 接收上传、调用 MarkItDown 和 vLLM
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              # 前端界面：文件上传、进度显示、Markdown 预览
│   ├── src/
│   │   └── App.tsx
│   └── Dockerfile
├── docker-compose.yml     # 编排服务：启动前端、后端、vLLM
└── README.md
```

---

## 🧩 模块说明

### backend/

- Python + FastAPI
- `/upload` 接口：接收前端上传的 PDF 文件
- 使用 `MarkItDown` 将 PDF 转为 Markdown
- 调用本地部署的 `vLLM` 模型，清洗 Markdown 中的乱码
- 返回清洗后的 Markdown 文本

### frontend/

- 采用Next.js、React、TypeScript、TailwindCSS
- 文件上传控件，使用 `fetch` + `FormData` 将 PDF 文件发送至后端
- 上传后显示解析结果（Markdown 格式）
- 使用 `ReactMarkdown` 等库渲染内容

### vLLM 服务

- 通过 OpenAI 接口风格提供 `/v1/chat/completions`
- 启动时指定模型路径（如 `mistralai/Mistral-7B-Instruct-v0.3`）
- 使用 GPU 加速推理

### docker-compose.yml

- 启动三个服务：`frontend`、`backend`、`vllm`
- 设置端口映射、依赖关系和资源限制（如 GPU 访问）

---

## 🚀 使用流程

1. 用户打开前端页面并上传 PDF 文件
2. 后端接收并转换为初步 Markdown 文本
3. 后端调用 vLLM 进行清洗
4. 最终清洗后的 Markdown 返回给前端展示

