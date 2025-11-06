# Contributing to NexusForge 2.0

Thank you for your interest in contributing! This document provides guidelines for contributing to NexusForge.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Keep discussions professional

## How to Contribute

### Reporting Bugs

1. Check if the bug is already reported in Issues
2. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Logs if available

### Suggesting Features

1. Check if feature is already requested
2. Create a new issue with:
   - Use case description
   - Proposed solution
   - Alternative solutions considered
   - Impact on existing functionality

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/NexusForge-2.0-.git
cd NexusForge-2.0-

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run examples
PYTHONPATH=. python examples/basic_usage.py
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for public APIs
- Keep functions focused and small
- Use meaningful variable names

### Example

```python
async def process_goal(self, goal: str) -> Dict[str, Any]:
    """
    Process a goal by breaking it down and spawning children if needed
    
    Args:
        goal: High-level goal to achieve
        
    Returns:
        Dictionary containing subtasks and spawned children
    """
    # Implementation
    pass
```

## Testing

- Write unit tests for new functionality
- Ensure existing tests pass
- Aim for high code coverage
- Test edge cases

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_core.py

# With coverage
pytest --cov=nexusforge tests/
```

## Documentation

- Update README for major changes
- Add docstrings to new functions/classes
- Update architecture docs if needed
- Include examples for new features

## Project Structure

```
NexusForge-2.0-/
├── nexusforge/          # Main package
│   ├── core/           # Core systems
│   ├── agents/         # Agent systems
│   ├── communication/  # Communication hub
│   ├── gui/           # Web dashboard
│   └── utils/         # Utilities
├── tests/             # Test suite
├── examples/          # Usage examples
├── docs/             # Documentation
└── README.md         # Main documentation
```

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add multi-threading support for agents
fix: Resolve memory leak in message queue
docs: Update API reference
test: Add tests for crew management
refactor: Simplify goal decomposition logic
```

## Areas for Contribution

### High Priority

- LLM integration for enhanced reasoning
- Distributed agent deployment
- Advanced visualization tools
- Performance optimizations
- Security enhancements

### Medium Priority

- Plugin system
- Additional expert modalities
- Enhanced CLI features
- More examples
- Internationalization

### Good First Issues

- Documentation improvements
- Additional test coverage
- Bug fixes
- Code cleanup
- Example applications

## Review Process

1. Maintainers review PRs within 3-5 days
2. Address review comments
3. Ensure CI passes
4. Squash commits if requested
5. Merge when approved

## Questions?

- Open a Discussion on GitHub
- Check existing documentation
- Ask in Pull Request comments

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:
- README.md
- Release notes
- GitHub contributors page

Thank you for making NexusForge better!
