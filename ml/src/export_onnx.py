import os
import torch
import numpy as np
import onnx
import onnxruntime as ort
from model import load_trained_model

def export_to_onnx(pth_path, onnx_output_path):
    print(f"Loading PyTorch checkpoint from {pth_path}...")
    model = load_trained_model(pth_path, device="cpu")

    dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)

    os.makedirs(os.path.dirname(onnx_output_path), exist_ok=True)
    
    print(f"Exporting model to ONNX: {onnx_output_path}...")
    
    # Use dynamo=False to ensure clean single-file export compatible with all ONNX runtimes
    torch.onnx.export(
        model,
        dummy_input,
        onnx_output_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        },
        dynamo=False
    )
    
    # Consolidate external data if any into single self-contained ONNX file
    model_proto = onnx.load(onnx_output_path)
    onnx.save_model(model_proto, onnx_output_path, save_as_external_data=False)
    
    # Remove external data file if created
    ext_data_path = onnx_output_path + ".data"
    if os.path.exists(ext_data_path):
        os.remove(ext_data_path)

    print(f"Single-file ONNX export complete: {os.path.getsize(onnx_output_path)} bytes")

    print("Verifying ONNX model execution with ONNX Runtime...")
    session = ort.InferenceSession(onnx_output_path)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    with torch.no_grad():
        torch_out = model(dummy_input).numpy()

    onnx_out = session.run([output_name], {input_name: dummy_input.numpy()})[0]

    np.testing.assert_allclose(torch_out, onnx_out, rtol=1e-3, atol=1e-4)
    print("SUCCESS: PyTorch and ONNX outputs match perfectly!")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pth_file = os.path.join(base_dir, "models", "best_model.pth")
    if not os.path.exists(pth_file):
        raise FileNotFoundError(f"Model checkpoint not found at {pth_file}")

    onnx_file = os.path.join(base_dir, "models", "resnet50_paddy.onnx")
    export_to_onnx(pth_file, onnx_file)
