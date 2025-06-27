# Ollama Integration Setup

This guide explains how to set up and use Ollama as an alternative AI provider for Paddi's security analysis.

## Overview

Ollama allows you to run large language models locally, providing:
- **Privacy**: Your data never leaves your machine
- **Cost Savings**: No API usage fees
- **Offline Operation**: Works without internet connection
- **Customization**: Use custom fine-tuned models

## Prerequisites

1. **Ollama Installation**
   ```bash
   # macOS/Linux
   curl https://ollama.ai/install.sh | sh
   
   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Model Download**
   ```bash
   # Recommended models for security analysis
   ollama pull llama3        # General purpose, good balance
   ollama pull codellama     # Better for code analysis
   ollama pull mistral       # Fast and efficient
   ```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Select Ollama as the AI provider
AI_PROVIDER=ollama

# Ollama configuration
OLLAMA_MODEL=llama3
OLLAMA_ENDPOINT=http://localhost:11434

# Optional: Adjust generation parameters
AI_TEMPERATURE=0.2
AI_MAX_OUTPUT_TOKENS=2048
```

### Available Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | Choose between 'gemini' or 'ollama' | `gemini` |
| `OLLAMA_MODEL` | Model to use (e.g., llama3, codellama) | `llama3` |
| `OLLAMA_ENDPOINT` | Ollama server URL | `http://localhost:11434` |
| `AI_TEMPERATURE` | Model temperature (0-1) | `0.2` |
| `AI_MAX_OUTPUT_TOKENS` | Maximum response length | `2048` |

## Usage

### Starting Ollama Server

```bash
# Start Ollama server (if not already running)
ollama serve
```

### Running Analysis with Ollama

1. **Using Environment Variables**
   ```bash
   export AI_PROVIDER=ollama
   python main.py audit
   ```

2. **Using Command Line Arguments**
   ```bash
   python app/explainer/agent_explainer.py \
     --ai-provider=ollama \
     --ollama-model=llama3 \
     --use-mock=false
   ```

3. **Full Pipeline with Ollama**
   ```bash
   # Run complete audit with Ollama
   python main.py audit \
     --ai-provider=ollama \
     --ollama-model=codellama \
     --use-mock=false
   ```

## Model Selection Guide

### Recommended Models

1. **llama3** (8B parameters)
   - Best general-purpose model
   - Good balance of speed and quality
   - Suitable for most security analysis tasks

2. **codellama** (7B/13B parameters)
   - Optimized for code understanding
   - Better at analyzing IAM policies and configurations
   - Slightly slower but more accurate for technical content

3. **mistral** (7B parameters)
   - Fast and efficient
   - Good for quick analysis
   - Lower resource requirements

### Performance Considerations

- **RAM Requirements**: 8GB minimum, 16GB recommended
- **Processing Time**: Local models are generally slower than cloud APIs
- **GPU Acceleration**: Optional but significantly improves performance

## Troubleshooting

### Common Issues

1. **Connection Refused Error**
   ```
   Error: Cannot connect to Ollama server at http://localhost:11434
   ```
   **Solution**: Ensure Ollama is running with `ollama serve`

2. **Model Not Found**
   ```
   Error: Model 'llama3' not found
   ```
   **Solution**: Pull the model first with `ollama pull llama3`

3. **Timeout Errors**
   - Increase timeout in settings
   - Use a smaller model
   - Ensure adequate system resources

### Checking Ollama Status

```bash
# List available models
ollama list

# Check if server is running
curl http://localhost:11434/api/tags

# Test a model
ollama run llama3 "Hello, how are you?"
```

## Comparison: Ollama vs Gemini

| Feature | Ollama | Gemini |
|---------|--------|--------|
| **Cost** | Free (local compute) | API usage fees |
| **Privacy** | Data stays local | Data sent to Google |
| **Internet** | Not required | Required |
| **Speed** | Slower (depends on hardware) | Fast |
| **Accuracy** | Good (model dependent) | Excellent |
| **Setup** | Requires installation | API key only |

## Advanced Configuration

### Custom Ollama Endpoint

If running Ollama on a different machine:

```bash
# Remote Ollama server
export OLLAMA_ENDPOINT=http://192.168.1.100:11434
```

### Model Parameters

Fine-tune generation for better results:

```python
# In your Python code
analyzer = OllamaSecurityAnalyzer(
    model="llama3",
    temperature=0.1,      # Lower = more focused
    max_output_tokens=4096  # Longer responses
)
```

## Security Considerations

1. **Local Processing**: All data remains on your machine
2. **Network Isolation**: Can run completely offline
3. **Model Security**: Download models only from official Ollama registry
4. **Resource Usage**: Monitor CPU/RAM usage during analysis

## Next Steps

- Try different models to find the best fit for your use case
- Consider fine-tuning a model on security-specific data
- Set up Ollama on a dedicated analysis server for team use