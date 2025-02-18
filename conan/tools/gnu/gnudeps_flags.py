"""
    This is a helper class which offers a lot of useful methods and attributes
"""
# FIXME: only for tools.gnu? perhaps it should be a global module
from conan.tools.microsoft.subsystems import subsystem_path, deduce_subsystem


class GnuDepsFlags(object):

    def __init__(self, conanfile, cpp_info):
        self._conanfile = conanfile
        self._subsystem = deduce_subsystem(conanfile, scope="build")

        # From cppinfo, calculated flags
        self.include_paths = self._format_include_paths(cpp_info.includedirs)
        self.lib_paths = self._format_library_paths(cpp_info.libdirs)
        self.defines = self._format_defines(cpp_info.defines)
        self.libs = self._format_libraries(cpp_info.libs)
        self.frameworks = self._format_frameworks(cpp_info.frameworks)
        self.framework_paths = self._format_framework_paths(cpp_info.frameworkdirs)
        self.sysroot = self._sysroot_flag(cpp_info.sysroot)

        # Direct flags
        self.cxxflags = cpp_info.cxxflags or []
        self.cflags = cpp_info.cflags or []
        self.sharedlinkflags = cpp_info.sharedlinkflags or []
        self.exelinkflags = cpp_info.exelinkflags or []
        self.system_libs = cpp_info.system_libs or []

        # Not used?
        # self.bin_paths
        # self.build_paths
        # self.src_paths

    _GCC_LIKE = ['clang', 'apple-clang', 'gcc']

    @staticmethod
    def _format_defines(defines):
        return ["-D%s" % define for define in defines] if defines else []

    def _format_frameworks(self, frameworks):
        """
        returns an appropriate compiler flags to link with Apple Frameworks
        or an empty array, if Apple Frameworks aren't supported by the given compiler
        """
        if not frameworks:
            return []
        # FIXME: Missing support for subsystems
        compiler = self._conanfile.settings.get_safe("compiler")
        compiler_base = self._conanfile.settings.get_safe("compiler.base")
        if (str(compiler) not in self._GCC_LIKE) and (str(compiler_base) not in self._GCC_LIKE):
            return []
        return ["-framework %s" % framework for framework in frameworks]

    def _format_framework_paths(self, framework_paths):
        """
        returns an appropriate compiler flags to specify Apple Frameworks search paths
        or an empty array, if Apple Frameworks aren't supported by the given compiler
        """
        if not framework_paths:
            return []
        compiler = self._conanfile.settings.get_safe("compiler")
        compiler_base = self._conanfile.settings.get_safe("compiler.base")
        if (str(compiler) not in self._GCC_LIKE) and (str(compiler_base) not in self._GCC_LIKE):
            return []
        return ["-F %s" % self._adjust_path(framework_path) for framework_path in
                framework_paths]

    def _sysroot_flag(self, sysroot):
        # FIXME: Missing support for subsystems
        if self._base_compiler != 'Visual Studio' and sysroot:
            sysroot = self._adjust_path(sysroot)
            return '--sysroot=%s' % sysroot
        return ""

    def _format_include_paths(self, include_paths):
        if not include_paths:
            return []
        # FIXME: Missing support for subsystems
        return ["-I%s" % (self._adjust_path(include_path))
                for include_path in include_paths if include_path]

    def _format_library_paths(self, library_paths):
        if not library_paths:
            return []
        # FIXME: Missing support for subsystems
        pattern = "-LIBPATH:%s" if self._base_compiler == 'Visual Studio' else "-L%s"
        return [pattern % self._adjust_path(library_path)
                for library_path in library_paths if library_path]

    def _format_libraries(self, libraries):
        if not libraries:
            return []

        result = []
        compiler = self._conanfile.settings.get_safe("compiler")
        compiler_base = self._conanfile.settings.get_safe("compiler.base")
        for library in libraries:
            if str(compiler) == 'Visual Studio' or str(compiler_base) == 'Visual Studio':
                if not library.endswith(".lib"):
                    library += ".lib"
                result.append(library)
            else:
                result.append("-l%s" % library)
        return result

    def _adjust_path(self, path):
        if self._base_compiler == 'Visual Studio':
            path = path.replace('/', '\\')
        else:
            path = path.replace('\\', '/')

        path = subsystem_path(self._subsystem, path)
        return '"%s"' % path if ' ' in path else path

    @property
    def _base_compiler(self):
        return str(self._conanfile.settings.get_safe("compiler.base") or
                   self._conanfile.settings.get_safe("compiler"))
