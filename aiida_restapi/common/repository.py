"""REST API utilities."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.common.pydantic import get_metadata

from .pagination import PaginatedResults
from .query import QueryParams
from .types import EntityModelType, EntityType, NodeModelType, NodeType


class EntityRepository(t.Generic[EntityType, EntityModelType]):
    """Utility class for AiiDA REST API operations.

    This class provides methods to retrieve AiiDA entities with optional filtering, sorting, and pagination.

    :ivar entity_cls: The AiiDA ORM entity class associated with this utility, e.g. `orm.User`, `orm.Node`, etc.
    """

    def __init__(self, orm_entity: type[EntityType]):
        self.entity_cls: type[EntityType] = orm_entity

    def get_projectable_properties(self) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :return: The list of projectable properties for the AiiDA entity.
        """
        return sorted(self.entity_cls.fields.keys())

    def get_entities(self, queries: QueryParams) -> PaginatedResults[EntityModelType]:
        """Get AiiDA entities with optional filtering, sorting, and/or pagination.

        :param queries: The query parameters, including filters, order_by, page_size, and page.
        :return: The paginated results, including total count, current page, page size, and list of entity models.
        """
        total = self.entity_cls.collection.count(filters=queries.filters)
        results = self.entity_cls.collection.find(
            filters=queries.filters,
            order_by=queries.order_by,
            limit=queries.page_size,
            offset=queries.page_size * (queries.page - 1),
        )
        return PaginatedResults[EntityModelType](
            total=total,
            page=queries.page,
            page_size=queries.page_size,
            results=[result.to_model() for result in results],
        )

    def get_entity_by_id(self, entity_id: int) -> EntityModelType:
        """Get an AiiDA entity by id.

        :param entity_id: The id of the entity to retrieve.
        :return: The AiiDA entity model, e.g. `orm.User.Model`, `orm.Node.Model`, etc.
        """
        return t.cast(EntityModelType, self.entity_cls.collection.get(pk=entity_id).to_model())

    def create_entity(self, model: EntityModelType) -> EntityModelType:
        """Create new AiiDA entity from its model.

        :param model: The Pydantic model of the entity to create.
        :return: The created and stored AiiDA `Entity` instance.
        """
        entity = self.entity_cls.from_model(model).store()
        return t.cast(EntityModelType, entity.to_model())


class NodeRepository(EntityRepository[NodeType, NodeModelType]):
    """Utility class for AiiDA Node REST API operations."""

    def get_projectable_properties(self, node_type: str | None = None) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :param node_type: The AiiDA node type.
        :return: The list of projectable properties for the AiiDA node.
        """
        if not node_type:
            return super().get_projectable_properties()
        else:
            node_cls = orm.utils.load_node_class(node_type)
            return sorted(node_cls.fields.keys())

    def get_entities(self, queries: QueryParams) -> PaginatedResults[NodeModelType]:
        """Get nodes with optional filtering, sorting, and/or pagination and augment repository content."""
        paginated_results = super().get_entities(queries)
        for model in paginated_results.results:
            self._patch_repository_metadata(model)
        return paginated_results

    def get_entity_by_id(self, entity_id: int) -> NodeModelType:
        """Get a single node by id and augment repository content."""
        model = super().get_entity_by_id(entity_id)
        return self._patch_repository_metadata(model)

    def create_entity(self, model: NodeModelType, node_type: str | None = None) -> NodeModelType:
        """Create new AiiDA node from its model.

        :param node_model: The AiiDA ORM model of the node to create.
        :param node_type: The AiiDA node type.
        :return: The created and stored AiiDA node instance.
        """
        if node_type is None:
            raise ValueError('Node type is required')
        node_cls = orm.utils.load_node_class(node_type)
        node = t.cast(NodeType, node_cls.from_model(model))
        node.base.attributes.set_many(
            {
                key: getattr(model, key)
                for key, field in model.model_fields.items()
                if key != 'orm_class' and get_metadata(field, 'is_attribute')
            }
        )
        node.base.extras.set_many(model.extras or {})
        node.store()
        created_model = node.to_model()
        patched_model = self._patch_repository_metadata(created_model)
        return patched_model

    def _patch_repository_metadata(self, model: NodeModelType) -> NodeModelType:
        """Add download URLs to the repository content of the node model.

        :param model: The AiiDA node model.
        :return: The patched AiiDA node model with download URLs in the repository metadata.
        """

        repo_metadata: dict[str, t.Any] = getattr(model, 'repository_metadata')
        if not repo_metadata:
            return model

        node = self.entity_cls.collection.get(pk=model.pk)

        total_size = 0
        for path in repo_metadata['o']:
            size = node.base.repository.get_object_size(path)
            total_size += size
            repo_metadata['o'][path] |= {
                'size': size,
                'download': f'/nodes/{model.pk}/repo/contents?filename={path}',
            }

        repo_metadata['o']['zipped'] = {
            'size': total_size,
            'download': f'/nodes/{model.pk}/repo/contents',
        }

        setattr(model, 'repository_metadata', repo_metadata)

        return model
