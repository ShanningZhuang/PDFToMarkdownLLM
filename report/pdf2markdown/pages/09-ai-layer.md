---
layout: default
---

# AI 核心

<div class="grid grid-cols-2 gap-8 items-center">
  <div>
    <ul class="text-lg space-y-3 font-mono">
      <li><span class="font-bold text-gray-500">输入:</span> 原始的、混乱的文本</li>
      <li><span class="font-bold text-gray-500">引擎:</span> vLLM + Qwen-32B</li>
      <li><span class="font-bold text-gray-500">处理:</span> 流式后处理</li>
      <li><span class="font-bold text-gray-500">输出:</span> 干净、结构化的 Markdown</li>
    </ul>
    <div class="mt-4 text-center">
      <carbon-chip class="text-8xl mx-auto text-purple-500" />
    </div>
  </div>
  <div>
    <p class="text-xl font-semibold">“魔法”提示词:</p>
    <div class="mt-2 p-3 bg-gray-100 rounded-lg text-xs prose">
      <p>你是一位 Markdown 格式化专家。请清理并修复以下从 PDF 转换而来的格式不佳的文本。你需要：</p>
      <ol>
        <li>修正错误的换行并合并段落。</li>
        <li>识别并正确标记所有级别的标题。</li>
        <li>修复表格和列表的格式。</li>
        <li>移除由 OCR 或编码错误引入的乱码。</li>
      </ol>
      <p><strong>请直接输出清理后的完整 Markdown 文本，无需任何解释或额外对话。</strong></p>
    </div>
  </div>
</div> 