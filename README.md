# PDF to Markdown Converter with LLM

A complete full-stack application for converting PDF documents to clean Markdown format using AI-powered text processing. Features real-time streaming, modern UI, and Docker deployment.

🌐 **Live Demo**: [https://pdf2markdown.tech:24680/](https://pdf2markdown.tech:24680/)
📈 **Report**: [https://pdf2markdown.tech:24680/report/](https://pdf2markdown.tech:24680/report/)

## 🚀 Features

- **📄 PDF Upload**: Drag & drop interface with file validation
- **🤖 AI-Powered Cleaning**: Uses vLLM with Mistral-7B for intelligent text processing
- **⚡ Real-time Streaming**: Watch markdown appear token by token (ChatGPT-style)
- **👀 Live Preview**: Switch between rendered markdown and raw text
- **📊 Performance Metrics**: Track processing time, token counts, and throughput
- **🎨 Modern UI**: Responsive design with TailwindCSS
- **🐳 Docker Ready**: Complete containerization with docker-compose
- **🔧 Health Monitoring**: Real-time backend and vLLM status checking

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     vLLM        │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (Mistral-7B)   │
│   Port: 3000    │    │   Port: 8001    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Tech Stack

**Frontend:**
- Next.js 14 with App Router
- TypeScript
- TailwindCSS
- React Markdown with syntax highlighting
- Lucide React icons

**Backend:**
- FastAPI (Python)
- MarkItDown for PDF conversion
- Streaming response support
- Health monitoring

**AI/LLM:**
- vLLM for model serving
- Mistral-7B-Instruct-v0.3
- OpenAI-compatible API
- GPU acceleration support

## 🚀 Quick Start

### 🌐 Try Online

Visit the live demo at **[http://pdf2markdown.tech:24680/](http://pdf2markdown.tech:24680/)** to try the application without any setup!

### 🐳 Local Deployment

#### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU (for vLLM acceleration)
- 8GB+ RAM recommended

#### 1. Clone and Start

```bash
git clone https://github.com/ShanningZhuang/PDFToMarkdownLLM.git
cd PDFToMarkdownLLM

# Start all services
docker-compose up -d
```

#### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **vLLM API**: http://localhost:8000

#### 3. Upload and Convert

1. Open http://localhost:3000 (or visit [pdf2markdown.tech](http://pdf2markdown.tech/))
2. Drag & drop a PDF file or click to browse
3. Configure processing options (LLM cleaning, streaming)
4. Watch the real-time conversion
5. Download the converted markdown

## 🛠️ Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### vLLM Setup (Local)

```bash
# Install vLLM
pip install vllm

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --host 0.0.0.0 \
  --port 8000
```

## 📁 Project Structure

```
PDFToMarkdownLLM/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   ├── components/      # React components
│   │   └── lib/             # Utilities and API services
│   ├── package.json
│   └── Dockerfile
├── backend/                  # FastAPI backend service
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile
│   └── API_DOCS.md          # API documentation
├── docker-compose.yml       # Service orchestration
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Backend:**
```env
VLLM_BASE_URL=http://localhost:8000
VLLM_AUTO_START=true
MAX_FILE_SIZE_MB=50
```

### Docker Compose Override

Create `docker-compose.override.yml` for custom configurations:

```yaml
version: '3.8'
services:
  vllm:
    environment:
      - MODEL_NAME=your-preferred-model
    command: >
      --model your-preferred-model
      --max-model-len 8192
```

## 📊 API Endpoints

### Core Endpoints

- `POST /upload` - Upload PDF with LLM cleaning
- `POST /upload-stream` - Upload PDF with streaming response
- `POST /convert-text` - Convert PDF without LLM cleaning
- `POST /clean-markdown` - Clean existing markdown
- `POST /clean-markdown-stream` - Clean markdown with streaming

### Management Endpoints

- `GET /health` - System health check
- `GET /vllm/status` - vLLM service status
- `POST /vllm/start` - Start vLLM service
- `POST /vllm/stop` - Stop vLLM service

See [backend/API_DOCS.md](backend/API_DOCS.md) for complete API documentation.

## 🎯 Usage Examples

### Online Usage

Simply visit [http://pdf2markdown.tech/](http://pdf2markdown.tech/) and start converting your PDFs!

### API Usage

#### Basic PDF Conversion

```bash
curl -X POST "http://pdf2markdown.tech/api/upload" \
  -F "file=@document.pdf"
```

#### Streaming Conversion

```bash
curl -X POST "http://pdf2markdown.tech/api/upload-stream" \
  -F "file=@document.pdf" \
  --no-buffer
```

#### Health Check

```bash
curl http://pdf2markdown.tech/api/health
```

## 🔍 Monitoring and Debugging

### Health Checks

The application provides comprehensive health monitoring:

- Frontend: Backend connectivity status
- Backend: API health and vLLM connectivity
- vLLM: Model loading and GPU status

### Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f vllm
```

### Performance Monitoring

The frontend displays real-time metrics:
- Processing duration
- Token generation speed
- File size and character count
- First token latency (streaming mode)

## 🚨 Troubleshooting

### Common Issues

**vLLM fails to start:**
- Ensure NVIDIA drivers are installed
- Check GPU memory availability
- Verify model download permissions

**Backend connection errors:**
- Check if backend is running on port 8001
- Verify firewall settings
- Check Docker network connectivity

**Frontend build errors:**
- Clear node_modules and reinstall
- Check Node.js version (18+ required)
- Verify environment variables

### Debug Mode

Enable debug logging:

```bash
# Backend debug
export LOG_LEVEL=DEBUG

# Frontend debug
export NEXT_PUBLIC_DEBUG=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [MarkItDown](https://github.com/microsoft/markitdown) for PDF conversion
- [vLLM](https://github.com/vllm-project/vllm) for efficient LLM serving
- [Mistral AI](https://mistral.ai/) for the language model
- [Next.js](https://nextjs.org/) and [FastAPI](https://fastapi.tiangolo.com/) teams

## 📞 Support

For support and questions:
- Try the live demo: [http://pdf2markdown.tech/](http://pdf2markdown.tech/)
- Create an issue in the [GitHub repository](https://github.com/ShanningZhuang/PDFToMarkdownLLM)
- Check the [API documentation](backend/API_DOCS.md)
- Review the troubleshooting section above

---

**Created by [Shanning Zhuang 庄善宁](https://shanningzhuang.github.io/) - PhD Student at Tsinghua University** 