def _load_template(filename):
    import os
    directory = __file__
    fpath = os.path.join(os.path.dirname(directory), filename + ".template")

    with open(fpath, "r") as f:
        return f.read()

def template(filename, **data):
    return _load_template(filename).format(**data)

def write_template(template_file, filename, **data):
    command = "sudo cat <<EOT > {0}\n{1}\nEOT"
    return command.format(filename, template(template_file, **data))

def append_template(template_file, filename, **data):
    command = "sudo cat <<EOT > {0}\n{1}\nEOT"
    return command.format(filename, template(template_file, **data))
