import os
import argparse
import numpy as np
import torch
from PIL import Image
import onnxruntime as ort
from preprocess import get_inference_transform, CLASS_MAPPING, CLASS_KEYS
from model import load_trained_model

def predict_pytorch(model, img_path):
    transform = get_inference_transform()
    img = Image.open(img_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)  # Shape: (1, 3, 224, 224)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1).numpy()[0]
    
    pred_idx = int(np.argmax(probs))
    return pred_idx, float(probs[pred_idx]), probs

def predict_onnx(onnx_path, img_path):
    transform = get_inference_transform()
    img = Image.open(img_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).numpy().astype(np.float32)

    session = ort.InferenceSession(onnx_path)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    outputs = session.run([output_name], {input_name: tensor})[0]
    
    # Apply softmax manually
    exp_outs = np.exp(outputs - np.max(outputs, axis=1, keepdims=True))
    probs = (exp_outs / np.sum(exp_outs, axis=1, keepdims=True))[0]

    pred_idx = int(np.argmax(probs))
    return pred_idx, float(probs[pred_idx]), probs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thermal Paddy Leaf Disease Predictor")
    parser.add_argument("--image", type=str, required=True, help="Path to input thermal image")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pth_file = os.path.join(base_dir, "models", "best_model.pth")
    onnx_file = os.path.join(base_dir, "models", "resnet50_paddy.onnx")

    print(f"Testing image: {args.image}")
    
    if os.path.exists(pth_file):
        model = load_trained_model(pth_file)
        idx, conf, probs = predict_pytorch(model, args.image)
        print(f"[PyTorch Prediction] Class {idx}: {CLASS_MAPPING[idx]} | Confidence: {conf*100:.2f}%")

    if os.path.exists(onnx_file):
        idx_o, conf_o, probs_o = predict_onnx(onnx_file, args.image)
        print(f"[ONNX Prediction] Class {idx_o}: {CLASS_MAPPING[idx_o]} | Confidence: {conf_o*100:.2f}%")
