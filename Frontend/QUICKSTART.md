# Quick Start Guide

Get the Hospital Data Pipeline Frontend up and running in 3 simple steps.

## Prerequisites

- Python 3.8 or higher
- Backend API running (default: `http://localhost:8000`)

## Step 1: Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

## Step 2: Configure API Endpoint (Optional)

If your backend is not running on `http://localhost:8000`, set the environment variable:

```bash
# Linux/Mac
export API_BASE_URL=http://your-backend-url:port

# Windows (Command Prompt)
set API_BASE_URL=http://your-backend-url:port

# Windows (PowerShell)
$env:API_BASE_URL="http://your-backend-url:port"
```

## Step 3: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## What's Next?

1. **Run Pipeline** - Click "Run Pipeline" in the sidebar to process data
2. **View Data** - Navigate to Patient Master, Vitals, Labs, or Anomalies
3. **See Visualizations** - Check out the charts in the Visualizations page

## Troubleshooting

**Can't connect to API?**
- Make sure your backend is running
- Check the API_BASE_URL is correct
- Look for error messages in the Streamlit interface

**No data showing?**
- Run the pipeline first from the "Run Pipeline" page
- Ensure your backend has data in the `/data` directory

**Visualizations not loading?**
- Run the pipeline to generate visualization files
- Check that PNG files exist in the backend's output directory

## Need Help?

Check the full [README.md](README.md) for detailed documentation.
