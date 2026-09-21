# AGENTS.md

Guidance for AI agents working in the **FlagQC** repository.

## What this project is

FlagQC is a quality-control toolkit for microscopy images (bioimaging). It flags
issues such as saturation, crosstalk, bit depth problems, background
non-uniformity, and odd histogram distributions. It is a research prototype,
distributed primarily as Jupyter notebooks, not a packaged library.

It was developed by the Crick Advanced Light Microscopy (CALM) group at the
Francis Crick Institute. README and repo still reference the upstream name
`py-bioimage-qc` / `FrancisCrickInstitute/py-bioimage-qc` (the project was
renamed to FlagQC in commit `ed02115`).

## Layout

- `image_qc_prototype_notebook.ipynb` — the **primary deliverable**. Contains the
  QC functions (duplicated inline) plus the crosstalk model workflow. This is the
  canonical implementation; it is the file the Binder badge in the README launches.
- `image_qc_prototype.py` — an older standalone script version of the same QC
  functions. **Not kept in sync** with the notebook (see "Gotchas").
- `regression_model.py` — the `CrossTalkRegressionModel` PyTorch module
  (imported by the notebook).
- `read_images_with_bioio.ipynb` — a minimal example notebook demonstrating
  `bioio` image loading.
- `inputs/` — example `.ome.tiff` microscopy data, tracked with Git LFS.
- `requirements.txt` — pinned-ish dependency list (unversioned).

## Commands

There is **no build system, test suite, linting config, CI, packaging file
(`setup.py`/`pyproject.toml`), or Makefile**. No `py.test`/`pytest`/unit tests
exist.

To run the code:

```bash
pip install -r requirements.txt
jupyter lab image_qc_prototype_notebook.ipynb   # or open in Binder via README
```

The standalone script is run directly (note the hardcoded input path):

```bash
python image_qc_prototype.py
```

Verify code with the Python version noted in the README badge (Python 3.13).

## Model dependency (crosstalk)

The crosstalk weights are **not in this repo**. The model is trained and
produced by a separate repository,
[`FrancisCrickInstitute/CrosstalkPy`](https://github.com/FrancisCrickInstitute/CrosstalkPy),
which is currently being refactored to align its model format with
[`djpbarry/KimmelNET`](https://github.com/djpbarry/KimmelNET).

Current state and direction:

- Today the notebook's `estimate_crosstalk` hardcodes a specific class
  (`CrossTalkRegressionModel(initial_filters=128, num_conv_blocks=6)`) and
  `load_state_dict`s a `.pth` path that does not exist
  (`./crosstalk_model/crosstalk_regression_model_trained_2025-12-15_18-22-01_256_0.0005.pth`).
  This is fragile: it couples FlagQC to CrosstalkPy's internal class name and
  constructor args, and will break if the refactor changes them.
- The intended fix is to load the **TorchScript `.pt` bundle** (architecture
  plus weights in one artifact) via `torch.jit.load(...)`, instead of
  `load_state_dict` on a re-constructed class. This decouples FlagQC from the
  model's internals.
- The exact `.pt` filename, release location, and I/O contract are not yet
  finalised because the refactor is in progress. The current input contract is
  `[batch, 2, 256, 256]` (channel 0 = "mixed", channel 1 = "source"), output
  a scalar alpha in `[0, 1]`; verify this has not changed before wiring up the
  new loader.

Do **not** hand-write the model class or its constructor args here; obtain the
trained artifact from CrosstalkPy and load it as a bundle. The decision on
whether to vendor the artifact into this repo or fetch it at runtime is still
open.

## Requirements / dependencies

From `requirements.txt`: `bioio`, `bioio-ome-tiff`, `numpy`, `scipy`, `jupyter`,
`torch`, `scikit-image`.

The code also imports `bioio_bioformats` (in `image_qc_prototype.py` and
`read_images_with_bioio.ipynb`), which is **not** listed in `requirements.txt`.
The notebook itself imports `bioio_ome_tiff` instead.

## Architecture and data flow

Image I/O is done via [`bioio`](https://allencellmodeling.github.io/bioio/)
(`BioImage`). Images are read with an explicit format-specific reader, e.g.
`bioio_ome_tiff.Reader` or `bioio_bioformats.Reader`.

`BioImage` exposes dimension names via `img.dims` (e.g. `CZYX`). Data is pulled
into NumPy arrays using `img.get_image_data('CZYX', C=c)` — note the selection
**before** the string, i.e. `get_image_data(..., C=c)` gives a `(Z, Y, X)`
stack for channel `c`, which the code then indexes with `[0, :, :]` to get a
single `(Y, X)` slice.

Standard per-channel QC pipeline (in the notebook and script):

1. `check_bit_depth` — derives bit depth from `dtype.itemsize * 8`.
2. `calculate_dynamic_range` — `(max - min) / dtype_max`, assumes integer dtype.
3. `calculate_saturation_percentage` — fraction of pixels at dtype min/max.
4. `detect_odd_histogram_distribution` — zero-bin ratio in the histogram.
5. Crosstalk estimation (notebook only) — pairwise per channel via the PyTorch
   regression model.

The crosstalk model (`CrossTalkRegressionModel` in `regression_model.py`) is a
convolutional network that takes two normalized 256×256 inputs stacked into a
`(1, 2, 256, 256)` tensor and outputs a scalar crosstalk fraction. Inputs are
normalized to `[0,1]` and resized to 256×256 in `crosstalk_test_transforms_fn`.

## Conventions and style

- Plain script/notebook Python; no package structure, no `__init__.py`, no type
  hints.
- Functions are defined at module top level in both the `.py` file and inline in
  the notebook.
- Numpy arrays are indexed with `(depth, height, width)` / `(Z, Y, X)` ordering
  throughout.
- QC functions accept a single 2D NumPy array argument (named `image`) and print
  results rather than returning structured output (they mix `print` + `return`).

## Gotchas and non-obvious points

- **Code is duplicated and divergent.** The QC functions exist both in
  `image_qc_prototype.py` and inline in `image_qc_prototype_notebook.ipynb`, and
  they are not identical. For example, `calculate_dynamic_range` differs between
  `image_qc_prototype.py` (uses `(max-min)/dtype_max`) and
  `read_images_with_bioio.ipynb` (uses `max/min`). Treat the notebook as
  canonical; do not assume the `.py` file matches it.
- **Missing model weights.** `estimate_crosstalk` in the notebook loads a
  `.pth` file from `./crosstalk_model/`, but that directory is absent from the
  repo. The crosstalk step will fail at runtime until a trained weights file is
  provided.
- **Hardcoded input paths.** Both the script (`./inputs/Experiment-09.ome.tiff`)
  and the notebook (`./inputs/Experiment-09-test.ome.tiff`) reference specific
  files under `inputs/`.
- **Git LFS.** `.tiff` files are tracked with Git LFS (see `.gitattributes`).
  Checked-out example images require LFS to be initialized; the repo only
  stores LFS pointers otherwise.
- **`requirements.txt` is incomplete.** `bioio_bioformats` is imported but
  missing from `requirements.txt`. The notebook uses `bioio_ome_tiff` instead.
- **Unused background-flatness code.** `estimate_background_flat_plane_deviation`
  is defined but its call sites are commented out in both the script and the
  notebook. It also assumes 3D `(depth, height, width)` input, unlike the other
  2D functions.
- **`calculate_dynamic_range` assumes an integer dtype.** It calls
  `np.iinfo(image.dtype)`, which fails for float arrays.

## Testing

No automated tests exist. Manually confirm behavior by running the notebook/script
and inspecting printed output. There is nothing to lint or type-check.
