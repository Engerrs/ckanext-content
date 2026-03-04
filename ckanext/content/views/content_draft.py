from __future__ import annotations

from flask import Blueprint
from flask.views import MethodView

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.plugins.toolkit as tk

from ckanext.content import utils

ValidationError = logic.ValidationError

content_draft = Blueprint("ckan_content_draft", __name__)


class CreateDraftView(MethodView):
    """Create draft from existing content"""

    def get(self, type: str, content_id: str):
        try:
            tk.get_action("create_ckan_content_draft")(
                {}, {"content_id": content_id, "type": type}
            )
        except tk.NotAuthorized:
            return tk.abort(404, "Page not found")
        except tk.ObjectNotFound:
            return tk.abort(404, "Content not found")
        except logic.ValidationError as e:
            # Draft already exists
            tk.h.flash_error(e.error_summary)
            return tk.redirect_to(
                "ckan_content_draft.edit", type=type, content_id=content_id
            )

        tk.h.flash_success(tk._("Draft content created successfully"))
        return tk.redirect_to(
            "ckan_content_draft.edit", type=type, content_id=content_id
        )


class EditDraftView(MethodView):
    """Edit draft content"""

    def get(self, type: str, content_id: str):
        try:
            draft_dict = tk.get_action("get_ckan_content_draft")(
                {}, {"content_id": content_id, "type": type}
            )
        except tk.NotAuthorized:
            return tk.abort(404, "Page not found")
        except tk.ObjectNotFound:
            return tk.abort(404, "Draft not found")

        if not draft_dict:
            return tk.abort(404, "Draft not found")

        schema = tk.h.get_content_schema(type)

        data = {
            "title": draft_dict.get("title"),
            "alias": draft_dict.get("alias"),
            "type": draft_dict.get("type"),
            "state": draft_dict.get("state"),
        }

        data.update(draft_dict.get("data", {}))

        return tk.render(
            "content/draft_edit.html",
            extra_vars={
                "type": type,
                "content_id": content_id,
                "draft_id": draft_dict.get("id"),
                "data": data,
                "flat": utils.flatten_repeating_fields(data),
                "schema": schema,
                "errors": {},
            },
        )

    def post(self, type: str, content_id: str):
        try:
            form_data = logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(logic.parse_params(tk.request.form))
                )
            )
        except dict_fns.DataError:
            return tk.base.abort(400, tk._("Integrity Error"))

        for f_name, file in tk.request.files.items():
            correct_key = f_name.split("_content-")
            if (
                file.filename
                and len(correct_key)
                and correct_key[1] == "upload"
            ):
                form_data[correct_key[0]] = file

        schema = tk.h.get_content_schema(type)
        data_dict = {
            "schema": schema,
            "form_data": form_data,
            "content_id": content_id,
            "type": type,
        }

        try:
            tk.get_action("update_ckan_content_draft")({}, data_dict)
        except tk.NotAuthorized:
            return tk.abort(404, "Page not found")
        except logic.ValidationError as e:
            tk.h.flash_error(e.error_summary)
            return tk.render(
                "content/draft_edit.html",
                extra_vars={
                    "type": type,
                    "content_id": content_id,
                    "data": form_data,
                    "schema": schema,
                    "errors": e.error_dict,
                },
            )

        tk.h.flash_success(tk._("Draft content updated successfully"))
        return tk.redirect_to(
            "ckan_content_draft.edit", type=type, content_id=content_id
        )


class ReadDraftView(MethodView):
    """View draft content"""

    def get(self, type: str, content_id: str):
        try:
            draft_dict = tk.get_action("get_ckan_content_draft")(
                {}, {"content_id": content_id, "type": type}
            )
        except tk.NotAuthorized:
            return tk.abort(404, "Page not found")
        except tk.ObjectNotFound:
            return tk.abort(404, "Draft not found")

        if not draft_dict:
            return tk.abort(404, "Draft not found")

        schema = tk.h.get_content_schema(type)
        template = tk.h.guess_content_type_snippet(type)

        # Prepare content like in ReadView
        original_content = draft_dict
        default_locale = tk.config.get("ckan.locale_default", "en")
        curr_lang = tk.h.lang()

        if curr_lang != default_locale:
            from copy import deepcopy

            content = tk.h.content_prepare_translation(
                deepcopy(original_content)
            )
        else:
            content = original_content

        return tk.render(
            template,
            extra_vars={
                "schema": schema,
                "type": type,
                "id": draft_dict.get("id"),
                "content_id": content_id,
                "content": content,
                "original_content": original_content,
                "is_draft": True,
            },
        )


class DeleteDraftView(MethodView):
    """Delete draft content"""

    def post(self, type: str, content_id: str):
        try:
            tk.get_action("delete_ckan_content_draft")(
                {}, {"content_id": content_id, "type": type}
            )
        except tk.NotAuthorized:
            return tk.abort(404, "Page not found")
        except tk.ObjectNotFound:
            tk.h.flash_error(tk._("Draft not found"))
            return tk.redirect_to(
                "ckan_content.edit", type=type, id=content_id
            )

        tk.h.flash_success(tk._("Draft deleted successfully"))
        return tk.redirect_to("ckan_content.edit", type=type, id=content_id)


class MergeDraftView(MethodView):
    """Merge draft into original content"""

    def post(self, type: str, content_id: str):
        try:
            tk.get_action("merge_ckan_content_draft")(
                {}, {"content_id": content_id, "type": type}
            )
        except tk.NotAuthorized:
            return tk.abort(404, "Page not found")
        except tk.ObjectNotFound as e:
            tk.h.flash_error(str(e))
            return tk.redirect_to(
                "ckan_content.edit", type=type, id=content_id
            )

        tk.h.flash_success(tk._("Draft merged successfully into content"))
        return tk.redirect_to("ckan_content.edit", type=type, id=content_id)


# Register routes
content_draft.add_url_rule(
    "/content-draft/create/<type>/<content_id>",
    view_func=CreateDraftView.as_view("create"),
)

content_draft.add_url_rule(
    "/content-draft/edit/<type>/<content_id>",
    view_func=EditDraftView.as_view("edit"),
)

content_draft.add_url_rule(
    "/content-draft/read/<type>/<content_id>",
    view_func=ReadDraftView.as_view("read"),
)

content_draft.add_url_rule(
    "/content-draft/delete/<type>/<content_id>",
    view_func=DeleteDraftView.as_view("delete"),
    methods=["POST"],
)

content_draft.add_url_rule(
    "/content-draft/merge/<type>/<content_id>",
    view_func=MergeDraftView.as_view("merge"),
    methods=["POST"],
)
