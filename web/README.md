# Paddi Web Dashboard

An interactive web dashboard for the Paddi security audit tool, designed to run on Google Cloud Run.

## 🌟 Features

### Current Implementation
- **Security Dashboard**: Visual overview of security findings with severity distribution
- **Interactive Charts**: Chart.js visualizations for findings analysis
- **Findings Table**: Detailed view of all security issues
- **Dark Mode**: Toggle between light and dark themes
- **AI Chat Interface**: Mock interface for future Gemini integration
- **Export Options**: Foundation for PDF/Markdown/HTML export
- **Cloud Run Ready**: Dockerized and configured for deployment

### Architecture

```
web/
├── app.py                 # Flask application
├── templates/
│   └── dashboard.html     # Main dashboard UI
├── static/
│   ├── css/
│   │   └── dashboard.css  # Material Design 3 styles
│   └── js/
│       └── dashboard.js   # Dashboard functionality
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
├── service.yaml         # Cloud Run configuration
└── deploy.sh           # Deployment script
```

## 🚀 Quick Start

### Local Development

1. Install dependencies:
```bash
cd web
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the dashboard at `http://localhost:8080`

### Cloud Run Deployment

1. Set your GCP project:
```bash
export PROJECT_ID=your-gcp-project-id
```

2. Run the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: API key for Vertex AI Gemini
- `SECRET_KEY`: Flask secret key for sessions
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `PORT`: Server port (default: 8080)

### API Endpoints

- `GET /`: Main dashboard page
- `GET /api/health`: Health check endpoint
- `POST /api/audit/start`: Start a new audit
- `GET /api/audit/status/<audit_id>`: Get audit status
- `GET /api/findings`: Get all findings
- `GET /api/findings/severity-distribution`: Get severity chart data
- `GET /api/findings/timeline`: Get timeline chart data
- `POST /api/chat`: Chat with AI assistant
- `GET /api/export/<format>`: Export report

## 🎯 Future Enhancements

### Real-time Features
- WebSocket integration for live updates
- Server-sent events for audit progress
- Real-time finding notifications

### Authentication & Multi-tenancy
- Google OAuth integration
- Project selector for multiple GCP projects
- Role-based access control
- User audit history

### Advanced Features
- Scheduled automated audits
- Integration with Google Drive for reports
- Slack/Teams notifications
- PDF report generation
- Full Gemini AI integration

### Technical Improvements
- Add comprehensive error handling
- Implement caching for performance
- Add comprehensive logging
- Create unit and integration tests
- Add monitoring and metrics

## 🏗️ Development Notes

### Adding New Features

1. **New API Endpoint**: Add to `app.py`
2. **New UI Component**: Update `dashboard.html` and `dashboard.js`
3. **New Chart**: Add Chart.js configuration in `dashboard.js`
4. **New Style**: Update `dashboard.css` following Material Design 3

### Testing

Currently, the dashboard uses mock data for demonstration. To integrate with real data:

1. Update API endpoints in `app.py` to call actual agents
2. Ensure agents output data in expected format
3. Configure proper authentication and permissions

### Security Considerations

- Always use HTTPS in production
- Implement proper authentication before exposing sensitive data
- Validate all user inputs
- Use least-privilege service accounts
- Rotate secrets regularly

## 📝 License

This project is part of the Paddi security audit tool suite.