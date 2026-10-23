import torch
import torch.nn as nn
import timm

def build_model(num_classes=6, pretrained=False):
    """
    Builds ResNet50 model matching notebook architecture.
    """
    model = timm.create_model("resnet50", pretrained=pretrained, num_classes=num_classes)
    return model

def load_trained_model(checkpoint_path, device="cpu"):
    """
    Loads saved checkpoint weights into ResNet50 model.
    """
    model = build_model(num_classes=6, pretrained=False)
    state_dict = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
