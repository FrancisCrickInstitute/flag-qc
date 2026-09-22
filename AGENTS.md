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
- `regression_model.py` — a local copy of the `CrossTalkRegressionModel`
  PyTorch module. **No longer imported by the notebook** (see "Model
  dependency"); kept for reference only.
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

The crosstalk model is trained and produced by a separate repository,
[`FrancisCrickInstitute/CrosstalkPy`](https://github.com/FrancisCrickInstitute/CrosstalkPy).
It is **not vendored** into this repo; FlagQC loads it from CrosstalkPy's
release `v1.0.0` at runtime.

- The notebook's `estimate_crosstalk` now loads the **TorchScript `.pt` bundle**
  (architecture plus weights in one artifact) via `torch.jit.load(...)`,
  decoupling FlagQC from CrosstalkPy's internal class names and constructor
  args.
- The artifact is
  `crosstalk_regression_model_v1.0.0_2026-09-22_14-42-47_128_0.0005.pt`
  (~51 MB), fetched from the release URL and cached next to the notebook on
  first use. `load_crosstalk_model` verifies its SHA256 checksum
  (`5f29b254b3ead78101d3f896fc69ecfae205d5695ded0a9558341c2a1e4ef8fb`) after
  download and fails loudly on mismatch.
- I/O contract: input `[batch, 2, 256, 256]` float tensor (channel 0 = "mixed",
  channel 1 = "source", min-max normalized), output `[batch, 1]` scalar alpha
  in `[0, 1]`. Batch size is dynamic. The model architecture is the
  single-branch `AdvancedRegressionModel` (`initial_filters=128`,
  `num_conv_blocks=6`).

If the release or contract changes (filename, URL, checksum, or I/O shape),
update `CROSSTALK_MODEL_URL`, `CROSSTALK_MODEL_FILENAME`, and
`CROSSTALK_MODEL_SHA256` in the notebook's `estimate_crosstalk` cell to match.

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

The crosstalk model (loaded as a TorchScript `.pt` bundle from CrosstalkPy, see
"Model dependency") is a convolutional network that takes two normalized 256×256
inputs stacked into a `(1, 2, 256, 256)` tensor and outputs a scalar crosstalk
fraction. Inputs are normalized to `[0,1]` and resized to 256×256 in
`crosstalk_test_transforms_fn`. The local `regression_model.py` copy is no
longer used at runtime.

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
- **Model weights are fetched at runtime.** `estimate_crosstalk` downloads the
  `.pt` bundle from CrosstalkPy's release on first use and caches it locally.
  The first run requires network access; the cached file also needs Git LFS if
  you want to commit it (it is not tracked by default).
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
