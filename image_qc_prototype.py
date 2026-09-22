import bioio_bioformats
import numpy as np
from bioio import BioImage
from scipy.optimize import curve_fit
from skimage.transform import resize

from regression_model import *
from regression_model import CrossTalkRegressionModel


def detect_odd_histogram_distribution(image, bins=256, percentile_threshold=99.99):
    # Calculate the histogram of the image
    hist, bin_edges = np.histogram(image, bins=bins, range=(np.min(image), np.max(image)))

    # Calculate the cumulative histogram to find the percentile threshold bin
    cumulative_hist = np.cumsum(hist)
    total_pixels = cumulative_hist[-1]

    # Find the bin that corresponds to the 95th percentile
    threshold_index = np.searchsorted(cumulative_hist, percentile_threshold / 100 * total_pixels)

    # Find the indices of the first non-zero bin
    non_zero_bins = np.where(hist > 0)[0]
    if len(non_zero_bins) == 0:
        # If no non-zero bins are found return zero for all metrics
        return 0, 0

    first_non_zero_bin = non_zero_bins[0]

    # Count zero bins between the first non-zero bin and the threshold bin
    zero_bins = np.sum(hist[first_non_zero_bin:threshold_index] == 0)

    # Calculate the ratio of zero bins to the total number of bins in this range
    total_bins_in_range = threshold_index - first_non_zero_bin
    zero_bin_ratio = zero_bins / total_bins_in_range if total_bins_in_range > 0 else 0

    return zero_bins, zero_bin_ratio


def flat_plane(coords, p0, p1, p2):
    # Unpack the coordinates
    x, y = coords
    # Linear plane model (1st order polynomial)
    return p0 * x + p1 * y + p2


def estimate_background_flat_plane_deviation(image_3d, foreground_percentile=90):
    depth, height, width = image_3d.shape
    
    # Initialise array to store background estimates for each slice
    background_3d = np.zeros_like(image_3d, dtype=np.float64)
    deviations = []

    for z in range(depth):
        # Process each 2D slice independently
        image = image_3d[z, :, :].astype(np.float64)

        # Generate grid of coordinates
        y = np.arange(height)
        x = np.arange(width)
        xx, yy = np.meshgrid(x, y)

        # Only fit to the dimmer pixels — excludes bright objects from skewing the plane
        cutoff = np.percentile(image, foreground_percentile)
        mask = image <= cutoff

        # Fit a flat plane to the current slice
        p_initial = np.zeros(3)
        params, _ = curve_fit(flat_plane, (xx[mask], yy[mask]), image[mask], p0=p_initial)

        # Calculate fitted background for the current slice
        background_slice = flat_plane((xx, yy), *params).reshape(image.shape)
        # Store the fitted background slice in the 3D array
        background_3d[z, :, :] = background_slice

        # Only measure deviation from the flat planeon the same background pixels used for the fit
        deviation = np.abs(image[mask] - background_slice[mask])
        deviations.append(np.std(deviation))

    # Calculate the overall non-uniformity metric as the mean of deviations across all slices
    non_uniformity = np.mean(deviations)
    non_uniformity_pct = non_uniformity / np.mean(background_3d) * 100  
    
    return background_3d, non_uniformity, non_uniformity_pct


def check_bit_depth(image):
    # Determine the bit depth of the image
    bit_depth = image.dtype.itemsize * 8  # itemsize gives the number of bytes, so multiply by 8 to get bits

    if bit_depth <= 8:
        print(f"Warning: The image has a low bit depth of {bit_depth}-bits, which may limit image quality.")
    else:
        print(f"The image has a bit depth of {bit_depth}-bits, which is adequate for most purposes.")

    return bit_depth


def calculate_dynamic_range(image, low_percentile=0.1, high_percentile=99.9):
    min_intensity = np.percentile(image, low_percentile)
    max_intensity = np.percentile(image, high_percentile)

    # Determine the maximum possible range based on the image's data type
    dtype_max = np.iinfo(image.dtype).max

    # Normalised dynamic range
    dynamic_range_percentage = round((max_intensity - min_intensity) * 100 / dtype_max, 2)
    return dynamic_range_percentage


def calculate_saturation_percentage(image):
    # Determine the minimum and maximum possible values based on the image's data type 
    dtype_min = np.iinfo(image.dtype).min
    dtype_max = np.iinfo(image.dtype).max

    # Count the number of saturated pixels
    saturated_pixels = np.sum((image == dtype_min) | (image == dtype_max))

    # Calculate the total number of pixels
    total_pixels = image.size

    # Calculate the percentage of saturated pixels
    saturation_percentage = round(saturated_pixels / total_pixels * 100, 2)

    return saturation_percentage


img = BioImage('./inputs/Experiment-09.ome.tiff', reader=bioio_bioformats.Reader)

for c in range(img.dims.C):
    channel = img.get_image_data('CZYX', C=c)
    channel = channel[0, :, :]
    check_bit_depth(channel)
    dr = calculate_dynamic_range(channel)
    print(f'Dynamic range of Channel {c} is {dr}%')
    saturation_percentage = calculate_saturation_percentage(channel)
    print(f'Relative saturation of Channel {c} is {saturation_percentage}%')
    background_3d, non_uniformity, non_uniformity_pct = estimate_background_flat_plane_deviation(channel)
    print(f"Non-uniformity (Flat Plane Deviation) for Channel {c} is {non_uniformity: .2f} ({non_uniformity_pct:.2f}%)")
    zero_bins, zero_bin_ratio = detect_odd_histogram_distribution(channel)
    print(f"Number of zero bins: {zero_bins}")
    print(f"Ratio of zero bins: {zero_bin_ratio:.4f}")

