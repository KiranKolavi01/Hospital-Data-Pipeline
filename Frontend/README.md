# Hospital Data Pipeline Frontend

A production-ready Streamlit web application for visualizing and managing hospital data pipeline operations.

## Features

- **Run Pipeline** - Trigger data pipeline execution and monitor progress
- **Patient Master** - View consolidated patient data with latest vitals and labs
- **Anomalies** - Monitor detected health anomalies with color-coded indicators
- **Vitals** - Browse cleaned patient vital signs data
- **Labs** - Explore laboratory test results
- **Visualizations** - View healthcare metrics and trends

## Tech Stack

- **Python 3.8+**
- **Streamlit** - Web application framework
- **Pandas** - Data manipulation
- **Requests** - HTTP client for API communication
- **Custom HTML/CSS** - Vercel-inspired UI polish

## Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application can be configured using environment variables:

- `API_BASE_URL` - Backend API base URL (default: `http://localhost:8000`)
- `REQUEST_TIMEOUT` - HTTP request timeout in seconds (default: `30`)
- `CACHE_TTL` - Cache time-to-live in seconds (default: `300`)

### Example:

```bash
export API_BASE_URL=http://localhost:8000
export REQUEST_TIMEOUT=60
export CACHE_TTL=600
```

## Usage

1. **Ensure the backend API is running** at the configured URL

2. **Start the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

3. **Open your browser** to `http://localhost:8501`

4. **Navigate** using the sidebar menu to access different features

## Project Structure

```
frontend/
├── app.py                    # Main application entry point
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── api/
│   ├── __init__.py
│   └── client.py            # Backend API client
├── pages/
│   ├── __init__.py
│   ├── run_pipeline.py      # Pipeline execution page
│   ├── patient_master.py    # Patient master view
│   ├── anomalies.py         # Anomalies view
│   ├── vitals.py            # Vitals data view
│   ├── labs.py              # Labs data view
│   └── visualizations.py    # Visualizations view
├── styles/
│   ├── __init__.py
│   └── custom_styles.py     # Custom CSS styling
└── utils/
    ├── __init__.py
    └── helpers.py           # Utility functions
```

## Design Philosophy

The UI is inspired by Vercel's design aesthetic:

- **Clean & Minimal** - Generous whitespace and clear hierarchy
- **Professional Typography** - Consistent font system with proper sizing
- **Subtle Interactions** - Smooth transitions and hover states
- **Muted Color Palette** - Professional colors with strategic accents
- **Responsive Design** - Adapts to different screen sizes

## API Endpoints

The frontend expects the following backend API endpoints:

- `GET /run-pipeline` - Trigger pipeline execution
- `GET /patient-master` - Fetch patient master data
- `GET /anomalies` - Fetch anomaly data
- `GET /vitals` - Fetch vitals data
- `GET /labs` - Fetch labs data
- `GET /visualizations/{filename}` - Fetch visualization images

## Troubleshooting

### Cannot connect to API

- Verify the backend server is running
- Check the `API_BASE_URL` configuration
- Ensure there are no firewall or network issues

### Visualizations not loading

- Run the pipeline first to generate visualizations
- Check that the backend has generated the PNG files
- Verify the `/visualizations` endpoint is accessible

### Data not updating

- Clear the cache by refreshing the page (Ctrl+R or Cmd+R)
- Check the `CACHE_TTL` setting if data seems stale
- Verify the backend is returning updated data

## Development

### Adding a new page

1. Create a new file in `pages/` directory
2. Implement a `render()` function
3. Import and add to `page_map` in `app.py`
4. Add page name to `PAGE_NAMES` in `config.py`

### Customizing styles

Edit `styles/custom_styles.py` to modify:
- Color palette (`COLORS`)
- Typography (`TYPOGRAPHY`)
- Spacing (`SPACING`)
- Component styles (buttons, tables, cards)

## License

This project is part of the Hospital Data Pipeline system.
