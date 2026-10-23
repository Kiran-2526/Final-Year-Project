# ML Subsystem - Thermal Image Paddy Leaf Disease Detection

This directory contains the machine learning pipeline, pretrained model weights, and ONNX export tools for the thermal paddy leaf disease classification model.

## Model Architecture
- **Base Network**: PyTorch `ResNet50` via `timm`
- **Output Classes**: 6 multiclass categories:
  0: Bacterial Leaf Blight (`BLB`)
  1: Rice Blast (`Blast`)
  2: Healthy (`healthy`)
  3: Hispa (`hispa`)
  4: Leaf Folder (`leaf folder`)
  5: Brown Leaf Spot (`leaf spot`)

## Preprocessing Pipeline
1. OpenCV Median Blur ($k=3$)
2. OpenCV CLAHE ($\text{clipLimit}=2.0, \text{tileGridSize}=(8,8)$)
3. Resize to 256
4. CenterCrop to 224
5. ImageNet Normalization ($\text{mean}=[0.485, 0.456, 0.406], \text{std}=[0.229, 0.224, 0.225]$)

## Export & Inference
- Model checkpoint saved at: `ml/models/best_model.pth`
- Exported single-file ONNX model saved at: `ml/models/resnet50_paddy.onnx`

To export to ONNX:
```bash
python ml/src/export_onnx.py
```
To evaluate and save metrics:
```bash
python ml/src/evaluate.py
```
