from ast import Return
from distutils.command.build import build
from importlib.resources import path
from turtle import pos
from unittest import result
from custom_encoder import CustomEncoder
from urllib import response
import boto3
import json
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodbTableName = 'Emp_Master'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodbTableName)

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
healthPath = '/health'
employeePath = '/employee'
employeesPath = '/employees'


def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']
    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == getMethod and path == employeePath:
        response = getEmployee(event['queryStringParameters']['Emp_Id'])
    elif httpMethod == getMethod and path == employeesPath:
        response = getEmployees()
    elif httpMethod == postMethod and path == employeePath:
        response = saveEmployee(json.loads(event['body']))
    elif httpMethod == patchMethod and path == employeePath:
        requestBody = json.loads(event['body'])
        response = modifyEmployee(requestBody['Emp_Id'], requestBody['updateKey'], requestBody['updateValue'])
    else:
        response = buildResponse(404, 'Not Found')
    return response

def getEmployee(Emp_Id):
    try:
        response = table.get_item(
            Key={
                'Emp_Id': Emp_Id
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['item'])
        else:
            return buildResponse(404, {'message': 'Emp_Id: %s not found' % Emp_Id})
    except:
        logger.exception('Do your custom error handling here. I am just gonna log it out there!!')


def getEmployees():
    try:
        response = table.scan()
        result = response['Item']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            result.extend(response['Item'])
        body = {
            'employees': response
        }
        return buildResponse(200, body)
    except:
        logger.exception('Do your custom error handling here. I am just gonna log it out there!!')

def saveEmployee(requestBody):
    try:
        table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body)
    except:
        logger.exception('Do your custom error handling here. I am just gonna log it out there!!')

def modifyEmployee(Emp_Id, updateKey, updateValue):
    try:
        response = table.update_item(
            Key={
                'Emp_Id': Emp_Id
            },
            UpdateExpression='set %s = :value' % updateKey,
            ExpressionAttributeValue={
                ':value': updateValue
            },
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'UpdatedAttributes': response
        }
        return buildResponse(200, body)

    except:
        logger.exception('Error')


def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response



