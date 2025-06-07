---
layout: default
---

# High-Level Architecture

<div class="flex items-center justify-between text-center text-lg mt-20 font-sans">
  <!-- Frontend -->
  <div class="w-1/4 p-4 bg-blue-50 rounded-lg shadow-md">
    <h3 class="font-bold text-blue-800">Frontend</h3>
    <p>Next.js</p>
  </div>
  
  <!-- Arrows -->
  <div class="w-1/6 flex flex-col items-center">
    <span class="text-2xl font-bold text-gray-400">→</span>
    <span class="text-xs">API Request</span>
    <span class="text-2xl font-bold text-gray-400 mt-2">←</span>
    <span class="text-xs">Streaming Response</span>
  </div>

  <!-- Backend -->
  <div class="w-1/4 p-4 bg-purple-50 rounded-lg shadow-md">
    <h3 class="font-bold text-purple-800">Backend</h3>
    <p>FastAPI</p>
  </div>
  
  <!-- Arrows -->
  <div class="w-1/6 flex flex-col items-center">
    <span class="text-2xl font-bold text-gray-400">→</span>
    <span class="text-xs">Text Processing</span>
    <span class="text-2xl font-bold text-gray-400 mt-2">←</span>
    <span class="text-xs">Markdown</span>
  </div>

  <!-- AI Service -->
  <div class="w-1/4 p-4 bg-green-50 rounded-lg shadow-md">
    <h3 class="font-bold text-green-800">AI Service Layer</h3>
    <p>vLLM</p>
  </div>
</div>

<div class="mt-8 text-center text-gray-600">
  <p>This design ensures the independence and scalability of each module.</p>
</div> 