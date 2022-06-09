from dataset import SplitImages
import os
import glob
import torch
import torchvision
from tqdm.auto import tqdm
import argparse


def calculate_mean_str(dataset_dir: str):
    dataset_files = list(glob.glob(os.path.join(dataset_dir, "*.jpeg")))
    transform = torchvision.transforms.Compose(
        [
            SplitImages(),
        ]
    )

    mean_sum = 0.0
    stds_sum = 0.0
    total = 0

    with tqdm(
        total=len(dataset_files),
        desc=f"Reading images. Mean: {round(mean_sum/(total if total>0 else 1),6)}. STD: {round(stds_sum/(total if total>0 else 1),6)}",
    ) as pbar:
        for img_name in dataset_files:
            images = torchvision.io.read_image(img_name)
            y = 0
            images, _ = transform((images, y))
            for image in images:
                mean_sum += torch.mean(image / 255.0).item()
                stds_sum += torch.std(image / 255.0).item()
                total += 1
            pbar.update(1)
            pbar.set_description(
                desc=f"Reading images. Mean: {round(mean_sum/(total if total>0 else 1),6)}. STD: {round(stds_sum/(total if total>0 else 1),6)}",
            )

    mean = mean_sum / total
    std = stds_sum / total

    print(f"Mean: {mean}")
    print(f"std: {std}")

    return mean, std


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset_dir",
        type=str,
        required=True,
        help="Path to the dataset directory containing jpeg files.",
    )

    args = parser.parse_args()

    mean, std = calculate_mean_str(dataset_dir=args.dataset_dir)
    with open("image_metrics.txt", "w", encoding="utf8") as output_file:
        print(f"Mean: {mean}", file=output_file)
        print(f"STD: {std}", file=output_file)
