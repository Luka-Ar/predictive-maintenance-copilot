# Contributing to Predictive Maintenance Copilot

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## Project Status

This is a **Phase 2 product-grade open-source release** focused on hybrid AI for predictive maintenance (ML + RAG + local LLM). Contributions are welcome, but please note:

- The project is not intended for production use in safety-critical systems
- Core prediction logic should remain stable unless changes are well-justified
- Focus on reliability, documentation, and maintainability

## How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or suggest improvements
- Provide clear descriptions and steps to reproduce
- Include your environment (Python version, OS, etc.)

### Code Contributions
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test your changes locally
5. Commit with clear messages: `git commit -m "Add feature: description"`
6. Push to your fork and create a Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Keep code simple and readable
- Add comments for complex logic
- Remove debug statements before submitting
- Test your changes thoroughly

### Areas for Contribution

- **Documentation** - Improve README, add examples, clarify setup
- **UI/UX** - Enhance the Next.js frontend styling and experience
- **Error Handling** - Improve error messages and recovery
- **Testing** - Add unit tests and integration tests
- **Performance** - Optimize ML model inference and API responses
- **Accessibility** - Improve frontend accessibility features

## Development Setup

```bash
# Backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd web
npm install

# Testing
python -m pytest  # when tests are added
```

## Pull Request Process

1. Update documentation if needed
2. Add your changes with clear commit messages
3. Ensure code works locally
4. Create PR with description of changes
5. Respond to review comments

## Questions?

Feel free to open an issue for questions or discussions about the project.

---

**Thank you for contributing!**
