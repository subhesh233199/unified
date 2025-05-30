def run_fallback_visualization(metrics: Dict, metric_names: List[str] = None):
    viz_folder = "visualizations"
    os.makedirs(viz_folder, exist_ok=True)
    _, _, visualization_crew = setup_crew()
    visualization_task = visualization_crew.tasks[0]
    
    # If no specific metrics provided, regenerate all
    target_metrics = metric_names if metric_names else metrics['metrics'].keys()
    
    for metric_name in target_metrics:
        if metric_name not in metrics['metrics']:
            logger.warning(f"Metric {metric_name} not found, skipping visualization")
            continue
        try:
            # Update visualization task description to focus on specific metric
            visualization_task.description = (
                f"Generate visualization instructions for the following metric:\n"
                f"Metric: {metric_name}\nData: {json.dumps(metrics['metrics'][metric_name])}\n"
                f"Save the visualization as {metric_name.lower().replace(' ', '_')}.png"
            )
            visualization_crew.kickoff()
            # Assume visualization.py (called by the agent) saves the image to viz_folder
            logger.info(f"Generated visualization for {metric_name}")
        except Exception as e:
            logger.error(f"Failed to generate visualization for {metric_name}: {str(e)}")
