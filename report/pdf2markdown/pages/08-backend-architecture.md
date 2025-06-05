---
layout: default
---

# ⚡ Backend Architecture

## Technology Stack

<div class="grid grid-cols-2 gap-8">
  <div>
    <h3 class="text-xl font-semibold mb-4">🛠️ Core Technologies</h3>
    <ul class="space-y-3">
      <li class="flex items-center space-x-3">
        <span class="w-3 h-3 bg-green-500 rounded-full"></span>
        <span><strong>FastAPI</strong> - High-performance async API</span>
      </li>
      <li class="flex items-center space-x-3">
        <span class="w-3 h-3 bg-red-500 rounded-full"></span>
        <span><strong>MarkItDown</strong> - Initial PDF conversion</span>
      </li>
      <li class="flex items-center space-x-3">
        <span class="w-3 h-3 bg-blue-500 rounded-full"></span>
        <span><strong>Streaming</strong> - Real-time response support</span>
      </li>
      <li class="flex items-center space-x-3">
        <span class="w-3 h-3 bg-purple-500 rounded-full"></span>
        <span><strong>Health Monitoring</strong> - System status tracking</span>
      </li>
    </ul>
  </div>

  <div>
    <h3 class="text-xl font-semibold mb-4">🔧 Core Services</h3>
    <ul class="space-y-3">
      <li class="flex items-center space-x-3">
        <span class="text-blue-500">🔄</span>
        <span>PDF processing pipeline</span>
      </li>
      <li class="flex items-center space-x-3">
        <span class="text-green-500">🤖</span>
        <span>LLM integration & prompt engineering</span>
      </li>
      <li class="flex items-center space-x-3">
        <span class="text-purple-500">⚡</span>
        <span>Real-time streaming coordination</span>
      </li>
      <li class="flex items-center space-x-3">
        <span class="text-orange-500">📊</span>
        <span>System health monitoring</span>
      </li>
    </ul>
  </div>
</div>

## Processing Pipeline

```mermaid
graph LR
    A[PDF Upload] --> B[MarkItDown<br/>Conversion]
    B --> C[Text<br/>Preprocessing]
    C --> D[LLM<br/>Enhancement]
    D --> E[Streaming<br/>Response]
    E --> F[Frontend<br/>Display]
    
    style A fill:#fff3e0
    style B fill:#e8f5e8
    style C fill:#e3f2fd
    style D fill:#f3e5f5
    style E fill:#fce4ec
    style F fill:#e1f5fe
```

<div class="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400">
  <h4 class="font-semibold">🎯 Performance Optimizations</h4>
  <p class="text-sm mt-2">Async processing, streaming responses, and efficient memory management for large documents</p>
</div> 