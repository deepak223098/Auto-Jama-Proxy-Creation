# Usage
Modules in this package may have dependencies on third-party libraries or other modules within the package.  The package is verified to work on the which includes all of the third party dependencies.  For best effect, include the entire common package in your project in order to support inter-package dependencies.  Python 3 support is not guaranteed.

# Contributing
Anyone can use, add, or modify modules in this package but they should follow a few rules:
- All functions, classes, and modules (files) shall include in-code documentation which briefly describes the purpose of the unit and, if relevant, any arguments and return values.
- All documentation shall adhere to the rules defined in [PEP 257](https://www.python.org/dev/peps/pep-0257/) as best as possible.
- All source code shall adhere to rules defined in [PEP 8](https://www.python.org/dev/peps/pep-0008/) as best as possible.
- No moules shall be dependent on modules or libraries outside of the common package, builtins, and third party libraries installed to [the tagged Python installation](http://asvn/fms-dev/tools/tags/python/Python273).
- The disk space consumed by the common package shall be kept to a minimum.  It is a dependency for other tools and should not significantly increase the size of those tools.

