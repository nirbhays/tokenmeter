/**
 * TokenMeter Node.js SDK — Drop-in replacement for the OpenAI Node.js client.
 *
 * @example
 * // Before:
 * import OpenAI from 'openai';
 *
 * // After (one-line change):
 * import OpenAI from 'tokenmeter';
 *
 * const client = new OpenAI();
 * const response = await client.chat.completions.create({
 *   model: 'gpt-4.1',
 *   messages: [{ role: 'user', content: 'Hello!' }],
 * });
 * console.log(response.tm_cost_usd); // Cost tracking!
 */

export { TokenMeterClient as default, TokenMeterClient as OpenAI } from './client';
export type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatCompletionChunk,
  Message,
  Choice,
  Usage,
  TokenMeterConfig,
  StreamChoice,
} from './types';
