# TokenMeter Roadmap

## Vision
Be the de-facto observability layer for LLM applications — as essential as logging is for traditional services.

## ✅ Shipped
- One-line drop-in integration (replace a single import)
- Real-time cost + token + latency tracking
- Smart model routing (up to 60% cost savings)
- OpenAI, Anthropic, Google Gemini support
- `<5ms` overhead

## 🔨 In Progress
- [ ] Mistral AI provider support
- [ ] LangChain callback integration
- [ ] CSV / JSON cost export

## 📋 Planned — Q2 2025
- [ ] Web dashboard for cost visualisation
- [ ] Per-feature / per-user cost attribution tags
- [ ] Budget alerts (Slack / email when threshold hit)
- [ ] OpenAI Assistants API support
- [ ] Streaming response cost tracking

## 📋 Planned — Q3 2025
- [ ] Ollama (local model) cost estimation
- [ ] Team / org cost sharing and allocation
- [ ] CI budget gates — fail PRs that exceed cost thresholds
- [ ] AWS Bedrock provider support

## 💡 Under Consideration
- Grafana dashboard plugin
- OpenTelemetry metrics export
- Cohere provider support
- LlamaIndex integration

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). Provider integrations are a great first contribution.
