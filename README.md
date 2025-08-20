[![DOI](https://zenodo.org/badge/931444556.svg)](https://doi.org/10.5281/zenodo.16910935)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

# napari-epyseg

Plugin to run [EpySeg](https://github.com/baigouy/EPySeg) directly in [Napari](https://napari.org/stable/).
Can handle temporal data (movie) or single time point (image).

## Installation

To install it from Napari, go into the `Plugins` menu, select `Install/Uninstall Plugins..` and look for napari-epyseg in the plugins list.

To install it directly outside of napari, create/reuse and activate a python environement, e.g `epyseg_env` and install it with `pip`:
```
pip install napari-epyseg
```

> [!IMPORTANT]
> `epyseg` is compatible until python 3.10 (included), but not for versions of python above. Thus, `napari-epyseg` is also compatible with python versions until 3.10

## Usage

In Napari, go to `Plugins>napari-epyseg` to start it.
It will open an interface in the left part of the main window.

![interface_image](./imgs/napepy-interface.png)

You must select the layer (image or movie, single color channel) on which to run `EpySeg`.
For this, in the `Pick an Image` parameter, select the corresponding layer (you should open the image/movie independantly of the plugin).

To run `EpySeg` with default parameters, press directly `Segment` once you have selected the image.
When processing is finished, a new layer called `Segmentation` will be added in the right panel of the interface.
You can save the result with the `Save segmentation` button that appears on the left part of the interface. 
Choose where to save the file and the file name with the `Segmentation filename` parameter, and click the button to save it.

![results_image](./imgs/result.png)

## Remark

This plugin was tested on python 3.10, with epyseg version 0.1.52, napari version 0.4.19, tensorflow 2.14

## Troubleshooting

* On Linux Ubuntu, python 3.10, epyseg don't run with tensorflow 2.15 and output the error: `DNN not found`. Downgrading tensorflow to 2.14 worked.
* `tifffile versions` compability: some versions of tifffile where not compatible with epyseg, but recent versions are now fine. `tifffile <= 2021.11.2` are fine and `tifffile==2025.1.10` also.

## License

This plugin is distributed under the BDS-3 license.
If you use this plugin, please cite [Epyseg](https://journals.biologists.com/dev/article/147/24/dev194589/226105/EPySeg-a-coding-free-solution-for-automated) and the plugin with its doi: [![DOI](https://zenodo.org/badge/931444556.svg)](https://doi.org/10.5281/zenodo.16910935)
