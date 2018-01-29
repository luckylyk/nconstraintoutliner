
import maya.OpenMaya as om
sel = om.MSelectionList()
om.MGlobal.getActiveSelectionList(sel)
dagpath = om.MDagPath()
comp = om.MObject()
sel.getDagPath(0, dagpath, comp)
dagnode = om.MFnDagNode(dagpath)


def create_yeti_lod_compound_attribute(index):

    message_fn = om.MFnMessageAttribute()
    camera_attribute = message_fn.create('YetiNode', 'yeti_node')
    message_fn.setKeyable(False)

    numeric_fn = om.MFnNumericAttribute()
    numeric_fn.setConnectable(False)
    min_attr = numeric_fn.create("Minimum", "min", om.MFnNumericData.kFloat)
    max_attr = numeric_fn.create("Maxnimum", "max", om.MFnNumericData.kFloat)

    output_fn = om.MFnNumericAttribute()
    output_density = output_fn.create(
        "DensityOutput", "dOut", om.MFnNumericData.kFloat)
    output_width = numeric_fn.create(
        "WidthOutput", "wOut", om.MFnNumericData.kFloat)
    output_fn.setConnectable(False)
    output_fn.setWritable(False)
    output_fn.setStorable(False)

    compound_fn = om.MFnCompoundAttribute()
    compound = compound_fn.create('YetiNode[{}]'.format(index), 'yNodes')
    compound_fn.addChild(camera_attribute)
    compound_fn.addChild(min_attr)
    compound_fn.addChild(max_attr)
    compound_fn.addChild(output_density)
    compound_fn.addChild(output_width)

    return compound

compound = create_yeti_lod_compound_attribute(5)
dagnode.addAttribute(compound)
