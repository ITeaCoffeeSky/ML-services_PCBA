import torch
from torchvision import transforms
from torchvision.transforms import v2
from torch.utils.data import Dataset
from torchvision.io import read_image
# from PIL import Image
# import io
import logging

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# logging settings
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)
py_handler = logging.FileHandler(f"./log/{__name__}.log", mode='a')
py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
py_handler.setFormatter(py_formatter)
py_logger.addHandler(py_handler)
py_logger.info(f"Start logging for module {__name__}...")


class image(Dataset):

    def __init__(self, X, Y, transform=None):
        self.X = X
        self.y = Y
        self.transform = transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):

        img_path = self.X[idx]
        image = read_image(img_path)

        if image.size()[0] == 1:
            image = image.expand(3, *image.shape[1:])

        if self.transform:
            # image = train_transforms1(image)
            image = self.transform(image)

        return image, self.y[idx]


def accuracy_recall_precision(model, dataloader):
    model.eval()

    all_predictions = []
    all_labels = []

    #  computing accuracy
    total_correct = 0
    total_instances = 0
    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)
        all_labels.extend(labels)
        predictions = torch.argmax(model(images), dim=1)
        all_predictions.extend(predictions)
        correct_predictions = sum(predictions == labels).item()
        total_correct += correct_predictions
        total_instances += len(images)
    accuracy = round(total_correct/total_instances, 4)

    #  computing recall and precision
    true_positives = 0
    false_negatives = 0
    false_positives = 0
    for idx in range(len(all_predictions)):
        if all_predictions[idx].item() == 1 and all_labels[idx].item() == 1:
            true_positives += 1
        elif all_predictions[idx].item() == 0 and all_labels[idx].item() == 1:
            false_negatives += 1
        elif all_predictions[idx].item() == 1 and all_labels[idx].item() == 0:
            false_positives += 1
    try:
        recall = round(true_positives/(true_positives + false_negatives), 4)
    except ZeroDivisionError:
        recall = 0.0
    try:
        precision = round(true_positives/(true_positives + false_positives), 4)
    except ZeroDivisionError:
        precision = 0.0

    return accuracy, recall, precision


def get_predict(model, dataloader):
    test_res = []
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            preds = model(inputs)
            preds_class = preds.argmax(dim=1)

            test_res.extend(preds_class.tolist())

    return test_res


def predict(X: list, y: list):

    resolution = (240, 240)

    test_transforms = transforms.Compose([
        transforms.Resize(resolution),
        v2.ToDtype(torch.float32, scale=True),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    test_X = X
    test_y = y

    test_dataset = image(test_X, test_y, test_transforms)

    batch_size = 10

    test_dataloader = torch.utils.data.DataLoader(test_dataset,
                                                  batch_size=batch_size,
                                                  shuffle=False,
                                                  num_workers=0)

    model_path = './models'
    model = torch.load(f'{model_path}/EfV2L_model_base_v1.pt')
    model = model.to(device)

    accuracy, recall, precision = accuracy_recall_precision(model, test_dataloader)
    y_pred = get_predict(model, test_dataloader)

    m = 'EfV2L_model_base_v1'
    py_logger.info(f"Model used: {m}")
    py_logger.info(f"Results: accuracy = {accuracy}, recall = {recall}, precision = {precision}")
    py_logger.info(f"Model out values: {y_pred}")

    return y_pred
