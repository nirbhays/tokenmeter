/**
 * TypeScript type definitions for the TokenMeter Node.js SDK.
 */

export interface TokenMeterConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
}

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content?: string | null;
  name?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface ToolSpec {
  type: 'function';
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, any>;
  };
}

export interface ResponseFormat {
  type: 'text' | 'json_object' | 'json_schema';
  json_schema?: Record<string, any>;
}

export interface ChatCompletionRequest {
  model: string;
  messages: Message[];
  temperature?: number;
  top_p?: number;
  n?: number;
  stream?: boolean;
  stop?: string | string[];
  max_tokens?: number;
  max_completion_tokens?: number;
  tools?: ToolSpec[];
  tool_choice?: string | Record<string, any>;
  response_format?: ResponseFormat;
  user?: string;
  seed?: number;
  // TokenMeter extensions
  tm_team?: string;
  tm_feature?: string;
  tm_routing_mode?: string;
  tm_cache?: boolean;
}

export interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface Choice {
  index: number;
  message: Message;
  finish_reason: string | null;
}

export interface ChatCompletionResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: Choice[];
  usage?: Usage;
  // TokenMeter extensions
  tm_provider?: string;
  tm_cost_usd?: number;
  tm_latency_ms?: number;
  tm_cached?: boolean;
  tm_routed_from?: string;
}

export interface DeltaMessage {
  role?: string;
  content?: string;
  tool_calls?: ToolCall[];
}

export interface StreamChoice {
  index: number;
  delta: DeltaMessage;
  finish_reason: string | null;
}

export interface ChatCompletionChunk {
  id: string;
  object: 'chat.completion.chunk';
  created: number;
  model: string;
  choices: StreamChoice[];
  usage?: Usage;
}
