import os
import platform
import shutil
import struct
import subprocess
import sys
import sysconfig

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

CONFIG_VERSION = open("upstream-quickjs/VERSION").read().strip()

_quickjs = Extension(
    "_quickjs",
    sources=[
        "module.c",
        "upstream-quickjs/cutils.c",
        "upstream-quickjs/libbf.c",
        "upstream-quickjs/libregexp.c",
        "upstream-quickjs/libunicode.c",
        "upstream-quickjs/quickjs.c",
    ],
    define_macros=[("CONFIG_VERSION", f'"{CONFIG_VERSION}"'), ("CONFIG_BIGNUM", None)],
)


class ZigCCBuildExt(build_ext):
    """Custom build_ext that uses zig cc as the C compiler."""

    def _find_zig(self):
        zig = shutil.which("zig")
        if zig:
            return zig
        # Fall back to looking inside the ziglang package directory
        try:
            import ziglang

            zig_path = os.path.join(
                os.path.dirname(ziglang.__file__),
                "zig.exe" if sys.platform == "win32" else "zig",
            )
            if os.path.exists(zig_path):
                return zig_path
        except ImportError:
            pass
        raise RuntimeError(
            "Could not find zig compiler. Install the 'ziglang' package."
        )

    def _get_zig_target(self):
        if sys.platform == "win32":
            # Use gnu target so zig uses its bundled MinGW headers —
            # no Windows SDK or MSVC install required.
            machine = platform.machine().lower()
            is_64bit = struct.calcsize("P") == 8
            if machine in ("arm64", "aarch64"):
                return "aarch64-windows-gnu"
            elif is_64bit:
                return "x86_64-windows-gnu"
            else:
                return "x86-windows-gnu"
        return None

    def build_extension(self, ext):
        zig = self._find_zig()

        ext_path = self.get_ext_fullpath(ext.name)
        os.makedirs(os.path.dirname(ext_path), exist_ok=True)

        # --- Include dirs ---
        include_dirs = list(ext.include_dirs or [])
        py_include = sysconfig.get_path("include")
        if py_include:
            include_dirs.append(py_include)
        plat_include = sysconfig.get_path("platinclude")
        if plat_include and plat_include not in include_dirs:
            include_dirs.append(plat_include)

        # --- Compile flags ---
        compile_flags = ["-O2"]
        for d in include_dirs:
            compile_flags.extend(["-I", d])
        for macro, value in ext.define_macros or []:
            if value is not None:
                compile_flags.append(f"-D{macro}={value}")
            else:
                compile_flags.append(f"-D{macro}")
        compile_flags.extend(ext.extra_compile_args or [])

        zig_target = self._get_zig_target()
        if zig_target:
            compile_flags.extend(["-target", zig_target])
        if sys.platform != "win32":
            compile_flags.append("-fPIC")

        # --- Compile ---
        obj_dir = os.path.join(self.build_temp, ext.name)
        os.makedirs(obj_dir, exist_ok=True)

        objects = []
        for source in ext.sources:
            obj_name = os.path.splitext(os.path.basename(source))[0] + ".obj"
            obj_path = os.path.join(obj_dir, obj_name)
            cmd = [zig, "cc", "-c", source, "-o", obj_path] + compile_flags
            print(f"  zig cc: compiling {source}")
            subprocess.check_call(cmd)
            objects.append(obj_path)

        # --- Link ---
        link_cmd = [zig, "cc", "-shared"] + objects + ["-o", ext_path]
        if zig_target:
            link_cmd.extend(["-target", zig_target])
        if sys.platform == "win32":
            # Link against Python import library
            for prefix in (sys.prefix, sys.base_prefix):
                lib = os.path.join(
                    prefix,
                    "libs",
                    f"python{sys.version_info.major}{sys.version_info.minor}.lib",
                )
                if os.path.exists(lib):
                    link_cmd.append(lib)
                    break
            else:
                raise RuntimeError("Could not find Python import library (python3X.lib)")
        elif sys.platform == "darwin":
            link_cmd.extend(["-undefined", "dynamic_lookup"])
        print(f"  zig cc: linking {ext_path}")
        subprocess.check_call(link_cmd)


setup(
    ext_modules=[_quickjs],
    cmdclass={"build_ext": ZigCCBuildExt},
)
