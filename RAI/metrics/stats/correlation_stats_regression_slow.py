from RAI.metrics.metric_group import MetricGroup
import scipy.stats
from RAI.utils.utils import calculate_per_all_features
import os


class CorrelationStatRegressionSlow(MetricGroup, class_location=os.path.abspath(__file__)):
    def __init__(self, ai_system) -> None:
        super().__init__(ai_system)
        
    def update(self, data):
        pass

    def compute(self, data_dict):
        if "data" in data_dict:
            args = {}
            if self.ai_system.metric_manager.user_config is not None and "stats" in self.ai_system.metric_manager.user_config and "args" in self.ai_system.metric_manager.user_config["stats"]:
                args = self.ai_system.metric_manager.user_config["stats"]["args"]
            data = data_dict["data"]
            scalar_data = data.scalar
            map = self.ai_system.meta_database.scalar_map
            features = self.ai_system.meta_database.features

            self.metrics["siegel-slopes"].value = calculate_per_all_features(scipy.stats.siegelslopes, scalar_data, data.y, map, features)
            self.metrics["theil-slopes"].value = calculate_per_all_features(scipy.stats.theilslopes, scalar_data, data.y, map, features)
