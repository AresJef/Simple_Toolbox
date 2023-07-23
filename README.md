### A simple collection of python utils.

Created to be used in a project, this package is published to github 
for ease of management and installation across different modules.

### Installation
Install from `github`

``` bash
pip install git+https://github.com/AresJef/Simple_Toolbox.git
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
simple_toolbox is based on several open-source repositories.

simple_toolbox makes modification of the following open-source repositories:
- [dateutil](https://github.com/dateutil/dateutil)




