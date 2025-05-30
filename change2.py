@app.post("/update_metrics", response_model=AnalysisResponse)
async def update_metrics(request: UpdateMetricsRequest):
    try:
        folder_path = convert_windows_path(request.folder_path)
        folder_path = os.path.normpath(folder_path)
        folder_path_hash = hash_string(folder_path)
        pdf_files = get_pdf_files_from_folder(folder_path)
        pdfs_hash = hash_pdf_contents(pdf_files)
        logger.info(f"Updating metrics for folder_path_hash: {folder_path_hash}, pdfs_hash: {pdfs_hash}")

        # Get existing cached report or run full analysis
        cached_response = get_cached_report(folder_path_hash, pdfs_hash)
        if not cached_response:
            logger.info(f"No cached report found, running full analysis")
            folder_path_request = FolderPathRequest(folder_path=folder_path, clear_cache=False)
            cached_response = await run_full_analysis(folder_path_request)

        # Detect changed metrics
        diff = deepdiff.DeepDiff(cached_response.metrics['metrics'], request.metrics['metrics'], ignore_order=True)
        changed_metrics = []
        if diff:
            for change_type in ['values_changed', 'dictionary_item_added', 'dictionary_item_removed']:
                if change_type in diff:
                    for path in diff[change_type]:
                        # Extract metric name from path (e.g., "root['Open ALL RRR Defects']")
                        match = re.search(r"\['([^']+)'\]", path)
                        if match:
                            metric_name = match.group(1)
                            if metric_name not in changed_metrics and metric_name != 'Customer Specific Testing (UAT)':
                                changed_metrics.append(metric_name)
            logger.info(f"Changed metrics detected: {changed_metrics}")

        # Initialize response
        updated_response = AnalysisResponse(
            metrics=request.metrics,
            visualizations=cached_response.visualizations,
            report=enhance_report_markdown(request.report),
            evaluation=cached_response.evaluation,
            hyperlinks=cached_response.hyperlinks,
            visualization_map=cached_response.visualization_map or {}  # Initialize if not present
        )

        # Regenerate visualizations for changed metrics
        viz_folder = "visualizations"
        os.makedirs(viz_folder, exist_ok=True)
        viz_base64 = updated_response.visualizations.copy()
        visualization_map = updated_response.visualization_map.copy()
        if changed_metrics:
            logger.info(f"Regenerating visualizations for changed metrics: {changed_metrics}")
            # Remove existing visualizations for changed metrics
            for metric_name in changed_metrics:
                if metric_name in EXPECTED_METRICS[:5]:  # ATLS/BTLS
                    filename = f"{metric_name.replace('/', '_')}_atls_btls.png"
                elif metric_name == 'Pass/Fail':
                    filename = 'pass_fail.png'
                else:
                    filename = f"{metric_name.replace('/', '_')}.png"
                filepath = os.path.join(viz_folder, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)

            # Try running visualizations.py
            script_path = "visualizations.py"
            try:
                if os.path.exists(script_path):
                    with shared_state.viz_lock:
                        logger.info(f"Executing existing {script_path}")
                        runpy.run_path(script_path, init_globals={'metrics': request.metrics})
                        logger.info("Visualizations script executed successfully")
                else:
                    logger.warning(f"{script_path} not found, falling back to run_fallback_visualization")
                    run_fallback_visualization(request.metrics, changed_metrics)
            except Exception as e:
                logger.error(f"Visualization script failed: {str(e)}")
                logger.info("Running fallback visualization for changed metrics")
                run_fallback_visualization(request.metrics, changed_metrics)

            # Collect new visualizations
            existing_files = {f for f in os.listdir(viz_folder) if f.endswith('.png')}
            viz_index = len(viz_base64)
            for metric_name in changed_metrics:
                if metric_name in EXPECTED_METRICS[:5]:
                    filename = f"{metric_name.replace('/', '_')}_atls_btls.png"
                elif metric_name == 'Pass/Fail':
                    filename = 'pass_fail.png'
                else:
                    filename = f"{metric_name.replace('/', '_')}.png"
                if filename in existing_files:
                    filepath = os.path.join(viz_folder, filename)
                    base64_str = get_base64_image(filepath)
                    if base64_str:
                        if metric_name in visualization_map:
                            viz_base64[visualization_map[metric_name]] = base64_str
                        else:
                            viz_base64.append(base64_str)
                            visualization_map[metric_name] = viz_index
                            viz_index += 1

            updated_response.visualizations = viz_base64
            updated_response.visualization_map = visualization_map

            # Validate minimum visualizations
            min_visualizations = 5
            if len(viz_base64) < min_visualizations:
                logger.error(f"Too few visualizations: {len(viz_base64)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate minimum required visualizations: got {len(viz_base64)}, need at least {min_visualizations}"
                )

        # Re-evaluate report
        full_source_text = "\n".join(
            f"File: {os.path.basename(pdf)}\n{locate_table(extract_text_from_pdf(pdf), START_HEADER_PATTERN, END_HEADER)}"
            for pdf in pdf_files
        )
        score, evaluation = evaluate_with_llm_judge(full_source_text, updated_response.report)
        updated_response.evaluation = {"score": score, "text": evaluation}

        # Update cache
        store_cached_report(folder_path_hash, pdfs_hash, updated_response)
        logger.info(f"Updated cache for folder_path_hash: {folder_path_hash}")
        return updated_response

    except Exception as e:
        logger.error(f"Error in /update_metrics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        plt.close('all')
