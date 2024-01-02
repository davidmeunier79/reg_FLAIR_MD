"""
seems was never wrapped in nipype
"""


def reg_aladin_dirty(reference, in_file):

    import os

    cwd = os.path.abspath("")
    os.chdir(cwd)
    out_file = os.path.abspath("outputResult.nii")
    cmd = "reg_aladin -flo {} -ref {} -res {}".format(
        in_file, reference, out_file)
    os.system(cmd)

    assert os.path.exists(out_file)
    return out_file
