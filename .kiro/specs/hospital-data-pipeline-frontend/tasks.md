# Implementation Plan: Hospital Data Pipeline Frontend

## Overview

This implementation plan creates a Streamlit-based frontend application with custom styling to achieve a professional, Vercel-inspired aesthetic. The application provides six main pages for pipeline execution, data viewing, and visualization display, all connected to a Backend API via REST endpoints.

## Tasks

- [x] 1. Set up project structure and configuration
  - Create frontend/ directory with subdirectories: styles/, api/, pages/, utils/
  - Create config.py with API_BASE_URL, REQUEST_TIMEOUT, CACHE_TTL, PAGE_NAMES
  - Create requirements.txt with streamlit, requests, pandas dependencies
  - Set up .gitignore for Python projects
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 2. Implement custom styling system
  - [x] 2.1 Create styles/custom_styles.py module
    - Define COLORS dictionary with Vercel-inspired color palette (primary, background, surface, text, border, error, success)
    - Define TYPOGRAPHY dictionary with font family, heading sizes, body sizes
    - Define SPACING dictionary with xs, s, m, l, xl values
    - Implement get_global_styles() function returning base CSS for typography, colors, spacing
    - Implement get_button_styles() function returning CSS for custom button styling
    - Implement get_table_styles() function returning CSS for dataframe styling
    - Implement get_card_styles() function returning CSS for card/container styling
    - Implement inject_styles(css_string) helper function using st.markdown() with unsafe_allow_html=True
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 3. Implement API client module
  - [x] 3.1 Create api/client.py with HospitalAPIClient class
    - Implement __init__(base_url) to initialize session and headers
    - Implement _make_request(endpoint, method) for internal HTTP request handling
    - Implement _handle_error(response) for internal error handling with network, HTTP, and JSON parsing errors
    - Implement run_pipeline() returning dict from GET /run-pipeline
    - Implement get_patient_master() returning pd.DataFrame from GET /patient-master
    - Implement get_anomalies() returning pd.DataFrame from GET /anomalies
    - Implement get_vitals() returning pd.DataFrame from GET /vitals
    - Implement get_labs() returning pd.DataFrame from GET /labs
    - Implement get_visualization(filename) returning bytes from GET /visualizations/{filename}
    - _Requirements: 1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 6.3, 6.4, 8.2, 9.1, 9.2_

- [x] 4. Implement utility functions
  - [x] 4.1 Create utils/helpers.py module
    - Implement format_timestamp(ts) for display formatting
    - Implement format_number(num, decimals) for number formatting
    - Implement validate_api_url(url) for URL validation
    - _Requirements: 8.4_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement main application entry point
  - [x] 6.1 Create app.py with main application logic
    - Implement configure_page() using st.set_page_config with wide layout, title "Hospital Data Pipeline", icon 🏥
    - Implement inject_global_styles() to apply custom CSS to entire application
    - Implement render_navigation() using st.sidebar.radio with all six page options
    - Implement route_to_page() to load selected page component
    - Initialize st.session_state with api_client, current_page, cached_data
    - Validate API connection on startup and display error if unreachable
    - _Requirements: 8.1, 8.4, 8.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 7. Implement Run Pipeline page
  - [x] 7.1 Create pages/run_pipeline.py module
    - Implement render() function with st.title("Run Pipeline")
    - Implement inject_page_styles() for page-specific styling
    - Create pipeline trigger button with custom styling
    - Implement button click handler to call api_client.run_pipeline()
    - Store pipeline_running and pipeline_logs in st.session_state
    - Display progress logs showing stages: Setup, Bronze, Silver, Gold, Visualization
    - Disable trigger button while pipeline is running
    - Display success message on completion or error message on failure
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 9.1, 9.2, 9.3, 9.4_

- [x] 8. Implement Patient Master page
  - [x] 8.1 Create pages/patient_master.py module
    - Implement render() function with st.title("Patient Master")
    - Implement fetch_data() using api_client.get_patient_master() with @st.cache_data
    - Display loading indicator with st.spinner while fetching data
    - Display data using st.dataframe() with custom CSS styling
    - Enable sorting and filtering on the dataframe
    - Display row count indicator
    - Handle errors with st.error() displaying user-friendly message
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 9.1, 9.2, 9.3_

- [x] 9. Implement Anomalies page
  - [x] 9.1 Create pages/anomalies.py module
    - Implement render() function with st.title("Anomalies")
    - Implement fetch_data() using api_client.get_anomalies() with @st.cache_data
    - Display loading indicator with st.spinner while fetching data
    - Display anomalies table using st.dataframe() with custom CSS
    - Add color-coded indicators for anomaly types (High Heart Rate - red, Low Oxygen - orange, High Blood Pressure - red)
    - Enable sorting and filtering by anomaly type
    - Display anomaly thresholds: HR > 120 bpm, OX < 92%, SYS > 160 OR DIA > 100 mmHg
    - Handle errors with st.error() displaying user-friendly message
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 9.1, 9.2, 9.3_

- [x] 10. Implement Vitals page
  - [x] 10.1 Create pages/vitals.py module
    - Implement render() function with st.title("Vitals")
    - Implement fetch_data() using api_client.get_vitals() with @st.cache_data
    - Display loading indicator with st.spinner while fetching data
    - Display vitals data using st.dataframe() with custom CSS styling
    - Enable sorting and filtering on the dataframe
    - Handle errors with st.error() displaying user-friendly message
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 9.1, 9.2, 9.3_

- [x] 11. Implement Labs page
  - [x] 11.1 Create pages/labs.py module
    - Implement render() function with st.title("Labs")
    - Implement fetch_data() using api_client.get_labs() with @st.cache_data
    - Display loading indicator with st.spinner while fetching data
    - Display labs data using st.dataframe() with custom CSS styling
    - Enable sorting and filtering on the dataframe
    - Handle errors with st.error() displaying user-friendly message
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 9.1, 9.2, 9.3_

- [x] 12. Implement Visualizations page
  - [x] 12.1 Create pages/visualizations.py module
    - Implement render() function with st.title("Visualizations")
    - Implement fetch_visualization(filename) helper using api_client.get_visualization()
    - Create three sections with custom card styling for each visualization
    - Fetch and display hr_trend.png with st.image() and caption "Heart Rate Trend - Multi-line plot showing heart rate over time for all patients"
    - Fetch and display oxygen_distribution.png with st.image() and caption "Oxygen Distribution - Histogram with 92% threshold line"
    - Fetch and display anomaly_counts.png with st.image() and caption "Anomaly Counts - Bar chart showing counts by anomaly type"
    - Display loading indicator for each visualization while fetching
    - Handle errors per visualization with st.error() for specific visualization failures
    - Use Streamlit columns for responsive grid layout
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 9.1, 9.2, 9.3_

- [x] 13. Final checkpoint and polish
  - [x] 13.1 Test all pages with Backend API
    - Verify Run Pipeline page triggers pipeline and displays logs correctly
    - Verify Patient Master page displays data table with sorting/filtering
    - Verify Anomalies page displays anomalies with color coding
    - Verify Vitals page displays vitals data table
    - Verify Labs page displays labs data table
    - Verify Visualizations page displays all three charts
    - Test error handling for network failures and API errors
    - Test loading states for all data fetching operations
    - _Requirements: 1.1-1.6, 2.1-2.7, 3.1-3.9, 4.1-4.6, 5.1-5.6, 6.1-6.9, 9.1-9.5_
  
  - [x] 13.2 Verify responsive design and styling
    - Test application on different screen sizes
    - Verify consistent typography and spacing across all pages
    - Verify navigation highlighting works correctly
    - Verify custom styling achieves professional, non-AI-generated appearance
    - _Requirements: 7.1-7.7, 10.1-10.5_

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks reference specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- The implementation uses Python with Streamlit framework as specified in the design
- Custom CSS is injected via st.markdown() with unsafe_allow_html=True for professional styling
- API client uses requests library with proper error handling for network and HTTP errors
- All data fetching uses @st.cache_data decorator to minimize redundant API calls
- Loading states use st.spinner() for user feedback during data fetching
- Error messages use st.error() for clear user communication
