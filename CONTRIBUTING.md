# Contributing to ZeroLag

Thank you for your interest in contributing to ZeroLag! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- Basic understanding of Python and GUI development

### Development Setup
1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/zerolag.git
   cd zerolag
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development dependencies
   ```

## 📋 How to Contribute

### Reporting Issues
- Use the GitHub issue tracker
- Provide detailed information about the problem
- Include system information (OS, Python version, etc.)
- Attach relevant logs or screenshots

### Suggesting Features
- Open a GitHub issue with the "enhancement" label
- Describe the feature and its benefits
- Consider the impact on performance and compatibility

### Code Contributions
1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

## 🏗️ Project Structure

```
zerolag/
├── src/                    # Source code
│   ├── core/              # Core input handling
│   ├── gui/               # PyQt5 interface
│   ├── profiles/          # Profile management
│   └── utils/             # Utilities and helpers
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/                # Configuration files
└── requirements.txt       # Dependencies
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/test_core.py
```

### Writing Tests
- Follow the AAA pattern (Arrange, Act, Assert)
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

## 📝 Code Style

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

### Example:
```python
def calculate_dpi_scaling(base_dpi: int, target_dpi: int) -> float:
    """
    Calculate the scaling factor for DPI adjustment.
    
    Args:
        base_dpi: The original DPI value
        target_dpi: The target DPI value
        
    Returns:
        The scaling factor as a float
        
    Raises:
        ValueError: If either DPI value is invalid
    """
    if base_dpi <= 0 or target_dpi <= 0:
        raise ValueError("DPI values must be positive")
    
    return target_dpi / base_dpi
```

## 🎯 Areas for Contribution

### High Priority
- Core input handling optimization
- Cross-platform compatibility
- Performance improvements
- Bug fixes

### Medium Priority
- GUI enhancements
- Profile management features
- Documentation improvements
- Test coverage

### Low Priority
- Code refactoring
- Performance monitoring
- Community features

## 🔍 Code Review Process

1. All code changes require review
2. At least one approval required
3. All CI checks must pass
4. Maintain test coverage
5. Update documentation as needed

## 🐛 Bug Reports

When reporting bugs, please include:
- OS and version
- Python version
- ZeroLag version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

## 💡 Feature Requests

When suggesting features:
- Describe the use case
- Explain the benefits
- Consider implementation complexity
- Think about performance impact

## 📚 Documentation

- Update README.md for major changes
- Add docstrings to new functions
- Update API documentation
- Include examples where helpful

## 🏷️ Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release notes
4. Tag the release
5. Build and test packages

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow the code of conduct

## 📞 Getting Help

- GitHub Discussions for questions
- Discord for real-time chat
- GitHub Issues for bugs and features

## 📄 License

By contributing to ZeroLag, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ZeroLag! 🎮
