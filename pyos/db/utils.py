import pyos

__all__ = ('path_to_meta_dict',)


def new_meta(orig: dict, new: dict) -> dict:
    merged = new.copy()
    if not orig:
        return merged

    for name in pyos.config.KEYS:
        if name in orig:
            if name.startswith('_'):
                # Always take internal, i.e. underscored, keys
                merged[name] = orig[name]
            else:
                merged.setdefault(name, orig[name])

    return merged


def path_to_meta_dict(path) -> dict:
    """
    :param path: the path to get a dictionary for
    :type path: pyos.os.PathSpec
    :return: the meta dictionary with the path
    """
    if path is None:
        return {}

    path = pyos.os.path.abspath(path)
    meta = {}
    if path.endswith(pyos.os.sep):
        meta[pyos.config.DIR_KEY] = path
    else:
        dirname, basename = pyos.os.path.split(path)
        meta[pyos.config.NAME_KEY] = basename
        meta[pyos.config.DIR_KEY] = dirname

    return meta
