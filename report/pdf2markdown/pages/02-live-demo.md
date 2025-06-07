---
layout: center
class: text-center
addons:
    - slidev-addon-qrcode
---

# Live Demo

<div class="mt-8">
  <p class="text-2xl">
    Try it yourself!
  </p>
</div>

<div class="mt-6 grid grid-cols-2 gap-8 items-center">
  <div>
    <a href="https://pdf2markdown.tech:24680/" target="_blank" 
       class="text-2xl bg-blue-500 hover:bg-blue-600 text-white px-8 py-4 rounded-lg inline-block transition-colors">
      🚀 Open Demo
    </a>
    <p class="mt-4 text-gray-500">https://pdf2markdown.tech:24680/</p>
  </div>
  <div>
  <QRCode     
    :width="100"
    :height="100"
    data="https://pdf2markdown.tech:24680"/>
  </div>
</div>

<div class="mt-8 text-gray-600">
  <p>View this presentation at: https://pdf2markdown.tech:24680/report/</p>
</div> 