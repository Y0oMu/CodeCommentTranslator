# CodeCommentTranslator 🌐💬

## Overview

CodeCommentTranslator is an open-source Python tool designed to simplify multilingual code documentation. It automatically detects and translates comments across various programming languages, making code more accessible to international developers.

## 🌟 Features

- **Multi-Language Support**: Detects and translates comments in `.py`, `.c`, `.cpp`, and other common source code files
- **Flexible Translation**: Supports multiple translation backends (currently OpenAI, with plans to expand)
- **Interactive CLI**: User-friendly command-line interface for easy file/folder translation
- **Extensible Design**: Modular architecture allows easy addition of new translation providers

## 🛠 Installation

### Prerequisites
- Python 3.8+
- OpenAI API Key (for current implementation)

### Install Dependencies
```bash
git clone https://github.com/Y0oMu/CodeCommentTranslator.git
cd CodeCommentTranslator
pip install -r requirements.txt
```

## 🚀 Usage

### Basic Usage
```bash
python main.py --target="path/to/file_or_folder"
```

### Workflow
1. The tool scans the specified path for code files
2. Displays files with comments (10 at a time)
3. Allows interactive selection and preview of comments
4. Translates selected comments using the configured translation backend

### Example Interaction
```
> python main.py --target="./my_project"
Found 15 files with comments
Showing first 10 files:
[1] src/main.py
[2] utils/helper.cpp
...

Enter 'next' for more files, 'show [id]' to view comments, 'y' to confirm translation
```

## 🔧 Configuration

Configure translation settings in `config.yaml`:
- Select translation provider
- Set target language
- Configure API credentials

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Current Roadmap
- [ ] Add support for more translation backends
- [ ] Improve language detection
- [ ] Add more programming language support
- [ ] Create configuration wizard

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing powerful translation capabilities
- The open-source community for continuous inspiration

---

**Note**: This project is under active development. Feedback and contributions are highly appreciated! 🚀
