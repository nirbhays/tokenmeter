import { TokenMeterClient } from '../src/client';

describe('TokenMeter Node.js SDK', () => {
  test('should create client with default config', () => {
    const client = new TokenMeterClient({ apiKey: 'test-key' });
    expect(client.apiKey).toBe('test-key');
    expect(client.baseUrl).toBe('http://localhost:8000');
  });

  test('should have chat.completions namespace', () => {
    const client = new TokenMeterClient({ apiKey: 'test-key' });
    expect(client.chat).toBeDefined();
    expect(client.chat.completions).toBeDefined();
    expect(typeof client.chat.completions.create).toBe('function');
  });

  test('should have models namespace', () => {
    const client = new TokenMeterClient({ apiKey: 'test-key' });
    expect(client.models).toBeDefined();
    expect(typeof client.models.list).toBe('function');
  });

  test('should use custom base URL', () => {
    const client = new TokenMeterClient({
      apiKey: 'test-key',
      baseUrl: 'https://proxy.tokenmeter.dev',
    });
    expect(client.baseUrl).toBe('https://proxy.tokenmeter.dev');
  });

  test('should strip trailing slash from base URL', () => {
    const client = new TokenMeterClient({
      apiKey: 'test-key',
      baseUrl: 'http://localhost:8000/',
    });
    expect(client.baseUrl).toBe('http://localhost:8000');
  });
});
