# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 CERN.
# Copyright (C) 2019-2021 Northwestern University.
# Copyright (C)      2021 TU Wien.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Routes for record-related pages provided by Invenio-App-RDM."""

from functools import wraps

from flask import g, request
from invenio_pidstore.errors import PIDUnregistered
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.resources.config import RDMDraftFilesResourceConfig
from invenio_records_resources.services.errors import PermissionDeniedError
from sqlalchemy.orm.exc import NoResultFound


def service():
    """Get the record service."""
    return current_rdm_records.records_service


def files_service():
    """Get the record files service."""
    return current_rdm_records.records_service.files


def draft_files_service():
    """Get the record files service."""
    return current_rdm_records.records_service.draft_files


def pass_record_latest(f):
    """Decorate a view to pass the latest version of a record."""
    @wraps(f)
    def view(**kwargs):
        pid_value = kwargs.get('pid_value')
        record_latest = service().read_latest(
            id_=pid_value, identity=g.identity
        )
        kwargs['record'] = record_latest
        return f(**kwargs)
    return view


def pass_draft(f):
    """Decorator to retrieve the draft using the record service."""
    @wraps(f)
    def view(**kwargs):
        pid_value = kwargs.get('pid_value')
        draft = service().read_draft(
            id_=pid_value,
            identity=g.identity
        )
        # TODO: Remove - all this should happen in service
        # Dereference relations (languages, licenses, etc.)
        draft._record.relations.dereference()
        kwargs['draft'] = draft
        return f(**kwargs)
    return view


def pass_is_preview(f):
    """Decorate a view to check if it's a preview."""
    @wraps(f)
    def view(**kwargs):
        preview = request.args.get('preview')
        is_preview = False
        if preview == '1':
            is_preview = True
        kwargs['is_preview'] = is_preview
        # TODO: Remove - all this should happen in service
        # Dereference relations (languages, licenses, etc.)
        return f(**kwargs)
    return view


def pass_record_from_pid(f):
    """Decorate a view to pass the latest version of a record."""
    @wraps(f)
    def view(*args, **kwargs):
        pid_type = kwargs.get('pid_scheme')
        pid_value = kwargs.get('pid_value')

        record = service().resolve_pid(
            id_=pid_value,
            pid_type=pid_type,
            identity=g.identity
        )

        kwargs['record'] = record
        return f(**kwargs)
    return view


def pass_record_or_draft(f):
    """Decorate to retrieve the record or draft using the record service."""
    @wraps(f)
    def view(**kwargs):
        pid_value = kwargs.get('pid_value')
        is_preview = kwargs.get('is_preview')
        if is_preview:
            record = service().read_draft(
                id_=pid_value,
                identity=g.identity
            )
        else:
            record = service().read(
                id_=pid_value, identity=g.identity
            )
        kwargs['record'] = record
        # TODO: Remove - all this should happen in service
        # Dereference relations (languages, licenses, etc.)
        record._record.relations.dereference()
        return f(**kwargs)
    return view


def pass_file_item(f):
    """Decorate a view to pass a file item using the files service."""
    @wraps(f)
    def view(**kwargs):
        pid_value = kwargs.get('pid_value')
        file_key = kwargs.get('filename')
        is_preview = kwargs.get('is_preview')
        if is_preview:
            item = draft_files_service().get_file_content(
                id_=pid_value,
                file_key=file_key,
                identity=g.identity
            )
        else:
            item = files_service().get_file_content(
                id_=pid_value,
                file_key=file_key,
                identity=g.identity
            )
        kwargs['file_item'] = item
        return f(**kwargs)
    return view


def pass_file_metadata(f):
    """Decorate a view to pass a file's metadata using the files service."""
    @wraps(f)
    def view(**kwargs):
        pid_value = kwargs.get('pid_value')
        file_key = kwargs.get('filename')
        is_preview = kwargs.get('is_preview')
        if is_preview:
            files = draft_files_service().read_file_metadata(
                id_=pid_value,
                file_key=file_key,
                identity=g.identity
            )
        else:
            files = files_service().read_file_metadata(
                id_=pid_value,
                file_key=file_key,
                identity=g.identity
            )
        kwargs['file_metadata'] = files
        return f(**kwargs)
    return view


def pass_record_files(f):
    """Decorate a view to pass a record's files using the files service."""
    @wraps(f)
    def view(**kwargs):
        preview = request.args.get('preview')
        is_preview = kwargs.get('is_preview')

        try:
            pid_value = kwargs.get('pid_value')
            if is_preview:
                files = draft_files_service().list_files(
                    id_=pid_value, identity=g.identity
                )
            else:
                files = files_service().list_files(
                    id_=pid_value, identity=g.identity
                )
            kwargs['files'] = files

        except PermissionDeniedError:
            # this is handled here because we don't want a 404 on the landing
            # page when a user is allowed to read the metadata but not the
            # files
            kwargs['files'] = None

        return f(**kwargs)
    return view


def pass_draft_files(f):
    """Decorate a view to pass a draft's files using the files service."""
    @wraps(f)
    def view(**kwargs):
        try:
            pid_value = kwargs.get('pid_value')
            files = draft_files_service().list_files(
                id_=pid_value, identity=g.identity
            )
            kwargs['draft_files'] = files

        except PermissionDeniedError:
            # this is handled here because we don't want a 404 on the landing
            # page when a user is allowed to read the metadata but not the
            # files
            kwargs['draft_files'] = None

        return f(**kwargs)
    return view
