[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/FrancisCrickInstitute/py-bioimage-qc/main?urlpath=%2Fdoc%2Ftree%2Fimage_qc_prototype_notebook.ipynb) [![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/release/python-3140/) [![pixi](https://img.shields.io/badge/pixi-enabled-00a1e9.svg?logo=pixi)](https://pixi.sh) ![Commit activity](https://img.shields.io/github/commit-activity/y/FrancisCrickInstitute/py-bioimage-qc?style=plastic) ![GitHub](https://img.shields.io/github/license/FrancisCrickInstitute/py-bioimage-qc?color=green&style=plastic)

# FlagQC

## Overview

This notebook provides a set of simple quality control analyses for microscopy images, allowing users to flag issues such as saturation, crosstalk or inappropriate bit depth.

**QC checks implemented:**
- Histogram oddities
- Background flatness
- Bit depth assessment
- Dynamic range calculation
- Saturation percentage
- Crosstalk estimation

⚠️ **WORK IN PROGRESS** The code is based on a prototype script.

> Crosstalk estimation loads a trained regression model from
> [CrosstalkPy](https://github.com/FrancisCrickInstitute/CrosstalkPy) at runtime;
> the first use of that check requires network access.

## Try It!

You can run the notebook now on Binder by clicking [here](https://mybinder.org/v2/gh/FrancisCrickInstitute/py-bioimage-qc/main?urlpath=%2Fdoc%2Ftree%2Fimage_qc_prototype_notebook.ipynb).

## Running Locally

```bash
pip install -r requirements.txt
jupyter lab image_qc_prototype_notebook.ipynb
```

The crosstalk check downloads a ~51 MB trained model on first use and caches it
locally, so network access is required the first time that check is run.

## Acknowledgements & Contact

This notebook was developed as part of the **FlagQC** project at the Crick Advanced Light Microscopy (_CALM_) department in the Francis Crick Institute.  
Its goal is to provide an accessible, practical toolkit for basic quality control of bioimaging data.

**Authors:**  
- [Dave Barry](https://www.crick.ac.uk/research/find-a-researcher/david-barry)* (david.barry@crick.ac.uk) 
- [Sara Salgueiro Torres](https://www.crick.ac.uk/research/find-a-researcher/sara-salgueiro-torres)* (sara.salgueirotorres@crick.ac.uk)
- [Stefania Marcotti](https://www.crick.ac.uk/research/find-a-researcher/stefania-marcotti)
- [Cameron Shand](https://www.crick.ac.uk/research/find-a-researcher/cameron-shand)
- [Alicja Skórkowska](https://portalwiedzy.cm-uj.krakow.pl/info/author/UJCM22b401960ddf4ee59b30ec6d96d36316?r=publication&ps=20&title=Profil%2Bosoby%2B%25E2%2580%2593%2BAlicja%2BSk%25C3%25B3rkowska%2B%25E2%2580%2593%2BUniwersytet%2BJagiello%25C5%2584ski%2B%25E2%2580%2593%2BCollegium%2BMedicum&lang=pl)

*Authors for correspondence


## Feedback & Contributions: 
We welcome your suggestions, feedback, and pull requests!  
For questions or to report issues, please open an issue [here](https://github.com/FrancisCrickInstitute/py-bioimage-qc/issues) or contact the authors directly.

---
*CALM, Francis Crick Institute <br>*
1 Midland Rd, London NW1 1AT <br>
2025
