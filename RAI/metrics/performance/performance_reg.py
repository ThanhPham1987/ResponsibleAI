from RAI.metrics.metric_group import MetricGroup
import sklearn
import os


class PerformanceRegMetricGroup(MetricGroup, class_location=os.path.abspath(__file__)):
    def __init__(self, ai_system) -> None:
        super().__init__(ai_system)

    def update(self, data):
        pass

    def compute(self, data_dict):
        if "data" and "predictions" in data_dict:
            data = data_dict["data"]
            preds = data_dict["predictions"]
            args = {}
            if self.ai_system.metric_manager.user_config is not None and "bias" in self.ai_system.metric_manager.user_config and "args" in self.ai_system.metric_manager.user_config["bias"]:
                args = self.ai_system.metric_manager.user_config["bias"]["args"]

            self.metrics["explained_variance"].value = sklearn.metrics.explained_variance_score(data.y, preds, **args.get("explained_variance", {}))
            self.metrics["mean_absolute_error"].value = sklearn.metrics.mean_absolute_error(data.y, preds, **args.get("mean_absolute_error", {}))
            self.metrics["mean_absolute_percentage_error"].value = sklearn.metrics.mean_absolute_percentage_error(data.y, preds, **args.get("mean_absolute_percentage_error", {}))
            self.metrics["mean_gamma_deviance"].value = sklearn.metrics.mean_gamma_deviance(data.y, preds, **args.get("mean_gamma_deviance", {}))
            self.metrics["mean_poisson_deviance"].value = sklearn.metrics.mean_poisson_deviance(data.y, preds, **args.get("mean_poisson_deviance", {}))
            self.metrics["mean_squared_error"].value = sklearn.metrics.mean_squared_error(data.y, preds, **args.get("mean_squared_error", {}))
            self.metrics["mean_squared_log_error"].value = sklearn.metrics.mean_squared_log_error(data.y, preds, **args.get("mean_squared_log_error", {}))
            self.metrics["median_absolute_error"].value = sklearn.metrics.median_absolute_error(data.y, preds, **args.get("median_absolute_error", {}))
            self.metrics["r2"].value = sklearn.metrics.r2_score(data.y, preds, **args.get("r2", {}))