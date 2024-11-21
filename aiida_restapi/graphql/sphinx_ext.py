"""Sphinx extension for documenting the GraphQL schema."""

# pylint: disable=import-outside-toplevel
from typing import TYPE_CHECKING, List

from graphql.utilities import print_schema

from .main import SCHEMA

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def setup(app: 'Sphinx') -> None:
    """Setup the sphinx extension."""
    from docutils.nodes import Element, literal_block
    from sphinx.util.docutils import SphinxDirective

    class SchemaDirective(SphinxDirective):
        """Directive to generate the GraphQL schema."""

        def run(self) -> List[Element]:
            """Run the directive."""
            text = print_schema(SCHEMA.graphql_schema)
            # TODO for lexing tried: https://gitlab.com/marcogiusti/pygments-graphql/-/blob/master/src/pygments_graphql.py
            # but it failed
            code_node = literal_block(text, text)  # , language="graphql")
            self.set_source_info(code_node)
            return [code_node]

    app.add_directive('aiida-graphql-schema', SchemaDirective)
