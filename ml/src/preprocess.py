import cv2
import numpy as np
from PIL import Image
import torchvision.transforms as transforms

class AdvancedPreprocessing:
    """
    Custom preprocessing step applying OpenCV Median Blur and CLAHE
    to enhance thermal Paddy Leaf images before deep learning inference/training.
    Matches exact notebook pipeline.
    """
    def __init__(self, median_blur_ksize=3, clahe_clip_limit=2.0, clahe_tile_grid_size=(8, 8)):
        self.median_blur_ksize = median_blur_ksize
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_grid_size = clahe_tile_grid_size
        self.clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=self.clahe_tile_grid_size)

    def __call__(self, img: Image.Image) -> Image.Image:
        img_np = np.array(img)

        if img_np.dtype != np.uint8:
            img_np = cv2.normalize(img_np, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        if len(img_np.shape) == 3 and img_np.shape[2] == 3:
            # RGB thermal image
            img_np = cv2.medianBlur(img_np, self.median_blur_ksize)
            channels = cv2.split(img_np)
            clahe_channels = [self.clahe.apply(ch) for ch in channels]
            processed_img_np = cv2.merge(clahe_channels)
        elif len(img_np.shape) == 2 or (len(img_np.shape) == 3 and img_np.shape[2] == 1):
            # Grayscale image
            if len(img_np.shape) == 3 and img_np.shape[2] == 1:
                img_np = img_np.squeeze(2)
            img_np = cv2.medianBlur(img_np, self.median_blur_ksize)
            processed_img_np = self.clahe.apply(img_np)
            processed_img_np = processed_img_np[:, :, np.newaxis]
        else:
            processed_img_np = img_np

        return Image.fromarray(processed_img_np)

# ImageNet normalization statistics as used in training notebook
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

def get_inference_transform():
    """
    Returns the exact evaluation/inference transform pipeline:
    Resize(256) -> CenterCrop(224) -> AdvancedPreprocessing() -> ToTensor() -> Normalize()
    """
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        AdvancedPreprocessing(),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD)
    ])

# Explicit mapping of class index to disease name & display details
CLASS_MAPPING = {
    0: "Bacterial Leaf Blight",
    1: "Rice Blast",
    2: "Healthy",
    3: "Hispa",
    4: "Leaf Folder",
    5: "Brown Leaf Spot"
}

CLASS_KEYS = {
    0: "BLB",
    1: "Blast",
    2: "healthy",
    3: "hispa",
    4: "leaf_folder",
    5: "leaf_spot"
}
