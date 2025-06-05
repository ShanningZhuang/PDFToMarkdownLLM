---
layout: default
class: slide-overflow
---

# 🏗️ System Architecture Overview

```mermaid
graph TB
    A[Frontend<br/>Next.js<br/>Port: 3000] -->|HTTP/WebSocket| B[Backend<br/>FastAPI<br/>Port: 8001]
    B -->|OpenAI API| C[vLLM Server<br/>Qwen-32B<br/>Port: 8000]
    
    D[User] -->|Upload PDF| A
    A -->|Drag & Drop<br/>Real-time UI| A
    B -->|MarkItDown<br/>Processing| B
    C -->|LLM Enhancement<br/>Streaming| C
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
```

<div class="mt-8 grid grid-cols-3 gap-6 text-center">
  <div class="p-4 bg-blue-50 rounded-lg">
    <h3 class="text-lg font-semibold mb-2">🎨 Frontend</h3>
    <p class="text-sm">React • TypeScript • TailwindCSS</p>
  </div>
  
  <div class="p-4 bg-purple-50 rounded-lg">
    <h3 class="text-lg font-semibold mb-2">⚡ Backend</h3>
    <p class="text-sm">FastAPI • Async • Streaming</p>
  </div>
  
  <div class="p-4 bg-green-50 rounded-lg">
    <h3 class="text-lg font-semibold mb-2">🤖 AI Layer</h3>
    <p class="text-sm">vLLM • GPU Optimized</p>
  </div>
</div> 