import http.server
import json
import asyncio
import requests

from botbuilder.schema import (Activity, ActivityTypes)
from botframework.connector import ConnectorClient
from botframework.connector.auth import (MicrosoftAppCredentials,
                                         JwtTokenValidation, SimpleCredentialProvider)

APP_ID = '5e5a4f07-5965-46d6-9d11-e7d444c0a56e'
APP_PASSWORD = 'jpiearQHIYE8]%[oAV7519@'

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'b8529efe29f644f4acf6a6ffaa3ee014',
}

params ={
    # Query parameter
    'q': 'What is AI?',
    # Optional request parameters, set to default values
    'timezoneOffset': '0',
    'verbose': 'false',
    'spellCheck': 'false',
    'staging': 'false',
}


class BotRequestHandler(http.server.BaseHTTPRequestHandler):

    @staticmethod
    def __create_reply_activity(request_activity, text):
        return Activity(
            type=ActivityTypes.message,
            channel_id=request_activity.channel_id,
            conversation=request_activity.conversation,
            recipient=request_activity.from_property,
            from_property=request_activity.recipient,
            text=text,
            service_url=request_activity.service_url)

    def __handle_conversation_update_activity(self, activity):
        self.send_response(202)
        self.end_headers()
        if activity.members_added[0].id != activity.recipient.id:
            credentials = MicrosoftAppCredentials(APP_ID, APP_PASSWORD)
            reply = BotRequestHandler.__create_reply_activity(activity, 'Hello and welcome to the AI & Testing bot!')
            connector = ConnectorClient(credentials, base_url=reply.service_url)
            connector.conversations.send_to_conversation(reply.conversation.id, reply)

    def __handle_message_activity(self, activity):
        self.send_response(200)
        self.end_headers()
        credentials = MicrosoftAppCredentials(APP_ID, APP_PASSWORD)
        connector = ConnectorClient(credentials, base_url=activity.service_url)
        # reply = BotRequestHandler.__create_reply_activity(activity, 'You said: %s' % activity.text)
        params['q'] = activity.text
        try:
            r = requests.get(
                'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/f3059921-7e30-4730-a349-09e37e46cd6e',
                headers=headers, params=params)
            data = r.json()
            print(data)
            main_query = "None"
            subject = "None"
            sec_query = "None"
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
        for entity in data['entities']:
            t = entity['type']
            if t == 'Query::Main Query':
                main_query = entity['entity']
            elif t == 'Subject':
                subject = entity['entity']
            elif t == 'Query::Secondary Query':
                sec_query = entity['entity']
        # print(main_query)
        reply = BotRequestHandler.__create_reply_activity(activity, "The main query is: " + main_query +
                                                          ", the subject is: " + subject)
        connector.conversations.send_to_conversation(reply.conversation.id, reply)

    def __handle_authentication(self, activity):
        credential_provider = SimpleCredentialProvider(APP_ID, APP_PASSWORD)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(JwtTokenValidation.assert_valid_activity(
                activity, self.headers.get("Authorization"), credential_provider))
            return True
        except Exception as ex:
            self.send_response(401, ex)
            self.end_headers()
            return False
        finally:
            loop.close()

    def __unhandled_activity(self):
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(str(body, 'utf-8'))
        activity = Activity.deserialize(data)

        if not self.__handle_authentication(activity):
            return

        if activity.type == ActivityTypes.conversation_update.value:
            self.__handle_conversation_update_activity(activity)
        elif activity.type == ActivityTypes.message.value:
            self.__handle_message_activity(activity)
        else:
            self.__unhandled_activity()


try:
    SERVER = http.server.HTTPServer(('localhost', 3979), BotRequestHandler)
    print('Started http server on localhost:3979')
    SERVER.serve_forever()
except KeyboardInterrupt:
    print('^C received, shutting down server')
    SERVER.socket.close()