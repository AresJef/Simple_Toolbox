### A simple collection of python utils.

Created to be used in a project, this package is published to gihub and 
pypi for ease of management and installation across different modules.

### Installation
install using `pip`

``` bash
pip install simple_toolkit
```

install from `github`

``` bash
pip install git+https://github.com/AresJef/Simple_Toolkit.git
```

### Compatibility
Only support for python 3.11 and above.

This package created a Cythonized version of dateutil.parser and 
dateutil.relativedelta. As a consequence of the modification, these 
two modules in this package have sacrificed some flexibility and a 
significant amount of readability in exchange for some enhancements 
in performance.

While this trade-off is not justifiable in any cases, it is certainly
interesting for me personally to understand how dateutil actual works
and I have learnt so much through this process.

### Acknowledgements
simple_toolkit is based on several open-source repositories.

simple_toolkit makes modification of the following open-source repositories:
- [dateutil](https://github.com/dateutil/dateutil/)




