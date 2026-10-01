[![Release](https://img.shields.io/github/v/release/spark-hydro/SWAT-MODFLOW3?style=flat-square)](https://github.com/spark-hydro/SWAT-MODFLOW3/releases)
[![Build](https://img.shields.io/github/actions/workflow/status/spark-hydro/SWAT-MODFLOW3/build.yml?branch=main&style=flat-square&label=build%20%2B%20regression%20test)](https://github.com/spark-hydro/SWAT-MODFLOW3/actions/workflows/build.yml)
[![Downloads](https://img.shields.io/github/downloads/spark-hydro/SWAT-MODFLOW3/total?style=flat-square)](https://github.com/spark-hydro/SWAT-MODFLOW3/releases)
[![License](https://img.shields.io/github/license/spark-hydro/SWAT-MODFLOW3?style=flat-square)](LICENSE)

# SWAT-MODFLOW3

SWAT-MODFLOW3 couples the watershed model **SWAT2012** (Rev. 636) with the groundwater models
**MODFLOW-NWT** and **RT3D** in one executable. SWAT calculates land-surface and channel processes
by HRU and subbasin and passes recharge to MODFLOW. MODFLOW calculates groundwater heads and the
exchange with the river network, and passes it back to SWAT.

The source is in `src/`: `swat` (SWAT2012), `modflow` (MODFLOW-NWT), `rt3d` (RT3D) and `smrt`
(the code that links them).

## Download

Ready-to-run executables are on the
[Releases page](https://github.com/spark-hydro/SWAT-MODFLOW3/releases):

| File | For |
|---|---|
| `swatmf3-<version>-gnu-win_amd64-Rel.zip` | Windows |
| `swatmf3-<version>-gnu-lin_x86_64-Rel.zip` | Linux (gfortran, static) |
| `swatmf3-<version>-ifx-lin_x86_64-Rel.zip` | Linux (Intel ifx) |

## Quick start

1. Unzip the executable for your system.
2. Run it from inside your model folder, the one that contains `file.cio` and `swatmf_link.txt`:

   ```bash
   cd my_model_folder
   /path/to/swatmf3-<version>-gnu-lin_x86_64-Rel
   ```

3. To see which version you have (no model needed):

   ```bash
   swatmf3-<version>-gnu-lin_x86_64-Rel --version
   ```

   `--version` is available from v1.2.2.

On Linux, file names are case-sensitive: the names written in `file.cio` must match the files exactly.

## Example model

`data/MiddleBosque1000` is the Middle Bosque SWAT-MODFLOW model (1000 m MODFLOW grid, one year,
1985) with reference outputs. Copy it before running, because a run writes its outputs into the
model folder:

```bash
cp -r data/MiddleBosque1000 /tmp/mymodel
cd /tmp/mymodel
/path/to/swatmf3-<version>-gnu-lin_x86_64-Rel
```

## Build from source

See **[BUILD.md](BUILD.md)** for requirements and step-by-step instructions for Linux
(gfortran, Intel ifx) and Windows (gfortran). In short, on Linux:

```bash
cmake --preset gfortran_release_linux
cmake --build build/release
```

## Testing

`scripts/regress.py` runs the example model and compares every number in the outputs with the
reference outputs. GitHub Actions does this for gfortran and ifx on every pull request, and builds
the downloads above when a version tag such as `v1.2.2` is pushed. See [BUILD.md](BUILD.md).

## Credits and citation

The SWAT-MODFLOW-RT3D linking code in `src/smrt` was written at Colorado State University; see the
author notes at the top of the source files. SWAT2012, MODFLOW-NWT and RT3D are the work of their
respective developers.

## License

Released under the GNU Lesser General Public License v2.1, the same license as SWAT+. See
[LICENSE](LICENSE).

<!-- TODO (maintainer): add the references to cite for SWAT-MODFLOW and the maintainers. -->
