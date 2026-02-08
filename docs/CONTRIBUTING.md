# Contributing to TokenMeter

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

See [DEVELOPMENT.md](DEVELOPMENT.md) for local setup instructions.

## How to Contribute

### Bug Reports

Open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, etc.)

### Feature Requests

Open an issue describing the feature and its use case.

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `python -m pytest tests/ -v`
6. Lint your code: `ruff check . && ruff format .`
7. Commit with a descriptive message
8. Push and open a PR

### Code Style

- **Python**: Follow PEP 8, enforced by ruff
- **TypeScript**: ESLint with Next.js config
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)

### Architecture Decisions

For significant changes, please open an issue first to discuss the approach.

## Project Structure

```
tokenmeter/
├── backend/          # FastAPI proxy + API
├── frontend/         # Next.js dashboard
├── sdks/             # Python + Node.js SDKs
├── database/         # SQL schemas
├── infra/            # Terraform + Fly.io
├── tests/            # Backend tests
└── docs/             # Documentation
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
