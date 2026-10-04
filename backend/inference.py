import os
import urllib.request
import nibabel as nib
import numpy as np
import torch

from monai.inferers import SlidingWindowInferer
from monai.transforms import NormalizeIntensity
from monai.transforms import Resize

from model import create_model


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "brats_mri_segmentation.pth"
)

MODEL_URL = os.getenv("MODEL_URL")

if not os.path.exists(MODEL_PATH):
    if not MODEL_URL:
        raise RuntimeError(
            "Model file not found and MODEL_URL is not configured."
        )

    print("Downloading segmentation model...")
    urllib.request.urlretrieve(
        MODEL_URL,
        MODEL_PATH
    )
    print("Model download complete.")

device = torch.device("cpu")

model = create_model()

state_dict = torch.load(
    MODEL_PATH,
    map_location=device
)

model.load_state_dict(state_dict)
model.to(device)
model.eval()

normalizer = NormalizeIntensity(
    nonzero=True,
    channel_wise=True
)

INFERENCE_SHAPE = (48, 96, 96)

# Keep inference within the memory budget of the hosted CPU service.
inferer = SlidingWindowInferer(
    roi_size=INFERENCE_SHAPE,
    sw_batch_size=1,
    overlap=0.25
)


def segment_brain(input_path):

    nii = nib.load(input_path)
    original_shape = nii.shape[:3]
    original_affine = nii.affine.copy()

    print("Original MRI shape:", nii.shape)

    if len(nii.shape) not in (3, 4):
        raise ValueError(
            "Expected a 3D MRI or a 4D NIfTI containing 4 MRI modalities."
        )

    if len(nii.shape) == 4 and nii.shape[-1] != 4:
        raise ValueError(
            f"Expected 4 MRI channels, but received shape {nii.shape}."
        )

    # Load and resize one modality at a time to keep memory usage low.
    # For a 3D MRI, reuse its one modality in all four model channels.
    resize = Resize(
        spatial_size=INFERENCE_SHAPE,
        mode="trilinear"
    )
    channels = np.empty((4, *INFERENCE_SHAPE), dtype=np.float32)
    input_channels = 1 if len(nii.shape) == 3 else 4
    for channel_index in range(input_channels):
        source = nii.dataobj if input_channels == 1 else nii.dataobj[..., channel_index]
        volume = np.asarray(source, dtype=np.float32)
        volume = np.transpose(volume, (2, 0, 1))[np.newaxis, ...]
        channels[channel_index] = np.asarray(
            resize(normalizer(volume))[0], dtype=np.float32
        )
    if input_channels == 1:
        channels[1:] = channels[0]

    tensor = torch.from_numpy(channels[np.newaxis, ...])

    print("Model input shape:", tensor.shape)

    with torch.inference_mode():

        prediction = inferer(
            inputs=tensor,
            network=model
        )

    probabilities = torch.sigmoid(prediction)

    prediction_mask = probabilities > 0.5

    prediction_mask = prediction_mask[0].cpu().numpy()

    # Convert 3 output channels to BraTS labels
    tumor_mask = np.zeros(
        prediction_mask.shape[1:],
        dtype=np.uint8
    )

    # TC
    tumor_mask[prediction_mask[0]] = 1

    # WT
    tumor_mask[prediction_mask[1]] = 2

    # ET
    tumor_mask[prediction_mask[2]] = 4

    # [D,H,W] -> [H,W,D]
    tumor_mask = np.transpose(
        tumor_mask,
        (1, 2, 0)
    )
    mask_tensor = torch.from_numpy(tumor_mask).float()
    mask_tensor = mask_tensor.unsqueeze(0).unsqueeze(0)

    mask_tensor = torch.nn.functional.interpolate(
        mask_tensor,
        size=original_shape,
        mode="nearest"
    )

    tumor_mask = mask_tensor[0, 0].numpy().astype(np.uint8)
    mask_nii = nib.Nifti1Image(
        tumor_mask,
        original_affine
    )

    OUTPUT_DIR = os.path.join(
        os.path.dirname(__file__),
        "outputs"
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    mask_path = os.path.join(
        OUTPUT_DIR,
        "tumor_mask.nii.gz"
    )

    nib.save(
        mask_nii,
        mask_path
    )

    print("Tumor mask saved:", mask_path)

    return mask_path
