#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import request
from flask_login import login_required, current_user

from redash import models, redis_connection
from redash.authentication import current_org
from redash.handlers import routes
from redash.handlers.base import json_response, record_event
from redash.permissions import require_super_admin
from redash.serializers import QuerySerializer
from redash.utils import json_loads
from redash.monitor import celery_tasks


@routes.route('/api/admin/queries/outdated', methods=['GET'])
@require_super_admin
@login_required
def outdated_queries():
    manager_status = redis_connection.hgetall('redash:status')
    query_ids = json_loads(manager_status.get('query_ids', '[]'))
    if query_ids:
        outdated_queries = (
            models.Query.query.outerjoin(models.QueryResult)
                              .filter(models.Query.id.in_(query_ids))
                              .order_by(models.Query.created_at.desc())
        )
    else:
        outdated_queries = []

    record_event(current_org, current_user._get_current_object(), {
        'action': 'list',
        'object_type': 'outdated_queries',
    })

    updated_at = None
    if manager_status and manager_status['last_refresh_at']:
        updated_at = manager_status['last_refresh_at']

    response = {
        'queries': QuerySerializer(outdated_queries, with_stats=True, with_last_modified_by=False).serialize(),
        'updated_at': updated_at,
    }
    return json_response(response)


@routes.route('/api/admin/queries/tasks', methods=['GET'])
@require_super_admin
@login_required
def queries_tasks():
    record_event(current_org, current_user._get_current_object(), {
        'action': 'list',
        'object_type': 'celery_tasks'
    })

    response = {
        'tasks': celery_tasks(),
    }

    return json_response(response)
