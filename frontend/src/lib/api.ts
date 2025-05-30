const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface UploadResponse {
  success: boolean;
  filename: string;
  raw_markdown: string;
  cleaned_markdown: string;
  cleaned_with_llm: boolean;
  content_length: number;
  metadata: {
    original_filename: string;
    file_size_bytes: number;
    conversion_method: string;
    llm_cleaning: boolean;
  };
}

export interface CleanMarkdownResponse {
  success: boolean;
  original_content: string;
  cleaned_content: string;
  content_length: number;
}

export interface HealthResponse {
  api: string;
  vllm: string;
  vllm_process?: {
    process_running: boolean;
    process_pid: number;
    port: number;
    model: string;
    memory_usage_mb: number;
    gpu_available: boolean;
    service_responsive: boolean;
  };
}

export interface VLLMStatusResponse {
  process_running: boolean;
  process_pid?: number;
  port: number;
  model: string;
  memory_usage_mb?: number;
  gpu_available: boolean;
  service_responsive?: boolean;
}

export interface ApiError {
  detail: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  async getVLLMStatus(): Promise<VLLMStatusResponse> {
    const response = await fetch(`${this.baseUrl}/vllm/status`);
    if (!response.ok) {
      throw new Error(`VLLM status check failed: ${response.statusText}`);
    }
    return response.json();
  }

  async startVLLM(modelName?: string): Promise<{ success: boolean; message: string; status: VLLMStatusResponse }> {
    const response = await fetch(`${this.baseUrl}/vllm/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: modelName ? JSON.stringify({ model_name: modelName }) : undefined,
    });
    
    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Failed to start VLLM: ${response.statusText}`);
    }
    
    return response.json();
  }

  async stopVLLM(): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/vllm/stop`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Failed to stop VLLM: ${response.statusText}`);
    }
    
    return response.json();
  }

  async uploadPDF(file: File, cleanWithLLM: boolean = true): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseUrl}/upload?clean_with_llm=${cleanWithLLM}`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async uploadPDFStream(file: File): Promise<ReadableStreamDefaultReader<Uint8Array>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload-stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Upload stream failed: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('No response body for streaming');
    }

    return response.body.getReader();
  }

  async convertPDFToText(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/convert-text`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Conversion failed: ${response.statusText}`);
    }

    return response.json();
  }

  async cleanMarkdown(markdownContent: string): Promise<CleanMarkdownResponse> {
    const response = await fetch(`${this.baseUrl}/clean-markdown`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        markdown_content: markdownContent,
      }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Markdown cleaning failed: ${response.statusText}`);
    }

    return response.json();
  }

  async cleanMarkdownStream(markdownContent: string): Promise<ReadableStreamDefaultReader<Uint8Array>> {
    const response = await fetch(`${this.baseUrl}/clean-markdown-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        markdown_content: markdownContent,
      }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `Markdown cleaning stream failed: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('No response body for streaming');
    }

    return response.body.getReader();
  }
}

export const apiService = new ApiService(); 