from dataclasses import dataclass, field
import json
import pymel.core as pm


@dataclass
class AttributeData:
    name: str
    value: any
    inputs: list["str"] = field(default_factory=list)
    outputs: list["str"] = field(default_factory=list)

    @classmethod
    def from_pynode(cls, attribute: pm.Attribute):
        name = attribute.name()
        attribute_type = attribute.type()
        if attribute_type == "string":
            value = attribute.get() or ""
        else:
            value = attribute.get()
        inputs = [input_attribute.name() for input_attribute in attribute.inputs(plugs=True)]
        outputs = [output_attribute.name() for output_attribute in attribute.outputs(plugs=True)]

        return AttributeData(
            name=name,
            value=value,
            inputs=inputs,
            outputs=outputs
        )


@dataclass
class CustomAttributeData:
    base_data: AttributeData
    type: str

    @classmethod
    def from_pynode(cls, attribute: pm.Attribute):
        base_data = AttributeData.from_pynode(attribute)
        attribute_type = attribute.type()

        return CustomAttributeData(
            base_data=base_data,
            type=attribute_type
        )

    @classmethod
    def from_node_string(cls, node_string):
        return cls.from_pynode(pm.Attribute(node_string))


@dataclass
class NodeData:
    name: str
    attributes: list[AttributeData] = field(default_factory=list)
    node_type: str

    @classmethod
    def from_pynode(cls, node: pm.nt.DependNode):
        name = node.name()
        attributes = [AttributeData.from_pynode(attribute) for attribute in cls.get_attributes(node)]
        return cls(
            name=name,
            attributes=attributes,
            node_type=node.nodeType()
        )

    @classmethod
    def get_attributes(cls, node):
        interesting_attributes = cls.get_interesting_attributes(node)
        return [AttributeData.from_pynode(attribute) for attribute in node.listAttr(string=interesting_attributes)]

    @classmethod
    def get_interesting_attributes(cls, node) -> list[str]:
        return list()


class AnimLayerData(NodeData):
    @classmethod
    def get_interesting_attributes(cls, node) -> list[str]:
        return ["childsoloed", "weight", "solo", "parentLayer"]


def get_node_name(node: pm.nt.DependNode):
    if isinstance(node, pm.nt.DagNode):
        return node.fullPath()
    else:
        return node.name()
