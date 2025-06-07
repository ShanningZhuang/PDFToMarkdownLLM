---
layout: default
---

# The AI Core

<div class="grid grid-cols-2 gap-8 items-center">
  <div>
    <ul class="text-lg space-y-3 font-mono">
      <li><span class="font-bold text-gray-500">INPUT:</span> Raw, messy text</li>
      <li><span class="font-bold text-gray-500">ENGINE:</span> vLLM + Qwen-32B</li>
      <li><span class="font-bold text-gray-500">PROCESS:</span> Streamed Post-processing</li>
      <li><span class="font-bold text-gray-500">OUTPUT:</span> Clean, structured Markdown</li>
    </ul>
    <div class="mt-4 text-center">
      <carbon-chip class="text-8xl mx-auto text-purple-500" />
    </div>
  </div>
  <div>
    <p class="text-xl font-semibold">The "Magic" Prompt:</p>
    <div class="mt-2 p-3 bg-gray-100 rounded-lg text-xs prose">
      <p>You are a Markdown formatting expert. Please clean up and fix the following poorly formatted text converted from a PDF. You need to:</p>
      <ol>
        <li>Correct wrong line breaks and merge paragraphs.</li>
        <li>Identify and correctly mark up headings of all levels.</li>
        <li>Fix the formatting of tables and lists.</li>
        <li>Remove garbled text introduced by OCR or encoding errors.</li>
      </ol>
      <p><strong>Please directly output the cleaned, complete Markdown text without any explanations or extra conversation.</strong></p>
    </div>
  </div>
</div> 