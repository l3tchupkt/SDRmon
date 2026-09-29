# Contributing to SDRmon

Welcome! Thank you for considering contributing to SDRmon. 

## Philosophy

SDRmon aims to be a proper Unix hardware tool rather than a collection of scripts. The architecture separates hardware, device abstraction, streaming, DSP, analysis, persistence, UI, and CLI.

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -e ".[rtlsdr]"`
3. Install development tools: `pip install pytest ruff pyright build`

## Code Style

- Follow PEP 8
- Use explicit interfaces and small modules
- Include docstrings for public APIs
- Avoid giant files and classes
- Add type annotations (verified with pyright)

## Testing

To run tests without requiring physical hardware:

```bash
pytest -m "not hardware"
```

To run hardware-specific tests:

```bash
pytest -m hardware
```

## Pull Requests

1. Create a feature branch
2. Ensure tests pass
3. Ensure formatting and typing passes (`ruff check .`, `ruff format --check .`, `pyright`)
4. Submit your PR!
