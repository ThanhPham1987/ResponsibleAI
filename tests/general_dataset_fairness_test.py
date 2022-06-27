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
from aif360.metrics import BinaryLabelDatasetMetric

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


names = [feature.name for feature in ai.meta_database.features]
df = pd.DataFrame(xTest, columns=names)
df['y'] = yTest

# structuredDataset = StructuredDataset(df, names, protected_attribute_names=['race'])
binDataset = BinaryLabelDataset(df=df, label_names=['y'], protected_attribute_names=['race'])
benchmark = BinaryLabelDatasetMetric(binDataset)

clf.fit(xTrain, yTrain)
predictions = clf.predict(xTest)
ai.compute({"test": predictions}, tag="Random Forest")

metrics = ai.get_metric_values()
metrics = metrics["test"]
info = ai.get_metric_info()


def test_base_rate():
    """Tests that the RAI pearson correlation calculation is correct."""
    assert metrics['dataset_fairness']['base_rate'] == benchmark.base_rate()


def test_num_instances():
    """Tests that the RAI pearson correlation calculation is correct."""
    assert metrics['dataset_fairness']['num_instances'] == benchmark.num_instances()


def test_num_negatives():
    """Tests that the RAI num negatives calculation is correct."""
    assert metrics['dataset_fairness']['num_negatives'] == benchmark.num_negatives()


def test_num_positives():
    """Tests that the RAI num positives calculation is correct."""
    assert metrics['dataset_fairness']['num_positives'] == benchmark.num_positives()
