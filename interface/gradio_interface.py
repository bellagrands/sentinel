import gradio as gr
import requests
import json # For pretty printing JSON responses
import pandas as pd # For DataFrame display

# Configuration
API_BASE_URL = "http://api:5000" # Assuming the API service is named 'api' in docker-compose

# --- API Interaction Functions (Stats, Alerts, Data Sources, Scrapers - condensed) ---
# (Assuming previous API functions for stats, alerts, data_sources, scrapers are here and correct)
def get_stats_raw(): # Renamed to avoid conflict, returns dict
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        response.raise_for_status()
        return response.json() # Return raw dict for processing by plot functions
    except Exception as e:
        print(f"Error in get_stats_raw: {e}") # Log error
        return {} # Return empty dict on error to prevent downstream issues

def get_stats_display(): # For the textbox display
    raw_stats = get_stats_raw()
    return json.dumps(raw_stats, indent=2) if raw_stats else "Error loading stats or no stats available."

# ... (other existing API functions: get_file_alerts, get_db_alerts, acknowledge_alert_api,
# fetch_data_sources_api, handle_add_update_data_source_api, handle_delete_data_source_api,
# fetch_available_scrapers_api, run_scraper_api, fetch_scraper_status_api are assumed to be here)
def get_file_alerts():
    try:
        response = requests.get(f"{API_BASE_URL}/alerts")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e: return f"Error: {e}"

def get_db_alerts():
    try:
        response = requests.get(f"{API_BASE_URL}/alerts/db")
        response.raise_for_status()
        alerts = response.json()
        return "\n\n".join([json.dumps(alert, indent=2) for alert in alerts]) if alerts else "No alerts found in DB."
    except Exception as e: return f"Error: {e}"

def acknowledge_alert_api(alert_id: str, alert_source: str):
    if not alert_id: return "Please enter an Alert ID.", ""
    refresh_fn = get_db_alerts if alert_source == "Database Alerts" else get_file_alerts
    try:
        response = requests.post(f"{API_BASE_URL}/alerts/{alert_id}/acknowledge")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2), refresh_fn()
    except Exception as e: return f"Error acknowledging: {e}", refresh_fn()

def fetch_data_sources_api():
    try:
        response = requests.get(f"{API_BASE_URL}/sources/")
        response.raise_for_status()
        sources_dict = response.json()
        sources_list = []
        for source_id, data in sources_dict.items(): # Iterate through dict
            item = {"id": source_id, "name": data.get("name"), "status": data.get("status"),
                    "update_frequency_str": data.get("update_frequency"),
                    "config_update_frequency_hrs": data.get("config", {}).get("update_frequency"),
                    "config_max_days_back": data.get("config", {}).get("max_days_back"),
                    "config_document_types": ", ".join(data.get("config", {}).get("document_types", [])),
                    "config_rate_limit": data.get("config", {}).get("rate_limit"),
                    "config_custom_fields": json.dumps(data.get("config", {}).get("custom_fields", {}))
                   }
            sources_list.append(item)
        return pd.DataFrame(sources_list) if sources_list else pd.DataFrame(), "Sources loaded."
    except Exception as e: return pd.DataFrame(), f"Error fetching sources: {e}"


def handle_add_update_data_source_api(sid, name, freq, mdb, dts, rl, cf):
    if not all([sid, name]): return "ID and Name required.", fetch_data_sources_api()[0]
    try:
        doc_types = [dt.strip() for dt in dts.split(',') if dt.strip()]
        custom_fields = json.loads(cf) if cf else {}
        payload = {"name": name, "config": {"update_frequency": int(freq), "max_days_back": int(mdb),
                                             "document_types": doc_types, "rate_limit": int(rl), "custom_fields": custom_fields}}
        response = requests.post(f"{API_BASE_URL}/sources/{sid}", json=payload)
        response.raise_for_status()
        msg = f"Source '{sid}' processed: {json.dumps(response.json(), indent=2)}"
    except Exception as e: msg = f"Error for '{sid}': {e}"
    df, _ = fetch_data_sources_api()
    return msg, df

def handle_delete_data_source_api(source_id: str):
    if not source_id: return "Source ID required.", fetch_data_sources_api()[0]
    try:
        response = requests.delete(f"{API_BASE_URL}/sources/{source_id}")
        response.raise_for_status()
        msg = response.json().get("message", f"Source '{source_id}' deleted.")
    except Exception as e: msg = f"Error deleting '{source_id}': {e}"
    df, _ = fetch_data_sources_api()
    return msg, df

def fetch_available_scrapers_api():
    try:
        response = requests.get(f"{API_BASE_URL}/scrapers/")
        response.raise_for_status()
        scrapers = response.json()
        scraper_names = [s["name"] for s in scrapers]
        return gr.Dropdown.update(choices=scraper_names if scraper_names else ["No scrapers available"]), "Scrapers list loaded."
    except Exception as e: return gr.Dropdown.update(choices=[]), f"Error fetching scrapers: {e}"

def run_scraper_api(scraper_name: str, search_terms_str: str, days_back: int):
    if not scraper_name: return "Please select a scraper to run."
    params = {}
    if search_terms_str: params["search_terms"] = [term.strip() for term in search_terms_str.split(',') if term.strip()]
    if days_back > 0: params["days_back"] = int(days_back)
    try:
        response = requests.post(f"{API_BASE_URL}/scrapers/{scraper_name}/run", json=params if params else None)
        response.raise_for_status()
        return f"Scraper '{scraper_name}' run initiated: {json.dumps(response.json(), indent=2)}"
    except Exception as e: return f"Error running scraper '{scraper_name}': {e}"

def fetch_scraper_status_api(scraper_name: str):
    if not scraper_name: return "Please select a scraper to check its status."
    try:
        response = requests.get(f"{API_BASE_URL}/scrapers/{scraper_name}/status")
        response.raise_for_status()
        return f"Status for '{scraper_name}': {json.dumps(response.json(), indent=2)}"
    except Exception as e: return f"Error fetching status for '{scraper_name}': {e}"

# --- Analysis API Function ---
def analyze_document_text_api(text_to_analyze: str):
    if not text_to_analyze.strip():
        return "Text input cannot be empty.", None, None, None, None

    try:
        response = requests.post(f"{API_BASE_URL}/v1/analyze_document", json={"text": text_to_analyze})
        response.raise_for_status()
        analysis_results = response.json()

        threat_score_val = analysis_results.get("threat_score", 0.0)
        categories_val = analysis_results.get("categories", [])
        # For entities, expect list of dicts, convert to DataFrame
        entities_list = analysis_results.get("entities", [])
        entities_df = pd.DataFrame(entities_list) if entities_list else pd.DataFrame(columns=['name', 'type'])
        summary_val = analysis_results.get("summary", "No summary provided.")

        return f"Analysis complete. Summary: {summary_val}", \
               threat_score_val, \
               gr.CheckboxGroup.update(choices=categories_val, value=categories_val), \
               entities_df, \
               summary_val # Also return summary for a dedicated field if needed

    except requests.exceptions.HTTPError as e:
        err_msg = f"Analysis API error ({e.response.status_code}): {e.response.json().get('detail', e.response.text) if e.response else str(e)}"
        return err_msg, 0.0, gr.CheckboxGroup.update(choices=[], value=[]), pd.DataFrame(), "Error in analysis."
    except Exception as e:
        return f"Error during analysis: {e}", 0.0, gr.CheckboxGroup.update(choices=[], value=[]), pd.DataFrame(), "Error in analysis."

# --- Helper functions for Dashboard Visualizations ---
def prepare_threat_distribution_plot(stats_data: dict):
    if not stats_data or "threat_distribution" not in stats_data:
        return gr.BarPlot.update(value=None) # Clear or hide plot

    # Assuming threat_distribution is a list/array of counts for score ranges
    # e.g., [count_0.0-0.2, count_0.2-0.4, ..., count_0.8-1.0]
    distribution = stats_data["threat_distribution"]
    score_ranges = ["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]

    # BarPlot expects a list of lists or Pandas DataFrame
    # [[val1_series1, val1_series2], [val2_series1, val2_series2]]
    # Or DataFrame with x, y columns. Let's use DataFrame.
    if len(distribution) == len(score_ranges):
        df = pd.DataFrame({
            "Score Range": score_ranges,
            "Count": distribution
        })
        return gr.BarPlot.update(value=df, x="Score Range", y="Count", title="Threat Score Distribution", height=300, width=500)
    return gr.BarPlot.update(value=None)


def prepare_top_categories_plot(stats_data: dict):
    if not stats_data or "top_categories" not in stats_data:
        return gr.BarPlot.update(value=None)

    top_categories = stats_data["top_categories"] # Expected: list of {'category': name, 'score': count}
    if not top_categories:
        return gr.BarPlot.update(value=None)

    df = pd.DataFrame(top_categories)
    # Rename 'score' to 'count' if it represents counts for BarPlot
    if 'score' in df.columns and 'count' not in df.columns: # Assuming 'score' here means count
        df = df.rename(columns={'score': 'Count'})
    if 'category' not in df.columns or 'Count' not in df.columns: # Check if essential columns are present
        return gr.BarPlot.update(value=None) # Cannot plot

    return gr.BarPlot.update(value=df, x="category", y="Count", title="Top Threat Categories", height=300, width=500)

def prepare_threat_timeline_plot(stats_data: dict):
    if not stats_data or "threat_timeline" not in stats_data:
        return gr.LinePlot.update(value=None)

    timeline_data = stats_data["threat_timeline"] # Expected: list of {'date': 'YYYY-MM-DD', 'avg_score': float}
    if not timeline_data:
        return gr.LinePlot.update(value=None)

    df = pd.DataFrame(timeline_data)
    if 'date' not in df.columns or 'avg_score' not in df.columns:
        return gr.LinePlot.update(value=None)

    return gr.LinePlot.update(value=df, x="date", y="avg_score", title="Threat Score Over Time", height=300, width=500,
                              tooltip=['date', 'avg_score'], x_label_angle=45)


def update_dashboard_visualizations():
    stats_data = get_stats_raw() # Fetch the raw stats data
    # This will return multiple plot updates
    return prepare_threat_distribution_plot(stats_data), \
           prepare_top_categories_plot(stats_data), \
           prepare_threat_timeline_plot(stats_data), \
           json.dumps(stats_data, indent=2) if stats_data else "Error loading stats or no stats available."


# --- Gradio Interface Definition ---
def main_interface():
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        with gr.Tabs():
            with gr.TabItem("Dashboard"):
                with gr.Column():
                    gr.Markdown("## Overall System Status & Key Metrics")
                    refresh_stats_button = gr.Button("Refresh Dashboard")
                    stats_display_json = gr.Textbox(label="System Statistics (JSON)", lines=10, interactive=False)

                    with gr.Row():
                        threat_dist_plot = gr.BarPlot(label="Threat Distribution")
                        top_cat_plot = gr.BarPlot(label="Top Categories")
                    threat_time_plot = gr.LinePlot(label="Threat Timeline")

                    # Initial load and refresh button click
                    app.load(update_dashboard_visualizations, outputs=[threat_dist_plot, top_cat_plot, threat_time_plot, stats_display_json])
                    refresh_stats_button.click(update_dashboard_visualizations, outputs=[threat_dist_plot, top_cat_plot, threat_time_plot, stats_display_json])

            with gr.TabItem("Alerts"):
                # (Alerts tab - condensed but functional)
                with gr.Column():
                    gr.Markdown("## System Alerts")
                    alert_type_radio = gr.Radio(choices=["File-based Alerts", "Database Alerts"], label="Select Alert Source", value="File-based Alerts")
                    alerts_display = gr.Textbox(label="Current Alerts", lines=10, interactive=False)
                    gr.Markdown("### Acknowledge Alert")
                    alert_id_input = gr.Textbox(label="Enter Alert ID")
                    acknowledge_button = gr.Button("Acknowledge Alert")
                    ack_status_message = gr.Textbox(label="Acknowledgement Status", interactive=False)
                    def update_alerts_display_wrapper(val): return get_file_alerts() if val == "File-based Alerts" else get_db_alerts()
                    alert_type_radio.change(update_alerts_display_wrapper, inputs=alert_type_radio, outputs=alerts_display)
                    acknowledge_button.click(acknowledge_alert_api, inputs=[alert_id_input, alert_type_radio], outputs=[ack_status_message, alerts_display])
                    app.load(lambda val: update_alerts_display_wrapper(val), inputs=alert_type_radio, outputs=alerts_display)

            with gr.TabItem("Data Sources"):
                # (Data Sources tab - condensed but functional)
                with gr.Column():
                    gr.Markdown("## Data Source Management")
                    ds_status_message = gr.Textbox(label="Status", interactive=False)
                    refresh_ds_button = gr.Button("Refresh List")
                    ds_dataframe = gr.DataFrame(headers=["id", "name", "status", "update_frequency_str", "config_update_frequency_hrs",
                                                        "config_max_days_back", "config_document_types", "config_rate_limit", "config_custom_fields"],
                                                interactive=False, row_count=(0,'dynamic'))
                    with gr.Accordion("Add/Update Source", open=False):
                        ds_id_input = gr.Textbox(label="ID"); ds_name_input = gr.Textbox(label="Name")
                        ds_freq = gr.Number(label="Update Freq (hrs)", value=24)
                        ds_mdb = gr.Number(label="Max Days Back", value=30)
                        ds_dts = gr.Textbox(label="Doc Types (comma-sep)", value="pdf,txt")
                        ds_rl = gr.Number(label="Rate Limit (reqs/min)", value=60)
                        ds_cf = gr.Textbox(label="Custom Fields (JSON)", value="{}")
                        add_ds_btn = gr.Button("Add/Update"); del_ds_btn = gr.Button("Delete")
                    app.load(fetch_data_sources_api, outputs=[ds_dataframe, ds_status_message])
                    refresh_ds_button.click(fetch_data_sources_api, outputs=[ds_dataframe, ds_status_message])
                    add_ds_btn.click(handle_add_update_data_source_api, inputs=[ds_id_input, ds_name_input, ds_freq, ds_mdb, ds_dts, ds_rl, ds_cf], outputs=[ds_status_message, ds_dataframe])
                    del_ds_btn.click(handle_delete_data_source_api, inputs=[ds_id_input], outputs=[ds_status_message, ds_dataframe])

            with gr.TabItem("Scrapers"):
                # (Scrapers tab - condensed but functional)
                with gr.Column():
                    gr.Markdown("## Scraper Control Center")
                    scraper_op_status = gr.Textbox(label="Op Status", interactive=False)
                    refresh_scrapers_btn = gr.Button("Refresh List")
                    scraper_select_dd = gr.Dropdown(label="Scrapers")
                    with gr.Accordion("Parameters", open=False):
                        scraper_terms = gr.Textbox(label="Search Terms (comma-sep)")
                        scraper_days = gr.Number(label="Days Back", value=0)
                    run_scraper_btn = gr.Button("Run"); status_scraper_btn = gr.Button("Check Status")
                    scraper_output_display = gr.Textbox(label="Output", lines=5, interactive=False)
                    app.load(fetch_available_scrapers_api, outputs=[scraper_select_dd, scraper_op_status])
                    refresh_scrapers_btn.click(fetch_available_scrapers_api, outputs=[scraper_select_dd, scraper_op_status])
                    run_scraper_btn.click(run_scraper_api, inputs=[scraper_select_dd, scraper_terms, scraper_days], outputs=scraper_output_display)
                    status_scraper_btn.click(fetch_scraper_status_api, inputs=[scraper_select_dd], outputs=scraper_output_display)

            with gr.TabItem("Analysis"):
                with gr.Column():
                    gr.Markdown("## Document Analysis")
                    analysis_status_msg = gr.Textbox(label="Analysis Status", interactive=False)
                    doc_text_input = gr.Textbox(label="Enter Document Text for Analysis", lines=10, placeholder="Paste text here...")
                    # url_input = gr.Textbox(label="Or Enter URL to Fetch and Analyze (Not Implemented)", placeholder="http://example.com/document.pdf")
                    analyze_doc_button = gr.Button("Analyze Document Text")

                    gr.Markdown("### Analysis Results")
                    threat_score_display = gr.Slider(label="Threat Score", minimum=0.0, maximum=1.0, step=0.01, interactive=False)
                    summary_display = gr.Textbox(label="Summary", lines=3, interactive=False)
                    categories_display = gr.CheckboxGroup(label="Detected Categories", interactive=False)
                    entities_display = gr.DataFrame(label="Detected Entities", headers=["name", "type"], interactive=False)

                    analyze_doc_button.click(
                        analyze_document_text_api,
                        inputs=[doc_text_input],
                        outputs=[analysis_status_msg, threat_score_display, categories_display, entities_display, summary_display]
                    )

    return app

if __name__ == "__main__":
    iface = main_interface()
    iface.launch(server_name="0.0.0.0")
