# Ollama Integration Setup Guide

This guide explains how to set up and use Ollama as an alternative AI provider for Paddi's security analysis.

## 📋 Prerequisites

- Docker or native Ollama installation
- At least 8GB of RAM (recommended: 16GB)
- Sufficient disk space for models (5-10GB per model)

## 🚀 Installation

### Option 1: Docker (Recommended)

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Option 2: Native Installation

#### macOS
```bash
curl https://ollama.ai/install.sh | sh
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
Download and run the installer from [ollama.ai](https://ollama.ai/download)

## 📦 Model Setup

### Download Models

```bash
# General purpose model (recommended)
ollama pull llama3

# Code-focused model for better security analysis
ollama pull codellama

# Alternative models
ollama pull mistral
ollama pull mixtral
```

### Verify Installation

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test a model
ollama run llama3 "Hello, world!"
```

## ⚙️ Configuration

### Environment Variables

Create or update your `.env` file:

```bash
# Select Ollama as the AI provider
AI_PROVIDER=ollama

# Ollama configuration
OLLAMA_MODEL=llama3
OLLAMA_ENDPOINT=http://localhost:11434
```

### Available Models

| Model | Size | Best For | Memory Required |
|-------|------|----------|-----------------|
| llama3 | 8B | General analysis | 8GB |
| codellama | 7B | Code security | 8GB |
| mistral | 7B | Fast analysis | 8GB |
| mixtral | 47B | Detailed analysis | 32GB |

## 🎯 Usage

### Command Line

```bash
# Using environment variables
export AI_PROVIDER=ollama
python main.py audit

# Using command line arguments
python main.py audit --ai-provider=ollama --ollama-model=codellama

# Direct explainer usage
python app/explainer/agent_explainer.py \
  --ai-provider=ollama \
  --ollama-model=llama3 \
  --ollama-endpoint=http://localhost:11434
```

### Python API

```python
from app.explainer.agent_explainer import SecurityRiskExplainer

# Initialize with Ollama
explainer = SecurityRiskExplainer(
    ai_provider="ollama",
    ollama_model="codellama",
    ollama_endpoint="http://localhost:11434",
    use_mock=False
)

# Run analysis
findings = explainer.analyze()
```

## 🔧 Advanced Configuration

### Custom Endpoints

If running Ollama on a different host or port:

```bash
OLLAMA_ENDPOINT=http://192.168.1.100:11434
```

### GPU Acceleration

Ollama automatically uses GPU if available. To check:

```bash
ollama ps  # Shows running models and GPU usage
```

### Model Parameters

You can customize model behavior by modifying the `OllamaSecurityAnalyzer` class:

```python
# In app/explainer/ollama_explainer.py
"options": {
    "temperature": 0.2,      # Lower = more consistent
    "top_p": 0.8,           # Control creativity
    "num_predict": 2048,    # Max tokens
    "num_ctx": 4096,        # Context window
}
```

## 🐛 Troubleshooting

### Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check logs
docker logs ollama  # If using Docker
journalctl -u ollama  # If using systemd
```

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3
```

### Out of Memory

- Use smaller models (llama3 instead of mixtral)
- Increase system RAM
- Close other applications
- Adjust context window size

### Slow Performance

- Use GPU acceleration if available
- Choose smaller, faster models
- Reduce context window size
- Consider using `mistral` for faster responses

## 📊 Comparison: Gemini vs Ollama

| Feature | Gemini | Ollama |
|---------|--------|--------|
| Privacy | Data sent to Google | Fully local |
| Cost | API usage fees | Free (hardware costs only) |
| Internet | Required | Not required |
| Speed | Fast (API) | Depends on hardware |
| Accuracy | High | Good to Very Good |
| Models | Gemini 1.5 | Multiple options |

## 🔒 Security Considerations

1. **Data Privacy**: All analysis happens locally - no data leaves your machine
2. **Network Security**: Ollama API is exposed on localhost by default
3. **Resource Usage**: Monitor CPU/GPU usage during analysis
4. **Model Updates**: Regularly update models for better performance

## 📚 Additional Resources

- [Ollama Documentation](https://github.com/jmorganca/ollama)
- [Model Library](https://ollama.ai/library)
- [Performance Tuning Guide](https://github.com/jmorganca/ollama/blob/main/docs/performance.md)