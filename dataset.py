from __future__ import print_function, division
import os
import torch
import torchvision.io
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import glob
from typing import List, Optional, Dict
from utils import IOHandler, get_mask
import pytorch_lightning as pl


def count_examples(dataset_dir: str) -> int:
    return len(glob.glob(os.path.join(dataset_dir, "*.jpeg")))


class RemoveMinimap(object):
    """Remove minimap (black square) from all the images in the sequence"""

    def __init__(self, hide_map_prob: float):
        """
        INIT

        :param float hide_map_prob: Probability of hiding the minimap (0<=hide_map_prob<=1)
        """

        self.hide_map_prob = hide_map_prob

    def __call__(self, sample: Dict[str, torch.tensor]) -> (torch.tensor, torch.tensor):
        """
        Applies the transformation to the sequence of images.

        :param Dict[str, np.ndarray] sample: Sequence of images
        :return: Dict[str, np.ndarray]- Transformed sequence of images
        """

        image, y = sample

        width: int = int(image.size(2) / 5)

        if self.hide_map_prob > 0:
            if torch.rand(1)[0] <= self.hide_map_prob:
                for j in range(0, 5):
                    image[:, 215:, j * width : (j * width) + 80] = torch.zeros(
                        (3, 55, 80), dtype=image.dtype
                    )

        return image, y


class RemoveImage(object):
    """
    Removes random images (black out) from the sequence
    """

    def __init__(self, dropout_images_prob: List[float]):
        """
        INIT

        :param  List[float] dropout_images_prob: Probability of dropping each image (0<=dropout_images_prob<=1)
        """
        self.dropout_images_prob = dropout_images_prob

    def __call__(self, sample: Dict[str, torch.tensor]) -> (torch.tensor, torch.tensor):
        """
        Applies the transformation to the sequence of images.

        :param Dict[str, np.ndarray] sample: Sequence of images
        :return: Dict[str, np.ndarray]- Transformed sequence of images
        """
        image, y = sample

        width: int = int(image.size(2) / 5)

        for j in range(0, 5):
            if self.dropout_images_prob[j] > 0:
                if torch.rand(1)[0] <= self.dropout_images_prob[j]:
                    image[:, :, j * width : (j + 1) * width] = torch.zeros(
                        (image.shape[0], image.shape[1], width), dtype=image.dtype
                    )

        return image, y


class SplitImages(object):
    """
    Splits a sequence image file into 5 images
    """

    def __call__(self, sample: torch.tensor) -> (torch.tensor, torch.tensor):
        """
        Applies the transformation to the sequence of images.

        :param np.ndarray sample: Sequence image
        :return: Dict[str, np.ndarray]- Transformed sequence of images
        """
        image, y = sample
        width: int = int(image.size(2) / 5)
        image1 = image[:, :, 0:width]
        image2 = image[:, :, width : width * 2]
        image3 = image[:, :, width * 2 : width * 3]
        image4 = image[:, :, width * 3 : width * 4]
        image5 = image[:, :, width * 4 : width * 5]
        return torch.stack([image1, image2, image3, image4, image5]), torch.tensor(y)


class SequenceColorJitter(object):
    """
    Randomly change the brightness, contrast and saturation of a sequence of images
    """

    def __init__(self, brightness=0.5, contrast=0.1, saturation=0.1, hue=0.5):
        """
        INIT

        :param float brightness: Probability of changing brightness (0<=brightness<=1)
        :param float contrast: Probability of changing contrast (0<=contrast<=1)
        :param float saturation: Probability of changing saturation (0<=saturation<=1)
        :param float hue: Probability of changing hue (0<=hue<=1)
        """
        self.jitter = transforms.ColorJitter(
            brightness=brightness, contrast=contrast, saturation=saturation, hue=hue
        )

    def __call__(self, sample: Dict[str, torch.tensor]) -> (torch.tensor, torch.tensor):
        """
        Applies the transformation to the sequence of images.

        :param Dict[str, torch.tensor] sample: Sequence of images
        :return: Dict[str, torch.tensor]- Transformed sequence of images
        """
        images, y = sample
        images = self.jitter(images)
        return images, y


class Normalize(object):
    """
    Normalize a tensor image with mean and standard deviation.
    """

    transform = transforms.Normalize(
        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    )

    def __call__(self, sample: (torch.tensor, torch.tensor)) -> (torch.tensor, torch.tensor):
        """
        Applies the transformation to the sequence of images.

        :param Dict[str, torch.tensor] sample: Sequence of images
        :return: Dict[str, torch.tensor]- Transformed sequence of images
        """
        images, y = sample

        return (
            torch.stack(
                [
                    self.transform(images[0] / 255.0),
                    self.transform(images[1] / 255.0),
                    self.transform(images[2] / 255.0),
                    self.transform(images[3] / 255.0),
                    self.transform(images[4] / 255.0),
                ]
            ),
            y,
        )


def collate_fn(batch):
    """
    Collate function for the dataloader.

    :param batch: List of samples
    :return: Dict[str, torch.tensor]- Transformed sequence of images
    """

    return_dict: Dict[str, torch.tensor] = {
        "images": torch.cat([b[0] for b in batch], dim=0),
        "attention_mask": torch.cat([b[1] for b in batch], dim=0),
        "y": torch.stack([b[2] for b in batch]),
    }
    return_dict["attention_mask"].requires_grad = False
    return_dict["y"].requires_grad = False
    return return_dict


def set_worker_sharing_strategy(worker_id: int) -> None:
    torch.multiprocessing.set_sharing_strategy("file_system")


class Tedd1104Dataset(Dataset):
    """TEDD1104 dataset."""

    def __init__(
        self,
        dataset_dir: str,
        hide_map_prob: float,
        token_mask_prob: float,
        transformer_nheads: int = None,
        dropout_images_prob: List[float] = None,
        sequence_length: int = 5,
        control_mode: str = "keyboard",
        train: bool = False,
    ):

        """
        INIT

        :param str dataset_dir: The directory of the dataset.
        :param bool hide_map_prob: Probability of hiding the minimap (0<=hide_map_prob<=1)
        :param bool token_mask_prob: Probability of masking a token in the transformer model (0<=token_mask_prob<=1)
        :param int transformer_nheads: Number of heads in the transformer model, None if LSTM is used
        :param List[float] dropout_images_prob: Probability of dropping an image (0<=dropout_images_prob<=1)
        :param int sequence_length: Length of the image sequence
        :param str control_mode: Type of the user input: "keyboard" or "controller"
        :param bool train: If True, the dataset is used for training.
        """

        self.dataset_dir = dataset_dir
        self.hide_map_prob = hide_map_prob
        self.dropout_images_prob = (
            dropout_images_prob if dropout_images_prob else [0.0] * sequence_length
        )
        self.control_mode = control_mode.lower()
        self.sequence_length = sequence_length
        self.token_mask_prob = token_mask_prob
        self.transformer_nheads = transformer_nheads
        self.train = train

        assert self.control_mode in [
            "keyboard",
            "controller",
        ], f"{self.control_mode} control mode not supported. Supported dataset types: [keyboard, controller].  "

        assert 0 <= self.hide_map_prob <= 1.0, (
            f"hide_map_prob not in 0 <= hide_map_prob <= 1.0 range. "
            f"hide_map_prob: {self.hide_map_prob}"
        )

        assert len(self.dropout_images_prob) == 5, (
            f"dropout_images_prob must have 5 probabilities, one for each image in the sequence. "
            f"dropout_images_prob len: {len(dropout_images_prob)}"
        )

        for dropout_image_prob in self.dropout_images_prob:
            assert 0 <= dropout_image_prob < 1.0, (
                f"All probabilities in dropout_image_prob must be in the range 0 <= dropout_image_prob < 1.0. "
                f"dropout_images_prob: {self.dropout_images_prob}"
            )

        assert 0 <= self.token_mask_prob < 1.0, (
            f"token_mask_prob not in 0 <= token_mask_prob < 1.0 range. "
            f"token_mask_prob: {self.token_mask_prob}"
        )

        if train:
            self.transform = transforms.Compose(
                [
                    RemoveMinimap(hide_map_prob=hide_map_prob),
                    RemoveImage(dropout_images_prob=dropout_images_prob),
                    SplitImages(),
                    SequenceColorJitter(),
                    Normalize(),
                ]
            )
        else:
            self.transform = transforms.Compose(
                [
                    # RemoveMinimap(hide_map_prob=hide_map_prob),
                    # RemoveImage(dropout_images_prob=dropout_images_prob),
                    SplitImages(),
                    # SequenceColorJitter(),
                    Normalize(),
                ]
            )

        self.dataset_files = glob.glob(os.path.join(dataset_dir, "*.jpeg"))

        self.IOHandler = IOHandler()

    def __len__(self):
        """
        Returns the length of the dataset.

        :return: int - Length of the dataset.
        """
        return len(self.dataset_files)

    def __getitem__(self, idx):
        """
        Returns a sample from the dataset.

        :param int idx: Index of the sample.
        :return: Dict[str, torch.tensor]- Transformed sequence of images
        """
        if torch.is_tensor(idx):
            idx = int(idx)

        img_name = self.dataset_files[idx]
        image = None
        while image is None:
            try:
                image = torchvision.io.read_image(img_name)
            except (ValueError, FileNotFoundError) as err:
                error_message = str(err).split("\n")[-1]
                print(
                    f"Error reading image: {img_name} probably a corrupted file.\n"
                    f"Exception: {error_message}\n"
                    f"We will load a random image instead."
                )
                img_name = self.dataset_files[
                    int(len(self.dataset_files) * torch.rand(1))
                ]

        y = self.IOHandler.imagename_input_conversion(
            image_name=img_name,
            output_type=self.control_mode,
        )

        image, y = self.transform((image, y))

        mask = get_mask(
            train=self.train,
            nheads=self.transformer_nheads,
            mask_prob=self.token_mask_prob,
            sequence_length=self.sequence_length,
        )

        return image, mask, y


class Tedd1104DataModule(pl.LightningDataModule):
    """
    Tedd1104DataModule is a PyTorch Lightning DataModule for the Tedd1104 dataset.
    """

    def __init__(
        self,
        batch_size: int,
        train_dir: str = None,
        val_dir: str = None,
        test_dir: str = None,
        token_mask_prob: float = 0.0,
        transformer_nheads: int = None,
        sequence_length: int = 5,
        hide_map_prob: float = 0.0,
        dropout_images_prob: List[float] = None,
        control_mode: str = "keyboard",
        num_workers: int = os.cpu_count(),
    ):
        """
        Initializes the Tedd1104DataModule.

        :param int batch_size: Batch size for the dataset.
        :param str train_dir: Directory containing the training dataset.
        :param str val_dir: Directory containing the validation dataset.
        :param str test_dir: Directory containing the test dataset.
        :param bool token_mask_prob: Probability of masking a token in the transformer model (0<=token_mask_prob<=1)
        :param int transformer_nheads: Number of heads in the transformer model, None if LSTM is used
        :param int sequence_length: Length of the image sequence
        :param float hide_map_prob: Probability of hiding the minimap (0<=hide_map_prob<=1)
        :param float dropout_images_prob: Probability of dropping an image (0<=dropout_images_prob<=1)
        :param str control_mode: Record the input from the "keyboard" or "controller"
        :param int num_workers: Number of workers to use to load the dataset.
        """
        super().__init__()
        self.train_dir = train_dir
        self.val_dir = val_dir
        self.test_dir = test_dir
        self.batch_size = batch_size
        self.token_mask_prob = token_mask_prob
        self.transformer_nheads = transformer_nheads
        self.sequence_length = sequence_length
        self.hide_map_prob = hide_map_prob
        self.dropout_images_prob = (
            dropout_images_prob if dropout_images_prob else [0.0, 0.0, 0.0, 0.0, 0.0]
        )
        self.control_mode = control_mode

        if num_workers > 32:
            print(
                "WARNING: num_workers is greater than 32, this may cause memory issues, consider using a smaller value."
                "Go ahead if you have a lot of RAM."
            )

        self.num_workers = num_workers

    def setup(self, stage: Optional[str] = None) -> None:
        """
        Sets up the dataset.

        :param str stage: Stage of the setup.
        """
        if stage in (None, "fit"):
            self.train_dataset = Tedd1104Dataset(
                dataset_dir=self.train_dir,
                hide_map_prob=self.hide_map_prob,
                dropout_images_prob=self.dropout_images_prob,
                control_mode=self.control_mode,
                train=True,
                token_mask_prob=self.token_mask_prob,
                transformer_nheads=self.transformer_nheads,
                sequence_length=self.sequence_length,
            )

            print(f"Total training samples: {len(self.train_dataset)}.")

            self.val_dataset = Tedd1104Dataset(
                dataset_dir=self.val_dir,
                hide_map_prob=0.0,
                dropout_images_prob=[0.0, 0.0, 0.0, 0.0, 0.0],
                control_mode="keyboard",
                token_mask_prob=0.0,
                transformer_nheads=self.transformer_nheads,
                sequence_length=self.sequence_length,
            )

            print(f"Total validation samples: {len(self.val_dataset)}.")

        if stage in (None, "test"):
            self.test_dataset = Tedd1104Dataset(
                dataset_dir=self.test_dir,
                hide_map_prob=0.0,
                dropout_images_prob=[0.0, 0.0, 0.0, 0.0, 0.0],
                control_mode="keyboard",
                token_mask_prob=0.0,
                transformer_nheads=self.transformer_nheads,
                sequence_length=self.sequence_length,
            )

            print(f"Total test samples: {len(self.test_dataset)}.")

    def train_dataloader(self) -> DataLoader:
        """
        Returns the training dataloader.

        :return: DataLoader - Training dataloader.
        """
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            pin_memory=True,
            shuffle=True,
            persistent_workers=True,
            collate_fn=collate_fn,
            worker_init_fn=set_worker_sharing_strategy,
        )

    def val_dataloader(self) -> DataLoader:
        """
        Returns the validation dataloader.

        :return: DataLoader - Validation dataloader.
        """
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            pin_memory=True,
            shuffle=False,
            persistent_workers=True,
            collate_fn=collate_fn,
            worker_init_fn=set_worker_sharing_strategy,
        )

    def test_dataloader(self) -> DataLoader:
        """
        Returns the test dataloader.

        :return: DataLoader - Test dataloader.
        """
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            pin_memory=True,
            shuffle=False,
            persistent_workers=True,
            collate_fn=collate_fn,
            worker_init_fn=set_worker_sharing_strategy,
        )
