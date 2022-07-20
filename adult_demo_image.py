from RAI.AISystem import AISystem, Model
from RAI.redis import RaiRedis
from RAI.utils import torch_to_RAI
from RAI.dataset import MetaDatabase, Feature, Dataset, Data
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import os
import random
import numpy as np


def main():
    use_dashboard = True
    os.environ["CUDA_VISIBLE_DEVICES"] = "cpu"
    torch.manual_seed(0)
    random.seed(0)
    np.random.seed(10)
    PATH = './cifar_net.pth'
    batch_size = 4

    # Get Data
    transform = transforms.Compose([transforms.ToTensor(),
                                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                            download=True, transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size,
                                              shuffle=True, num_workers=2)

    testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                           download=True, transform=transform)
    testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size,
                                             shuffle=False, num_workers=2)

    print("Converting test data")
    xTestData, yTestData = torch_to_RAI(testloader)
    print("Converting train data")
    xTrainData, yTrainData = torch_to_RAI(trainloader)
    print("Done data conversion")

    classes = ('plane', 'car', 'bird', 'cat',
               'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 6, 5)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(6, 16, 5)
            self.fc1 = nn.Linear(16 * 5 * 5, 120)
            self.fc2 = nn.Linear(120, 84)
            self.fc3 = nn.Linear(84, 10)

        def forward(self, x):
            x = self.pool(F.relu(self.conv1(x)))
            x = self.pool(F.relu(self.conv2(x)))
            x = torch.flatten(x, 1)  # flatten all dimensions except batch
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            x = self.fc3(x)
            return x

    net = Net()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

    def train():
        print("Starting training")
        for epoch in range(2):  # loop over the dataset multiple times
            running_loss = 0.0
            for i, data in enumerate(trainloader, 0):
                inputs, labels = data
                optimizer.zero_grad()
                outputs = net(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
                if i % 2000 == 1999:  # print every 2000 mini-batches
                    print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
                    running_loss = 0.0
        print('Finished Training')
        torch.save(net.state_dict(), PATH)

    if os.path.isfile(PATH):
        print("Loading model")
        net.load_state_dict(torch.load(PATH))
    else:
        train()

    image = Feature('Image', 'Image', 'The 32x32 input image')
    outputs = Feature('image_type', 'numerical', 'The type of image', categorical=True,
                      values={i: v for i, v in enumerate(classes)})
    meta = MetaDatabase([image])
    model = Model(agent=net, output_features=outputs, name="conv_net", predict_fun=net, description="ConvNet", model_class="ConvNet")
    configuration = {"time_complexity": "polynomial"}
    dataset = Dataset({"train": Data(xTrainData, yTrainData), "test": Data(xTestData, yTestData)})
    ai = AISystem(name="CIFAR_Conv_1",  task='classification', meta_database=meta, dataset=dataset, model=model)
    ai.initialize(user_config=configuration)

    preds = []
    for i, vals in enumerate(testloader, 0):
        image, label = vals
        _, predicted = torch.max(net(image), 1)
        preds += predicted

    ai.compute({"test": {"predict": preds}}, tag='model1')

    if use_dashboard:
        r = RaiRedis(ai)
        r.connect()
        r.reset_redis()
        r.add_measurement()
        r.add_dataset()

    ai.display_metric_values()

    from RAI.Analysis import AnalysisManager
    analysis = AnalysisManager()
    print("available analysis: ", analysis.get_available_analysis(ai, "test"))
    result = analysis.run_all(ai, "test", "Test run!")
    for analysis in result:
        print("Analysis: " + analysis)
        print(result[analysis].to_string())

if __name__ == '__main__':
    main()
