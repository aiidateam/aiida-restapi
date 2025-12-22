import pydantic as pdt
from aiida.orm import Node


class NodeLinks(Node.Model):
    link_label: str = pdt.Field(description='The label of the link to the node.')
    link_type: str = pdt.Field(description='The type of the link to the node.')
