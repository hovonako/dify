# -*- coding:utf-8 -*-
from flask import request
from flask_restful import fields, marshal_with, reqparse
from flask_restful.inputs import int_range
from werkzeug.exceptions import NotFound

from controllers.service_api import api
from controllers.service_api.app import create_or_update_end_user_for_user_id
from controllers.service_api.app.error import NotChatAppError
from controllers.service_api.wraps import AppApiResource
from libs.helper import TimestampField, uuid_value
import services
from services.conversation_service import ConversationService

conversation_fields = {
    'id': fields.String,
    'name': fields.String,
    'inputs': fields.Raw,
    'status': fields.String,
    'introduction': fields.String,
    'created_at': TimestampField
}

conversation_infinite_scroll_pagination_fields = {
    'limit': fields.Integer,
    'has_more': fields.Boolean,
    'data': fields.List(fields.Nested(conversation_fields))
}


class ConversationApi(AppApiResource):

    def external_api_call(self, api_url):
        try:
            response = requests.get(api_url)
            return response.json()
        except Exception as e:
            print(f"Error occurred while making API call: {e}")
            return None

    @marshal_with(conversation_infinite_scroll_pagination_fields)
    def get(self, app_model, end_user):
        if app_model.mode != 'chat':
            raise NotChatAppError()

        parser = reqparse.RequestParser()
        parser.add_argument('last_id', type=uuid_value, location='args')
        parser.add_argument('limit', type=int_range(1, 100), required=False, default=20, location='args')
        parser.add_argument('user', type=str, location='args')
        args = parser.parse_args()

        if end_user is None and args['user'] is not None:
            end_user = create_or_update_end_user_for_user_id(app_model, args['user'])

        api_url = 'http://example.com/api' # replace with actual API URL
        context = self.external_api_call(api_url)
        if context is None:
            raise Exception("Failed to get data from external API")
        try:
            return ConversationService.pagination_by_last_id(app_model, end_user, args['last_id'], args['limit'], context)
        except services.errors.conversation.LastConversationNotExistsError:
            raise NotFound("Last Conversation Not Exists.")

class ConversationDetailApi(AppApiResource):
    @marshal_with(conversation_fields)
    def delete(self, app_model, end_user, c_id):
        if app_model.mode != 'chat':
            raise NotChatAppError()

        conversation_id = str(c_id)

        user = request.get_json().get('user')

        if end_user is None and user is not None:
            end_user = create_or_update_end_user_for_user_id(app_model, user)

        api_url = 'http://example.com/api' # replace with actual API URL
        context = self.external_api_call(api_url)
        if context is None:
            raise Exception("Failed to get data from external API")
        try:
            ConversationService.delete(app_model, conversation_id, end_user, context)
            return {"result": "success"}
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")

class ConversationRenameApi(AppApiResource):

    @marshal_with(conversation_fields)
    def post(self, app_model, end_user, c_id):
        if app_model.mode != 'chat':
            raise NotChatAppError()

        conversation_id = str(c_id)

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, location='json')
        parser.add_argument('user', type=str, location='json')
        args = parser.parse_args()

        if end_user is None and args['user'] is not None:
            end_user = create_or_update_end_user_for_user_id(app_model, args['user'])

        api_url = 'http://example.com/api' # replace with actual API URL
        context = self.external_api_call(api_url)
        if context is None:
            raise Exception("Failed to get data from external API")
        try:
            return ConversationService.rename(app_model, conversation_id, end_user, args['name'], context)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")


api.add_resource(ConversationRenameApi, '/conversations/<uuid:c_id>/name', endpoint='conversation_name')
api.add_resource(ConversationApi, '/conversations')
api.add_resource(ConversationApi, '/conversations/<uuid:c_id>', endpoint='conversation')
api.add_resource(ConversationDetailApi, '/conversations/<uuid:c_id>', endpoint='conversation_detail')
