from os import listdir as os_listdir
cimport cython

### Clean Path
cdef str _clean_path(str path, str os_sep):
    cdef:
        str bslash = "\\"
        str fslash = "/"
        str colon = ":"
        str star = "*"
        str quest = "?"
        str quote = "\""
        str lt = "<"
        str gt = ">"
        str pipe = "|"
        str nil = ""

    if not path:
        return path

    if bslash in path and bslash != os_sep:
        path = path.replace(bslash, os_sep)
    if fslash in path and fslash != os_sep:
        path = path.replace(fslash, os_sep)
    if colon in path:
        path = path.replace(colon, nil)
    if star in path:
        path = path.replace(star, nil)
    if quest in path:
        path = path.replace(quest, nil)
    if quote in path:
        path = path.replace(quote, nil)
    if lt in path:
        path = path.replace(lt, nil)
    if gt in path:
        path = path.replace(gt, nil)
    if pipe in path:
        path = path.replace(pipe, nil)
    
    return path

cpdef str clean_path(str path, str os_sep):
    return _clean_path(path, os_sep)

### Offset path
cpdef str offset_path(str path, int offset, str os_sep):
    cdef int zero = 0

    if not path or not offset:
        return path

    cdef list paths = _clean_path(path, os_sep).split(os_sep)

    if not paths:
        return path
    elif offset > zero:
        return os_sep.join(paths[offset:])
    else:
        return os_sep.join(paths[:offset])

### List Directory
@cython.boundscheck(False)  # Deactivate bounds checking
cpdef list list_directory(str path, tuple excludes):
    cdef:
        tuple dft_excludes = (".DS_Store", "Thumbs.db", "desktop.ini", ".git", ".gitignore")
        list files = []
        str f

    if not excludes:
        excludes = dft_excludes

    cdef list dir_files = os_listdir(path)
    if not dir_files:
        return []

    for f in dir_files:
        if f not in excludes and not f.startswith("._"):
            files.append(f)

    return files

 