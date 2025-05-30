def run_fallback_visualization(metrics: Dict[str, Any], metric_names: List[str] = None):
    with shared_state.viz_lock:
        try:
            os.makedirs("visualizations", exist_ok=True)
            logging.basicConfig(level=logging.INFO, filename='visualization.log')
            logger = logging.getLogger(__name__)
            logger.info("Starting fallback visualization")

            if not metrics or 'metrics' not in metrics or not isinstance(metrics['metrics'], dict):
                logger.error(f"Invalid metrics data: {metrics}")
                raise ValueError("Metrics data is empty or invalid")

            atls_btls_metrics = EXPECTED_METRICS[:5]
            coverage_metrics = EXPECTED_METRICS[5:8]
            other_metrics = EXPECTED_METRICS[8:10]
            # Filter metrics to process based on metric_names
            target_metrics = metric_names if metric_names else (atls_btls_metrics + coverage_metrics + other_metrics)
            if 'Pass/Fail' in metrics['metrics'] and (not metric_names or 'Pass/Fail' in metric_names):
                target_metrics = list(set(target_metrics + ['Pass/Fail']))

            generated_files = []
            for metric in atls_btls_metrics:
                if metric not in target_metrics:
                    continue
                try:
                    data = metrics['metrics'].get(metric, {})
                    if not isinstance(data, dict) or 'ATLS' not in data or 'BTLS' not in data:
                        logger.warning(f"Creating placeholder for {metric}: invalid or missing ATLS/BTLS data")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, f"No data for {metric}", ha='center', va='center')
                        plt.title(metric)
                        filename = f'visualizations/{metric.replace("/", "_")}_atls_btls.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for {metric}: {filename}")
                        continue
                    atls_data = data.get('ATLS', [])
                    btls_data = data.get('BTLS', [])
                    versions = [item['version'] for item in atls_data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    atls_values = [float(item['value']) if isinstance(item['value'], (int, float)) else 0 for item in atls_data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    btls_values = [float(item['value']) if isinstance(item['value'], (int, float)) else 0 for item in btls_data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    if not versions or len(atls_values) != len(versions) or len(btls_values) != len(versions):
                        logger.warning(f"Creating placeholder for {metric}: inconsistent data lengths")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, f"Incomplete data for {metric}", ha='center', va='center')
                        plt.title(metric)
                        filename = f'visualizations/{metric.replace("/", "_")}_atls_btls.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for {metric}: {filename}")
                        continue
                    x = np.arange(len(versions))
                    width = 0.35
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.bar(x - width/2, atls_values, width, label='ATLS', color='blue')
                    plt.bar(x + width/2, btls_values, width, label='BTLS', color='orange')
                    plt.xlabel('Release')
                    plt.ylabel('Value')
                    plt.title(metric)
                    plt.xticks(x, versions)
                    plt.legend()
                    filename = f'visualizations/{metric.replace("/", "_")}_atls_btls.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated grouped bar chart for {metric}: {filename}")
                except Exception as e:
                    logger.error(f"Failed to generate chart for {metric}: {str(e)}")
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.text(0.5, 0.5, f"Error generating {metric}", ha='center', va='center')
                    plt.title(metric)
                    filename = f'visualizations/{metric.replace("/", "_")}_atls_btls.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated error placeholder chart for {metric}: {filename}")

            for metric in coverage_metrics:
                if metric not in target_metrics:
                    continue
                try:
                    data = metrics['metrics'].get(metric, [])
                    if not isinstance(data, list) or not data:
                        logger.warning(f"Creating placeholder for {metric}: invalid data format")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, f"No data for {metric}", ha='center', va='center')
                        plt.title(metric)
                        filename = f'visualizations/{metric.replace("/", "_")}.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for {metric}: {filename}")
                        continue
                    versions = [item['version'] for item in data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    values = [float(item['value']) if isinstance(item['value'], (int, float)) else 0 for item in data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    if not versions or len(values) != len(versions):
                        logger.warning(f"Creating placeholder for {metric}: inconsistent data lengths")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, f"Incomplete data for {metric}", ha='center', va='center')
                        plt.title(metric)
                        filename = f'visualizations/{metric.replace("/", "_")}.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for {metric}: {filename}")
                        continue
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.plot(versions, values, marker='o', color='green')
                    plt.xlabel('Release')
                    plt.ylabel('Value')
                    plt.title(metric)
                    filename = f'visualizations/{metric.replace("/", "_")}.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated line chart for {metric}: {filename}")
                except Exception as e:
                    logger.error(f"Failed to generate chart for {metric}: {str(e)}")
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.text(0.5, 0.5, f"Error generating {metric}", ha='center', va='center')
                    plt.title(metric)
                    filename = f'visualizations/{metric.replace("/", "_")}.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated error placeholder chart for {metric}: {filename}")

            for metric in other_metrics:
                if metric not in target_metrics:
                    continue
                try:
                    data = metrics['metrics'].get(metric, [])
                    if not isinstance(data, list) or not data:
                        logger.warning(f"Creating placeholder for {metric}: invalid data format")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, f"No data for {metric}", ha='center', va='center')
                        plt.title(metric)
                        filename = f'visualizations/{metric.replace("/", "_")}.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for {metric}: {filename}")
                        continue
                    versions = [item['version'] for item in data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    values = [float(item['value']) if isinstance(item['value'], (int, float)) else 0 for item in data if isinstance(item, dict) and 'version' in item and 'value' in item]
                    if not versions or len(values) != len(versions):
                        logger.warning(f"Creating placeholder for {metric}: inconsistent data lengths")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, f"Incomplete data for {metric}", ha='center', va='center')
                        plt.title(metric)
                        filename = f'visualizations/{metric.replace("/", "_")}.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for {metric}: {filename}")
                        continue
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.bar(versions, values, color='purple')
                    plt.xlabel('Release')
                    plt.ylabel('Value')
                    plt.title(metric)
                    filename = f'visualizations/{metric.replace("/", "_")}.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated bar chart for {metric}: {filename}")
                except Exception as e:
                    logger.error(f"Failed to generate chart for {metric}: {str(e)}")
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.text(0.5, 0.5, f"Error generating {metric}", ha='center', va='center')
                    plt.title(metric)
                    filename = f'visualizations/{metric.replace("/", "_")}.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated error placeholder chart for {metric}: {filename}")

            if 'Pass/Fail' in metrics['metrics'] and 'Pass/Fail' in target_metrics:
                try:
                    data = metrics['metrics'].get('Pass/Fail', {})
                    if not isinstance(data, dict):
                        logger.warning(f"Creating placeholder for Pass/Fail: invalid data format")
                        plt.figure(figsize=(8,5), dpi=120)
                        plt.text(0.5, 0.5, "No data for Pass/Fail", ha='center', va='center')
                        plt.title("Pass/Fail Metrics")
                        filename = 'visualizations/pass_fail.png'
                        plt.savefig(filename)
                        plt.close()
                        generated_files.append(filename)
                        logger.info(f"Generated placeholder chart for Pass/Fail: {filename}")
                    else:
                        pass_data = data.get('Pass', [])
                        fail_data = data.get('Fail', [])
                        versions = [item['version'] for item in pass_data if isinstance(item, dict) and 'version' in item and 'value' in item]
                        pass_values = [float(item['value']) if isinstance(item['value'], (int, float)) else 0 for item in pass_data if isinstance(item, dict) and 'version' in item and 'value' in item]
                        fail_values = [float(item['value']) if isinstance(item['value'], (int, float)) else 0 for item in fail_data if isinstance(item, dict) and 'version' in item and 'value' in item]
                        if not versions or len(pass_values) != len(versions) or len(fail_values) != len(versions):
                            logger.warning(f"Creating placeholder for Pass/Fail: inconsistent data lengths")
                            plt.figure(figsize=(8,5), dpi=120)
                            plt.text(0.5, 0.5, "Incomplete data for Pass/Fail", ha='center', va='center')
                            plt.title("Pass/Fail Metrics")
                            filename = 'visualizations/pass_fail.png'
                            plt.savefig(filename)
                            plt.close()
                            generated_files.append(filename)
                            logger.info(f"Generated placeholder chart for Pass/Fail: {filename}")
                        else:
                            x = np.arange(len(versions))
                            width = 0.35
                            plt.figure(figsize=(8,5), dpi=120)
                            plt.bar(x - width/2, pass_values, width, label='Pass', color='green')
                            plt.bar(x + width/2, fail_values, width, label='Fail', color='red')
                            plt.xlabel('Release')
                            plt.ylabel('Count')
                            plt.title('Pass/Fail Metrics')
                            plt.xticks(x, versions)
                            plt.legend()
                            filename = 'visualizations/pass_fail.png'
                            plt.savefig(filename)
                            plt.close()
                            generated_files.append(filename)
                            logger.info(f"Generated grouped bar chart for Pass/Fail: {filename}")
                except Exception as e:
                    logger.error(f"Failed to generate chart for Pass/Fail: {str(e)}")
                    plt.figure(figsize=(8,5), dpi=120)
                    plt.text(0.5, 0.5, "Error generating Pass/Fail", ha='center', va='center')
                    plt.title("Pass/Fail Metrics")
                    filename = 'visualizations/pass_fail.png'
                    plt.savefig(filename)
                    plt.close()
                    generated_files.append(filename)
                    logger.info(f"Generated error placeholder chart for Pass/Fail: {filename}")

            logger.info(f"Completed fallback visualization, generated {len(generated_files)} files")
            return generated_files
        except Exception as e:
            logger.error(f"Fallback visualization failed: {str(e)}")
            raise
        finally:
            plt.close('all')
