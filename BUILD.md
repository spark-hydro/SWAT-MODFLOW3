# Building SWAT-MODFLOW3

SWAT-MODFLOW3 builds with CMake and a Fortran compiler (gfortran or Intel ifx), on Linux and
Windows. This replaces the old Visual Studio project. The sources are in `src/`
(`swat`, `modflow`, `rt3d`, `smrt`).

## Just want the program?

Download a build from the [Releases page](https://github.com/spark-hydro/SWAT-MODFLOW3/releases):

| File | For |
|---|---|
| `swatmf3-<version>-gnu-win_amd64-Rel.zip` | Windows (gfortran) |
| `swatmf3-<version>-gnu-lin_x86_64-Rel.zip` | Linux (gfortran, static) |
| `swatmf3-<version>-ifx-lin_x86_64-Rel.zip` | Linux (Intel ifx) |

Unzip, then run the executable from inside your model folder (the one with `file.cio`).

## Requirements

- A Fortran compiler: gfortran 13 or newer, or Intel ifx
- CMake 3.22 or newer
- Ninja (the presets use it)
- Python 3, only for the regression test

Install on Arch: `sudo pacman -S gcc-fortran cmake ninja python`
Install on Ubuntu/Debian: `sudo apt install gfortran cmake ninja-build python3`

## Linux, gfortran

Run from the repository folder:

```bash
cmake --preset gfortran_release_linux
cmake --build build/release
```

The executable is `build/release/swatmf3-<version>-gnu-lin_x86_64-Rel`. For a debug build with
bounds and floating-point checks, use `gfortran_debug_linux` and `build/debug`.

Without presets:

```bash
cmake -B build -G Ninja -D CMAKE_Fortran_COMPILER=gfortran -D CMAKE_BUILD_TYPE=Release
cmake --build build
```

## Linux, Intel ifx

```bash
source /opt/intel/oneapi/setvars.sh        # path depends on where oneAPI is installed
cmake --preset ifx_release -B build/ifx_release
cmake --build build/ifx_release
```

`-B build/ifx_release` keeps it separate from a gfortran build. Use `ifx_debug` for Debug.
The Intel runtime is linked statically, so the executable runs on machines without oneAPI.

## Windows, gfortran (MSYS2)

1. Install [MSYS2](https://www.msys2.org) and open the **UCRT64** shell.
2. Install the tools:
   ```bash
   pacman -S mingw-w64-ucrt-x86_64-gcc-fortran mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja
   ```
3. In that shell, go to the repository folder (drive `E:` is `/e/`) and run:
   ```bash
   cmake --preset gfortran_release_windows
   cmake --build build/release
   ```

The executable is `build\release\swatmf3-<version>-gnu-win_amd64-Rel.exe`. The release
workflow builds Windows this way on GitHub; building it locally has not been tested by the
maintainers.

## Running a model

Run the executable from inside the model folder, which must contain `file.cio`,
`swatmf_link.txt` and the SWAT and MODFLOW input files:

For example, with a copy of the example model (a run writes its output files into the folder,
so do not run inside `data/MiddleBosque1000` itself):

```bash
cp -r data/MiddleBosque1000 /tmp/mymodel
cd /tmp/mymodel
/path/to/repo/build/release/swatmf3-*-Rel
```

On Linux, file names are case-sensitive: the names in `file.cio` must match the files exactly.

To see which version you have, without a model:

```bash
swatmf3-<version>-gnu-lin_x86_64-Rel --version
```

(`--version` is available in builds made after v1.2.1.) The same information is printed at
the start of every run.

## Docker

The `Dockerfile` builds SWAT-MODFLOW3 with CMake and gfortran on Ubuntu 24.04 and gives a small
image that runs a model from a mounted folder. Useful for cloud and cluster runs, or when you do
not want to install a compiler. The Docker idea comes from a contribution by Paul van Genuchten
([@pvgenuchten](https://github.com/pvgenuchten), PR #6).

Ready-made images are published with every release on the GitHub Container Registry, so you do
not need to build anything:

```bash
docker pull ghcr.io/spark-hydro/swatmf3:latest          # or a version, e.g. :v1.2.4
docker run --rm ghcr.io/spark-hydro/swatmf3:latest --version
docker run --rm -v /path/to/my_model:/model ghcr.io/spark-hydro/swatmf3:latest
```

To build the image yourself from the source:

```bash
docker build -t swatmf3 --build-arg VERSION=$(git describe --tags --always) .
docker run --rm swatmf3 --version
docker run --rm -v /path/to/my_model:/model swatmf3
```

- `-v /path/to/my_model:/model` attaches your model folder (with `file.cio`); the outputs are written
  back into it. Add `--user "$(id -u):$(id -g)"` so the files belong to you instead of root.
- `VERSION` is only used for the version shown by `--version`; without it the image says `unknown`.

## Testing

`data/MiddleBosque1000` is an example model (one year, 1985) with reference outputs from the
original Intel build. The regression script runs the model on a temporary copy and compares
every number in the outputs with the reference:

```bash
python3 scripts/regress.py build/release/swatmf3-*-Rel data/MiddleBosque1000
```

It ends with `PASSED` or `FAILED`. Differences around 1e-4 or smaller are normal between
compilers (the limit is 1e-3). It also runs through CTest:

```bash
ctest --test-dir build/release
```

The script compares against the output files that are in the folder you give it, so the
check is only independent when those files come from a different, trusted build, as they do
in `data/MiddleBosque1000`.

## Good to know

- The version in the executable name and the startup banner comes from `git describe --tags`
  and is set when CMake configures. After a new commit, run the first `cmake` command again to refresh it.
- Old executables stay in `build/` when the version changes. `regress.py` uses the newest one.
- The gfortran flags (`-std=legacy -fdec -fallow-argument-mismatch`, fixed-line length off) are
  needed for the legacy MODFLOW/SWAT code; warnings are turned off with `-w`. Remove `-w` in
  `CMakeLists.txt` to see them.
- GitHub Actions also builds the Docker image and runs the regression inside it on every pull request.
- GitHub Actions builds with gfortran and ifx and runs the regression on every pull request
  (`.github/workflows/build.yml`). Pushing a tag like `v1.2.5` builds the three downloads above,
  attaches them to a release and publishes the Docker image (`.github/workflows/release.yml`).
