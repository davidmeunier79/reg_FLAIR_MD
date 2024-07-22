
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

from macapype.utils.utils_nodes import NodeParams
from macapype.utils.misc import parse_key

#from nodes.prepare import reg_aladin_dirty

from nipype.interfaces.niftyreg.reg import RegAladin

###############################################################################
def create_short_preparation_FLAIR_pipe(params,
                                        name="short_preparation_FLAIR_pipe"):
    """Description: apply transfo on FLAIR (no reorient so far)

    Processing steps;

    - coreg FLAIR on T1
    - apply coreg on FLAIR

    Params:

    Inputs:

        inputnode:

            orig_T1:
                T1 files (from BIDSDataGrabber)

            FLAIR:
                FLAIR file

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:

            coreg_FLAIR:
                preprocessed FLAIR file

    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['orig_T1', 'FLAIR']),
        name='inputnode'
    )

    if "align_FLAIR_on_T1" in params.keys():
        print("in align_FLAIR_on_T1")

        # align FLAIR on avg T1
        align_FLAIR_on_T1 = NodeParams(
            fsl.FLIRT(),
            params=parse_key(params, "align_FLAIR_on_T1"),
            name="align_FLAIR_on_T1")

        data_preparation_pipe.connect(inputnode, 'orig_T1',
                                      align_FLAIR_on_T1, 'reference')

        data_preparation_pipe.connect(inputnode, 'FLAIR',
                                      align_FLAIR_on_T1, 'in_file')

    elif "reg_aladin_FLAIR_on_T1" in params.keys():
        print("in reg_aladin_FLAIR_on_T1")

        align_FLAIR_on_T1 = pe.Node(
            interface=RegAladin(),
            name="align_FLAIR_on_T1")

        data_preparation_pipe.connect(inputnode, 'orig_T1',
                                      align_FLAIR_on_T1, 'ref_file')

        data_preparation_pipe.connect(inputnode, 'FLAIR',
                                      align_FLAIR_on_T1, 'flo_file')

        align_FLAIR_on_T1_2 = pe.Node(
            interface=RegAladin(),
            name="align_FLAIR_on_T1_2")

        data_preparation_pipe.connect(inputnode, 'orig_T1',
                                      align_FLAIR_on_T1_2, 'ref_file')

        data_preparation_pipe.connect(align_FLAIR_on_T1, 'res_file',
                                      align_FLAIR_on_T1_2, 'flo_file')
    else:
        print("no align_FLAIR_on_T1 or reg_aladin_FLAIR_on_T1, breaking")
        exit(0)

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['coreg_FLAIR']),
        name='outputnode')

    data_preparation_pipe.connect(align_FLAIR_on_T1_2, 'res_file',
                                  outputnode, 'coreg_FLAIR')

    return data_preparation_pipe


def create_short_preparation_MD_pipe(params,
                                     name="short_preparation_MD_pipe"):
    """Description: apply transfo on MD (no reorient so far)

    Processing steps;

    - init coreg b0mean on SS_T2
    - coreg b0mean on T2 using bbr and native_wm
    - apply coreg transfo on MD

    Params:

    Inputs:

        inputnode:

            orig_T2:
                T2 files (from BIDSDataGrabber)

            SS_T2:
                After Skull strip

            MD:
                MD file

            b0mean:
                B0 mean file

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:

            coreg_MD:
                preprocessed MD file with init

            coreg_better_MD:
                preprocessed MD file with init and flirt

    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['SS_T2', 'MD',
                                      'b0mean', 'native_wm_mask']),
        name='inputnode'
    )

    # init_align_b0mean_on_T2
    init_align_b0mean_on_T2 = NodeParams(
        fsl.FLIRT(), params=parse_key(params, "init_align_b0mean_on_T2"),
        name="init_align_b0mean_on_T2")

    data_preparation_pipe.connect(inputnode, 'SS_T2',
                                  init_align_b0mean_on_T2, 'reference')
    data_preparation_pipe.connect(inputnode, 'b0mean',
                                  init_align_b0mean_on_T2, 'in_file')

    # align_b0mean_on_T2
    align_b0mean_on_T2 = NodeParams(
        fsl.FLIRT(), params=parse_key(params, "align_b0mean_on_T2"),
        name="align_b0mean_on_T2")

    data_preparation_pipe.connect(inputnode, 'SS_T2',
                                  align_b0mean_on_T2, 'reference')
    data_preparation_pipe.connect(inputnode, 'b0mean',
                                  align_b0mean_on_T2, 'in_file')
    data_preparation_pipe.connect(inputnode, 'native_wm_mask',
                                  align_b0mean_on_T2, 'wm_seg')
    data_preparation_pipe.connect(init_align_b0mean_on_T2, 'out_matrix_file',
                                  align_b0mean_on_T2, 'in_matrix_file')

    # Apply transfo computed on b0 on MD (init)
    align_MD_on_T2_with_b0 = pe.Node(fsl.ApplyXFM(),
                                     name="align_MD_on_T2_with_b0")

    data_preparation_pipe.connect(inputnode, 'SS_T2',
                                  align_MD_on_T2_with_b0, 'reference')
    data_preparation_pipe.connect(inputnode, 'MD',
                                  align_MD_on_T2_with_b0, 'in_file')
    data_preparation_pipe.connect(init_align_b0mean_on_T2, 'out_matrix_file',
                                  align_MD_on_T2_with_b0, 'in_matrix_file')

    # Apply transfo computed on b0 on MD (second_flirt with GM)
    align_better_MD_on_T2_with_b0 = pe.Node(
        fsl.ApplyXFM(), name="align_better_MD_on_T2_with_b0")

    data_preparation_pipe.connect(inputnode, 'SS_T2',
                                  align_better_MD_on_T2_with_b0, 'reference')
    data_preparation_pipe.connect(inputnode, 'MD',
                                  align_better_MD_on_T2_with_b0, 'in_file')
    data_preparation_pipe.connect(align_b0mean_on_T2, 'out_matrix_file',
                                  align_better_MD_on_T2_with_b0,
                                  'in_matrix_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['coreg_MD', 'coreg_better_MD']),
        name='outputnode')

    data_preparation_pipe.connect(align_MD_on_T2_with_b0, 'out_file',
                                  outputnode, 'coreg_MD')

    data_preparation_pipe.connect(align_better_MD_on_T2_with_b0, 'out_file',
                                  outputnode, 'coreg_better_MD')

    return data_preparation_pipe
