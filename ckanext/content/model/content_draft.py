from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from typing_extensions import Self
from typing import Any

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.types as types
from ckan.model.types import make_uuid

from ckanext.content import types as content_types


class ContentDraftModel(tk.BaseModel):
    __tablename__ = "content_draft"

    id = sa.Column(sa.Text, primary_key=True, default=make_uuid)
    content_id = sa.Column(
        sa.Text,
        sa.ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = sa.Column(sa.Text, nullable=False)
    alias = sa.Column(sa.String, nullable=False)
    type = sa.Column(sa.String, nullable=False)
    data = sa.Column(MutableDict.as_mutable(JSONB))
    author = sa.Column(sa.String, nullable=False)
    state = sa.Column(sa.String, nullable=False, default="draft")
    created = sa.Column(sa.DateTime, server_default=sa.func.now())
    modified = sa.Column(
        sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()
    )
    translations = sa.Column(MutableDict.as_mutable(JSONB))

    @classmethod
    def get_by_id(cls, id: str) -> Self | None:
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_by_content_id(cls, content_id: str) -> Self | None:
        """Get draft by parent content_id"""
        return (
            model.Session.query(cls)
            .filter(cls.content_id == content_id)
            .first()
        )

    @classmethod
    def get_by_type(cls, type: str) -> list[Self]:
        return (
            model.Session.query(cls)
            .filter(cls.type == type)
            .order_by(cls.modified.desc())
            .all()
        )

    @classmethod
    def create(cls, data_dict: dict[str, Any]) -> Self:
        # Always set state to draft
        data_dict["state"] = "draft"
        draft = cls(**data_dict)

        model.Session.add(draft)
        model.Session.commit()

        return draft

    def delete(self) -> None:
        model.Session().autoflush = False
        model.Session.delete(self)
        model.Session.commit()

    def update(self, data_dict: dict[str, Any]) -> None:
        # Always keep state as draft
        data_dict["state"] = "draft"
        for key, value in data_dict.items():
            setattr(self, key, value)
        model.Session.commit()

    def update_translation(self, lang: str, data: dict[str, Any]) -> None:
        if not self.translations:
            self.translations = MutableDict()

        self.translations[lang] = data
        model.Session.commit()

    def delete_translation_key(self, lang: str):
        if self.translations and lang in self.translations:
            del self.translations[lang]
            model.Session.commit()

    def dictize(self, context: types.Context) -> content_types.Content:
        return content_types.Content(
            id=str(self.id),
            title=str(self.title),
            alias=str(self.alias),
            type=str(self.type),
            author=str(self.author),
            state=str(self.state),
            created=self.created.isoformat(),
            modified=self.modified.isoformat(),
            data=self.data,  # type: ignore
            translations=self.translations,  # type: ignore
        )
