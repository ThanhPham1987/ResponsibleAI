import os
import sys
from RAI.dataset import Data, Dataset
from RAI.AISystem import AISystem, Model
from RAI.utils import df_to_RAI
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from aif360.datasets import BinaryLabelDataset
from aif360.metrics import ClassificationMetric
from aif360.sklearn.metrics import average_odds_error

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
use_dashboard = False
np.random.seed(21)

data_path = "../data/adult/"
train_data = pd.read_csv(data_path + "train.csv", header=0,
                         skipinitialspace=True, na_values="?")
test_data = pd.read_csv(data_path + "test.csv", header=0,
                        skipinitialspace=True, na_values="?")

all_data = pd.concat([train_data, test_data], ignore_index=True)
idx = all_data['race'] != 'White'
all_data['race'][idx] = 'Black'

meta, X, y = df_to_RAI(all_data, target_column="income-per-year", normalize=None, max_categorical_threshold=5)
xTrain, xTest, yTrain, yTest = train_test_split(X, y, random_state=1, stratify=y)

clf = RandomForestClassifier(n_estimators=10, criterion='entropy', random_state=0, min_samples_leaf=5, max_depth=2)

model = Model(agent=clf, name="test_classifier", task='binary_classification', predict_fun=clf.predict, predict_prob_fun=clf.predict_proba,
              description="Detect Cancer in patients using skin measurements", model_class="Random Forest Classifier")
configuration = {"fairness": {"priv_group": {"race": {"privileged": 1, "unprivileged": 0}},
                              "protected_attributes": ["race"], "positive_label": 1},
                 "time_complexity": "polynomial"}

dataset = Dataset({"train": Data(xTrain, yTrain), "test": Data(xTest, yTest)})
ai = AISystem("AdultDB_Test1", meta_database=meta, dataset=dataset, model=model, enable_certificates=False)
ai.initialize(user_config=configuration)

clf.fit(xTrain, yTrain)
predictions = clf.predict(xTest)

names = [feature.name for feature in ai.meta_database.features]
df = pd.DataFrame(xTest, columns=names)
df['y'] = yTest

bin_gt_dataset = BinaryLabelDataset(df=df, label_names=['y'], protected_attribute_names=['race'])

df_preds = pd.DataFrame(xTest, columns=names)
df_preds['y'] = predictions
bin_pred_dataset = BinaryLabelDataset(df=df_preds, label_names=['y'], protected_attribute_names=['race'])

benchmark = ClassificationMetric(bin_gt_dataset, bin_pred_dataset, privileged_groups=[{"race": 1}],
                                 unprivileged_groups=[{"race": 0}])

ai.compute({"test": predictions}, tag="Random Forest")
metrics = ai.get_metric_values()
metrics = metrics["test"]
info = ai.get_metric_info()


def test_disparate_impact():
    """Tests that the RAI disparate_impact calculation is correct."""
    assert metrics['group_fairness']['disparate_impact_ratio'] == benchmark.disparate_impact()


def test_statistical_parity_difference():
    """Tests that the RAI statistical_parity_difference calculation is correct."""
    assert metrics['group_fairness']['statistical_parity_difference'] == benchmark.statistical_parity_difference()


def test_between_group_generalized_entropy_index():
    """Tests that the RAI between_group_generalized_entropy_index calculation is correct."""
    assert metrics['group_fairness']['between_group_generalized_entropy_error'] == benchmark.between_group_generalized_entropy_index()


def test_equal_opportunity_difference():
    """Tests that the RAI equal_opportunity_difference calculation is correct."""
    assert metrics['group_fairness']['equal_opportunity_difference'] == benchmark.equal_opportunity_difference()


def test_average_odds_difference():
    """Tests that the RAI average_odds_difference calculation is correct."""
    assert metrics['group_fairness']['average_odds_difference'] == benchmark.average_odds_difference()


def test_average_odds_difference():
    """Tests that the RAI average_odds_difference calculation is correct."""
    # Convert to pandas series.
    gt_series = df['y'].squeeze()
    gt_series.index = df['race']
    assert metrics['group_fairness']['average_odds_error'] == average_odds_error(gt_series, predictions, prot_attr='race')
