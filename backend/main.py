import os
import tempfile

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from inference import segment_brain
import re
import nibabel as nib
import numpy as np
import shutil
from research_sources import research_topic


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_treatment_mask(treatment, reduction_percent):
    original_path = os.path.join(
        os.path.dirname(__file__),
        "outputs",
        "tumor_mask.nii.gz"
    )

    nii = nib.load(original_path)
    mask = nii.get_fdata().astype(np.uint8)

    tumor_coords = np.argwhere(mask > 0)

    if len(tumor_coords) == 0:
        raise ValueError("No tumor was found in the segmentation.")

    # Convert percentage reduction in volume
    # into a 3D linear scaling factor.
    remaining_volume = 1 - (reduction_percent / 100)

    scale = remaining_volume ** (1 / 3)

    # Center of the tumor.
    center = tumor_coords.mean(axis=0)

    # Move tumor voxels toward the center.
    scaled_coords = (
        center + (tumor_coords - center) * scale
    )

    scaled_coords = np.rint(scaled_coords).astype(int)

    # Keep coordinates inside the MRI dimensions.
    for axis in range(3):
        scaled_coords[:, axis] = np.clip(
            scaled_coords[:, axis],
            0,
            mask.shape[axis] - 1
        )

    treatment_mask = np.zeros_like(mask)

    # Preserve the tumor's label.
    labels = mask[
        tumor_coords[:, 0],
        tumor_coords[:, 1],
        tumor_coords[:, 2]
    ]

    treatment_mask[
        scaled_coords[:, 0],
        scaled_coords[:, 1],
        scaled_coords[:, 2]
    ] = labels

    filename_match = {
        "3D-CRT": "CRT.nii.gz",
        "Intensity-modulated radiation therapy": "IMRT_mask.nii.gz",
        "Proton beams": "proton_mask.nii.gz",
        "Stereotactic radiosurgery ": "stereo_mask.nii.gz",
        "Radiotherapy": "radio_mask.nii.gz"
    }
    filename_final = filename_match.get(treatment)

    output_path = os.path.join(
        os.path.dirname(__file__),
        "outputs",
        filename_final
    )

    output_nii = nib.Nifti1Image(
        treatment_mask,
        nii.affine
    )
    nib.save(output_nii, output_path)
    return output_path

@app.get("/")
def root():
    return {
        "message": "NeuroHeist backend is running"
    }

@app.post("/upload")
async def upload_scan(
    file: UploadFile = File(...)
):
    # Make sure the uploaded file is NIfTI.
    filename = file.filename.lower()

    if not (
        filename.endswith(".nii")
        or filename.endswith(".nii.gz")
    ):
        return {
            "error": "Only .nii and .nii.gz files are supported."
        }

    # Save uploaded file temporarily.
    suffix = ".nii.gz" if filename.endswith(".nii.gz") else ".nii"

    input_file = tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False
    )

    input_path = input_file.name

    try:
        contents = await file.read()

        input_file.write(contents)
        input_file.close()
        OUTPUT_DIR = os.path.join(
            os.path.dirname(__file__),
            "outputs"
        )
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # Remove treatment masks from the previous scan.
        old_masks = [
            "CRT.nii.gz",
            "IMRT_mask.nii.gz",
            "proton_mask.nii.gz",
            "stereo_mask.nii.gz",
            "radio_mask.nii.gz"
        ]

        for filename in old_masks:
            old_path = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(old_path):
            os.remove(old_path)
            
        og_path = os.path.join(
            OUTPUT_DIR,
            "og_brain.nii.gz"
        )
        shutil.copyfile(input_path, og_path)

        # Run the actual AI segmentation.
        mask_path = segment_brain(input_path)

        return {
            "message": "Scan segmented successfully.",
            "tumor_mask": f"/tumor-mask/{os.path.basename(mask_path)}"
        }

    except Exception as error:
        input_file.close()

        print("SEGMENTATION ERROR:")
        print(error)

        return {
            "error": str(error)
        }


@app.get("/tumor-mask/{filename}")
def get_tumor_mask(filename: str):
    path = os.path.join(
        os.path.dirname(__file__),
        "outputs",
        filename
    )
    if not os.path.exists(path):
        return {
            "error": "Tumor mask not found."
        }

    return FileResponse(
        path,
        media_type="application/gzip",
        filename=filename
    )
@app.get("/treatment-masks")
def get_treatment_masks():

    output_dir = os.path.join(
        os.path.dirname(__file__),
        "outputs"
    )

    filename_match = {
        "3D-CRT": "CRT.nii.gz",
        "Intensity-modulated radiation therapy": "IMRT_mask.nii.gz",
        "Proton beams": "proton_mask.nii.gz",
        "Stereotactic radiosurgery": "stereo_mask.nii.gz",
        "Radiotherapy": "radio_mask.nii.gz"
    }

    available_masks = []

    for treatment, filename in filename_match.items():

        file_path = os.path.join(output_dir, filename)

        if os.path.exists(file_path):
            available_masks.append({
                "treatment": treatment,
                "filename": filename,
                "maskUrl": f"/tumor-mask/{filename}"
            })

    return {
        "masks": available_masks
    }

@app.post("/simulate")
async def simulate_treatment(data: dict):
    treatment = data.get("treatment")

    if not treatment:
        return {
            "error": "No treatment was provided."
        }

    try:
        print("Treatment selected:", treatment)

        # Research the exact treatment selected by the user.
        gemini_answer = research_topic(treatment)

        print("Gemini response:", gemini_answer)

        reduction = gemini_answer.tumor_factor

        # Gemini may return either:
        # 0.38  -> 38%
        # 38    -> 38%
        if 0 <= reduction <= 1:
            reduction_percent = reduction * 100
        else:
            reduction_percent = reduction

        reduction_percent = max(
            0,
            min(100, reduction_percent)
        )

        # Create a new tumor mask with ONLY the tumor reduced.
        mask_path = create_treatment_mask(
            treatment,
            reduction_percent
        )

        return {
            "treatment": treatment,
            "reductionPercent": reduction_percent,
            "summary": (
                f"Research-based simulation for {treatment} "
                f"predicts approximately "
                f"{reduction_percent:.1f}% tumor volume reduction."
            ),
            "maskUrl": (
                "/tumor-mask/"
                + os.path.basename(mask_path)
                + f"?v={int(reduction_percent * 1000)}"
            )
        }

    except Exception as error:
        print("TREATMENT SIMULATION ERROR:")
        print(error)

        return {
            "error": str(error)
        }