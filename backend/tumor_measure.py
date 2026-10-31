import numpy as np
import nibabel as nib
import os

def measure():
    brain_path = os.path.join(
    os.path.dirname(__file__),
    "outputs",
    "og_brain.nii.gz"
    )

    seg_path = os.path.join(
    os.path.dirname(__file__),
    "outputs",
    "tumor_mask.nii.gz"
    )

    seg_img = nib.load(seg_path)
    brain_img = nib.load(brain_path)

    seg_data = seg_img.get_fdata(dtype = np.float32)
    brain_data = brain_img.get_fdata(dtype = np.float32)

    voxel_count = seg_img.header.get_zooms()[:3]
    voxel_vol = np.prod(voxel_count)

    seg_mask = seg_data > 0
    tumor_voxel_count = np.count_nonzero(seg_mask)
    tumor_vol = (tumor_voxel_count * voxel_vol) / 1000.0

    brain_data = brain_data[..., 0]
    brain_mask = brain_data > 0
    brain_voxel_count = np.sum(brain_mask)
    brain_vol = (brain_voxel_count * voxel_vol) / 1000.0

    ratio = (tumor_vol / brain_vol) * 100.0
    return brain_vol, tumor_vol, ratio
