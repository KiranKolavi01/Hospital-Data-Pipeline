"""
Run Pipeline Page - Trigger and monitor data pipeline execution.
"""
import streamlit as st
from styles.custom_styles import inject_styles


def inject_page_styles():
    """Apply page-specific styles."""
    styles = """
    <style>
        .pipeline-stage {
            padding: 16px 20px;
            margin: 12px 0;
            border-radius: 12px;
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-left: 6px solid #34ACED;
            font-size: 14px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
        }
        
        .pipeline-stage.completed {
            background-color: #ECFDF5;
            border-left-color: #10B981;
        }
        
        .pipeline-stage.failed {
            background-color: #FEF2F2;
            border-left-color: #EF4444;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 12px;
            background: #F3F4F6;
            font-size: 11px;
            font-weight: 600;
            color: #374151;
        }
        
        .status-dot {
            height: 6px;
            width: 6px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        
        .dot-success { background-color: #10B981; }
        .dot-failed { background-color: #EF4444; }
        
        .stage-name {
            font-weight: 700;
            color: #111827;
        }
        
        .stage-status {
            color: #6B7280;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
    </style>
    """
    inject_styles(styles)


def render_pipeline_logs():
    """Display pipeline execution logs."""
    if st.session_state.pipeline_logs:
        st.markdown("### Pipeline Execution Log")
        
        for log in st.session_state.pipeline_logs:
            stage_name = log.get('name', 'Unknown')
            status = log.get('status', 'unknown')
            message = log.get('message', '')
            timestamp = log.get('timestamp', '')
            
            status_class = 'completed' if status == 'completed' else 'failed'
            dot_class = 'dot-success' if status == 'completed' else 'dot-failed'
            
            st.markdown(
                f"""
                <div class="log-entry">
                    <span class="status-badge {status_class}">
                        <span class="status-dot {dot_class}"></span>{status.upper()}
                    </span>
                    <span style="color: #6B7280; font-size: 11px;">{timestamp}</span>
                    <p style="margin: 4px 0 0 0; font-size: 13px;">{message}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No logs available yet. Run the pipeline to see progress.")


def run_pipeline_handler():
    """Handle pipeline execution button click."""
    api_client = st.session_state.api_client
    
    # Set pipeline running state
    st.session_state.pipeline_running = True
    st.session_state.pipeline_logs = []
    
    try:
        with st.spinner("Running pipeline..."):
            result = api_client.run_pipeline()
        
        # Parse result
        status = result.get('status', 'unknown')
        message = result.get('message', '')
        stages = result.get('stages', [])
        
        # Store logs in session state
        st.session_state.pipeline_logs = stages
        
        # Display result
        if status == 'success':
            st.success(f"Pipeline completed successfully! {message}")
        else:
            st.error(f"Pipeline failed: {message}")
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
    
    except TimeoutError as e:
        st.error(f"Timeout Error: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        # Reset pipeline running state
        st.session_state.pipeline_running = False


def render():
    """Main render function for Run Pipeline page."""
    inject_page_styles()
    
    st.title("Run Pipeline")
    st.markdown(
        "Trigger the Hospital Data Pipeline to process raw data through "
        "Bronze → Silver → Gold layers and generate visualizations."
    )
    
    st.divider()
    
    # Pipeline trigger section
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Trigger button
        button_disabled = st.session_state.pipeline_running
        
        if st.button(
            "Run Pipeline",
            disabled=button_disabled,
            use_container_width=True,
            type="primary"
        ):
            run_pipeline_handler()
    
    with col2:
        if st.session_state.pipeline_running:
            st.info("Pipeline is currently running...")
        else:
            st.markdown(
                "<p style='color: #666; font-size: 14px; margin-top: 8px;'>"
                "Click the button to start processing hospital data"
                "</p>",
                unsafe_allow_html=True
            )
    
    st.divider()
    
    # Display pipeline logs
    render_pipeline_logs()
    
    # Pipeline stages info
    if not st.session_state.pipeline_logs:
        st.markdown("### Pipeline Stages")
        st.markdown(
            """
            The pipeline processes data through the following stages:
            
            1. **Setup** - Create required folders and initialize environment
            2. **Bronze** - Ingest raw data from source files
            3. **Silver** - Clean and standardize data, create patient master
            4. **Gold** - Detect anomalies based on health thresholds
            5. **Visualization** - Generate charts and plots
            """
        )
