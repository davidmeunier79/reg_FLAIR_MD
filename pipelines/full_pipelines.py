"""
    Gather all full pipelines

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces import fsl

from .prepare import (create_short_preparation_FLAIR_pipe,
                      create_short_preparation_MD_pipe)

from macapype.utils.misc import parse_key

###############################################################################
# FLAIR after SPM based segmentation
# -soft SPM_FLAIR or SPM_T1_FLAIR
###############################################################################


def create_transfo_FLAIR_pipe(params_template, params={},
                              name='transfo_FLAIR_pipe'):
    """ Description: apply tranformation to FLAIR, MD and FA if necssary

    Processing steps:

    - -coreg FA on T1
    - apply coreg on MD
    - debias using T1xT2BiasFieldCorrection (using mask is betcrop)
    - registration to template file with IterREGBET
    - SPM segmentation the old way (SPM8, not dartel based)

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)
    - debias (see :class:`T1xT2BiasFieldCorrection \
    <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`) - also available \
    as :ref:`indiv_params <indiv_params>`
    - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) - \
    also available as :ref:`indiv_params <indiv_params>`
    - old_segment_pipe (see :class:`create_old_segment_pipe \
    <macapype.pipelines.segment.create_old_segment_pipe>`)
    - nii_to_mesh_fs_pipe (see :class:`create_nii_to_mesh_fs_pipe \
    <macapype.pipelines.surface.create_nii_to_mesh_fs_pipe>`)

    Inputs:

        inputnode:

            SS_T1:
                T1 file names

            orig_T1:
                T2 file names

            FLAIR:
                flair file name

            transfo_file:
                Transformation file between native to template

            inv_transfo_file:
                Transformation file between template and native

            threshold_wm:
                gm binary tissue in template space

            indiv_params (opt):
                dict with individuals parameters for some nodes

        outputnode:

            coreg_FLAIR:
                FLAIR coregistered to T1

            norm_FLAIR:
                FLAIR normalised in template space

        arguments:

            params_template:
                dict of template files containing brain_template and priors \
            (list of template based segmented tissues)

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_spm_subpipes")

    Outputs:

    """

    print("Transfo FLAIR pipe name: ", name)

    # Creating pipeline
    transfo_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['orig_T1', 'FLAIR', 'lin_transfo_file']),
        name='inputnode'
    )

    data_preparation_pipe = create_short_preparation_FLAIR_pipe(
        params=parse_key(params, "short_preparation_FLAIR_pipe"))

    transfo_pipe.connect(inputnode, 'orig_T1',
                         data_preparation_pipe, 'inputnode.orig_T1')
    transfo_pipe.connect(inputnode, 'FLAIR',
                         data_preparation_pipe, 'inputnode.FLAIR')

    # apply norm to FLAIR
    norm_lin_FLAIR = pe.Node(fsl.ApplyXFM(), name="norm_lin_FLAIR")
    norm_lin_FLAIR.inputs.reference = params_template["template_brain"]

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_FLAIR',
                         norm_lin_FLAIR, 'in_file')
    transfo_pipe.connect(inputnode, 'lin_transfo_file',
                         norm_lin_FLAIR, 'in_matrix_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['coreg_FLAIR', 'norm_FLAIR']),
        name='outputnode'
    )

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_FLAIR',
                         outputnode, 'coreg_FLAIR')

    transfo_pipe.connect(norm_lin_FLAIR, 'out_file',
                         outputnode, 'norm_FLAIR')

    return transfo_pipe


# SPM with MD
def create_transfo_MD_pipe(params_template, params={},
                           name='transfo_MD_pipe'):
    """ Description: apply tranformation to FLAIR, MD and FA if necssary

    Processing steps:

    - -coreg FA on T1
    - apply coreg on MD
    - debias using T1xT2BiasFieldCorrection (using mask is betcrop)
    - registration to template file with IterREGBET
    - SPM segmentation the old way (SPM8, not dartel based)

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)
    - debias (see :class:`T1xT2BiasFieldCorrection \
    <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`) - also available \
    as :ref:`indiv_params <indiv_params>`
    - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) - \
    also available as :ref:`indiv_params <indiv_params>`
    - old_segment_pipe (see :class:`create_old_segment_pipe \
    <macapype.pipelines.segment.create_old_segment_pipe>`)
    - nii_to_mesh_fs_pipe (see :class:`create_nii_to_mesh_fs_pipe \
    <macapype.pipelines.surface.create_nii_to_mesh_fs_pipe>`)

    Inputs:

        inputnode:

            SS_T1:
                T1 file names

            orig_T1:
                T2 file names

            FLAIR:
                flair file name

            transfo_file:
                Transformation file between native to template

            inv_transfo_file:
                Transformation file between template and native

            threshold_wm:
                gm binary tissue in template space

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dict of template files containing brain_template and priors \
            (list of template based segmented tissues)

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_spm_subpipes")

    Outputs:

    """

    print("Transfo MD pipe name: ", name)

    # Creating pipeline
    transfo_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['orig_T1', 'SS_T2', 'MD', 'b0mean',
                    'threshold_wm', 'lin_transfo_file',
                    'inv_lin_transfo_file']),
        name='inputnode'
    )

    compute_native_wm = pe.Node(fsl.ApplyXFM(), name='compute_native_wm')

    transfo_pipe.connect(inputnode, 'threshold_wm',
                         compute_native_wm, 'in_file')

    transfo_pipe.connect(inputnode, 'orig_T1',
                         compute_native_wm, 'reference')

    transfo_pipe.connect(inputnode, 'inv_lin_transfo_file',
                         compute_native_wm, 'in_matrix_file')

    data_preparation_pipe = create_short_preparation_MD_pipe(
        params=parse_key(params, "short_preparation_MD_pipe"))

    transfo_pipe.connect(inputnode, 'SS_T2',
                         data_preparation_pipe, 'inputnode.SS_T2')
    transfo_pipe.connect(inputnode, 'MD',
                         data_preparation_pipe, 'inputnode.MD')
    transfo_pipe.connect(inputnode, 'b0mean',
                         data_preparation_pipe, 'inputnode.b0mean')
    transfo_pipe.connect(compute_native_wm, 'out_file',
                         data_preparation_pipe, 'inputnode.native_wm_mask')

    # apply norm to coreg_MD
    norm_lin_MD = pe.Node(fsl.ApplyXFM(), name="norm_lin_MD")
    norm_lin_MD.inputs.reference = params_template["template_brain"]

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_MD',
                         norm_lin_MD, 'in_file')
    transfo_pipe.connect(inputnode, 'lin_transfo_file',
                         norm_lin_MD, 'in_matrix_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['coreg_MD', 'norm_MD']),
        name='outputnode'
    )

    # coreg
    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_MD',
                         outputnode, 'coreg_MD')

    # norm
    transfo_pipe.connect(norm_lin_MD, 'out_file',
                         outputnode, 'norm_MD')

    return transfo_pipe
