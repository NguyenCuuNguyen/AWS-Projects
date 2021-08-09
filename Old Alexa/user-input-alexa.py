#RESTORE THIS VERSION FOR MY EXPENSE SKILL
#Step1: Add my expense skill ID to lambda's trigger
#Step2: Add lambda's ARN to my expense skill's endpoint

# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import boto3
import json
import sys
import os #to retrieve env variables passed to Lambda, i.e DynamoDB table's name to persist user data
import ask_sdk_core.utils as ask_utils
import datetime
import time


#from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response


#from ask_sdk_core.skill_builder import StandardSkillBuilder #ERROR: DynamoDB support, Default API client, user's device basic details
import os #to retrieve env variables passed to Lambda, i.e DynamoDB table's name to persist user data
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components.request_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components.request_components import AbstractResponseInterceptor


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


db_region = os.environ.get('us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=db_region)
table = dynamodb.Table('alexa-demo-table')
dynamodb_adapter = DynamoDbAdapter(table_name=table, create_table=False, dynamodb_resource=dynamodb)
#global_user_name = '' #This is NOT the right way to declare global var in python

def get_user_info(access_token): #access_token comes from cookie
    #print access_token
    amazonProfileURL = 'https://api.amazon.com/user/profile?access_token=' #2br
    r = requests.get(url=amazonProfileURL+access_token)
    if r.status_code == 200:
        return r.json()
    else:
        return False

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input) #determine if the class can process the incoming request.

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # extract persistent attributes, if they exist
        # attr = handler_input.attributes_manager.persistent_attributes
        # user_name = 'Name' in attr

        # if user_name:
        #     name = attr["Name"]
        #     speak_output = "Welcome back to My Report, {name}!".format(name=name) #" and on a scale from 1 to 5, how are you feeling today?"

        # else:
        speak_output = "Welcome to My Report! What's your name?" #" and on a scale from 1 to 5, how are you feeling today?"
        reprompt="What's your name again?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots #request_envelope NOT requestEnvelope
        global global_user_name
        global_user_name = slots["Name"].value

        username ={
            'ID': slots["Name"].value
        }
        # attributes_manager = handler_input.attributes_manager
        # attributes_manager.persistent_attributes = username
        # attributes_manager.save_persistent_attributes()
        # print("save username to dynamodb successfully")
        speak_output = "Hi {name}, How are you feeling today and rank it on the scale from 1 to 5?".format(name=global_user_name)
        #TODO: persist username, maintain the same session
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output) #without ask, Alexa won't call the next function
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can report by saying a rating and your name! Let's try that"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can report your feelings or Help for details. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"
        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."
        reprompt_text = "Please ask again"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

#TODO: remove name hard code
class ReportingHandler(AbstractRequestHandler):
    """Receive user JSON input and save into DynamoDB table"""
    def can_handle(self, handler_input):
        print("yup, it's triggered")
        return ask_utils.is_intent_name("ReportIntent")(handler_input)


    def handle(self, handler_input):
        print("yup, it's inside handle")
        slots = handler_input.request_envelope.request.intent.slots #request_envelope NOT requestEnvelope
        feeling = slots["Feeling"].value
        rating = int(slots["Number"].value)
        if rating <= 3:
            rating = str(rating)
            speak_output = 'I’m sorry to hear that. {rating} for {feeling} have been updated'.format(rating=rating, feeling=feeling)
        elif rating <= 5:
            rating = str(rating)
            speak_output = 'Great! I logged {rating} for {feeling}'.format(rating=rating, feeling=feeling)
        print(feeling + " " + rating)
        reprompt_text= "Sorry I don't understand. How are you feeling on the scale of 5?"


        local_now = datetime.datetime.now()
        time2 = local_now.strftime('date: %Y-%m-%d time:%H:%M:%S')
        #TODO: retrieve username from the same Alexa session

        # user_name = table.query( #queries for all of the users with matched userID
        # KeyConditionExpression=Key("ID").eq("Craig") #& Key('password') #FIX THIS
        #)
        #attr = handler_input.attributes_manager.persistent_attributes
        #username = 'ID' in attr
        #print(username)
        print(global_user_name)
        try:
            table.put_item(
                Item={
                'ID': global_user_name, #user_name['Items'],
                'Feeling': feeling,
                'Rating':rating,
                'Date': str(time2)
                }
            )
        except Exception as e:
            print(e)
            speak_output = "Unable to save the information"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )



class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        #logger.error(exception, exc_info=True)
        print(exception)
        speak_output = "Sorry I don't understand. What's your name?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def lambda_handler(event, context):
    print(event)
    #Fetching access token
    accesstoken = str(handler_input.request_envelope.context.system.api_access_token)


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = CustomSkillBuilder(persistence_adapter=dynamodb_adapter)

sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(ReportingHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
