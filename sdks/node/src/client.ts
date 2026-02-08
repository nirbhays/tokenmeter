/**
 * TokenMeter Node.js SDK Client
 */

import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatCompletionChunk,
  TokenMeterConfig,
} from './types';

class ChatCompletions {
  private client: TokenMeterClient;

  constructor(client: TokenMeterClient) {
    this.client = client;
  }

  async create(params: ChatCompletionRequest): Promise<ChatCompletionResponse | AsyncIterable<ChatCompletionChunk>> {
    const headers: Record<string, string> = {};
    if (params.tm_team) headers['X-TM-Team'] = params.tm_team;
    if (params.tm_feature) headers['X-TM-Feature'] = params.tm_feature;
    if (params.tm_routing_mode) headers['X-TM-Routing-Mode'] = params.tm_routing_mode;

    const body: Record<string, any> = { ...params };
    // Move TM fields to headers and body
    if (params.tm_team) body['x-tm-team'] = params.tm_team;
    if (params.tm_feature) body['x-tm-feature'] = params.tm_feature;
    if (params.tm_routing_mode) body['x-tm-routing-mode'] = params.tm_routing_mode;
    if (params.tm_cache !== undefined) body['x-tm-cache'] = params.tm_cache;

    // Clean up TM fields from body
    delete body.tm_team;
    delete body.tm_feature;
    delete body.tm_routing_mode;
    delete body.tm_cache;

    if (params.stream) {
      return this.createStream(body, headers);
    }

    const response = await this.client.request<ChatCompletionResponse>(
      'POST',
      '/v1/chat/completions',
      body,
      headers,
    );
    return response;
  }

  private async *createStream(
    body: Record<string, any>,
    headers: Record<string, string>,
  ): AsyncIterable<ChatCompletionChunk> {
    const url = `${this.client.baseUrl}/v1/chat/completions`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.client.apiKey}`,
        ...headers,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`TokenMeter API error: ${response.status} ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') return;

        try {
          const chunk: ChatCompletionChunk = JSON.parse(payload);
          yield chunk;
        } catch {
          continue;
        }
      }
    }
  }
}

class Chat {
  public completions: ChatCompletions;

  constructor(client: TokenMeterClient) {
    this.completions = new ChatCompletions(client);
  }
}

class ModelsAPI {
  private client: TokenMeterClient;

  constructor(client: TokenMeterClient) {
    this.client = client;
  }

  async list() {
    return this.client.request<any>('GET', '/v1/models');
  }
}

export class TokenMeterClient {
  public apiKey: string;
  public baseUrl: string;
  public chat: Chat;
  public models: ModelsAPI;

  private timeout: number;

  constructor(config: TokenMeterConfig = {}) {
    this.apiKey = config.apiKey || process.env.TOKENMETER_API_KEY || process.env.OPENAI_API_KEY || '';
    this.baseUrl = (config.baseUrl || process.env.TOKENMETER_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
    this.timeout = config.timeout || 120000;

    this.chat = new Chat(this);
    this.models = new ModelsAPI(this);
  }

  async request<T>(method: string, path: string, body?: any, extraHeaders?: Record<string, string>): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
      'User-Agent': 'tokenmeter-node/0.1.0',
      ...extraHeaders,
    };

    const options: RequestInit = {
      method,
      headers,
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    options.signal = controller.signal;

    try {
      const response = await fetch(url, options);
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(
          errorBody.error?.message || `TokenMeter API error: ${response.status}`,
        );
      }

      return (await response.json()) as T;
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`TokenMeter request timed out after ${this.timeout}ms`);
      }
      throw error;
    }
  }
}
