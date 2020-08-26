import random
from collections import defaultdict
from django.apps import apps
import boto3
import json
from botocore.exceptions import ClientError



def create_new_ref_number():
    return str(random.sample(range(999999), 1))


#class to bulk upload objects
class BulkCreateManager(object):
    """
    This helper class keeps track of ORM objects to be created for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is created for all models.
    """

    def __init__(self, chunk_size=100):
        self._create_queues = defaultdict(list)
        self.chunk_size = chunk_size

    def _commit(self, model_class):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._create_queues[model_key])
        self._create_queues[model_key] = []

    def add(self, obj):
        """
        Add an object to the queue to be created, and call bulk_create if we
        have enough objs.
        """
        model_class = type(obj)
        model_key = model_class._meta.label
        self._create_queues[model_key].append(obj)
        if len(self._create_queues[model_key]) >= self.chunk_size:
            self._commit(model_class)

    def done(self):
        """
        Always call this upon completion to make sure the final partial chunk
        is saved.
        """
        for model_name, objs in self._create_queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))

class Notification:
    #Send for subscription

    def SubscribeEmployeeObj(self, phone_num):

        context ={}

        sns = boto3.client('sns')

        topic_arn = 'arn:aws:sns:us-east-1:321504535921:intellidata-employee-communication-topic'

        #obj = get_object_or_404(Member, pk = pk)

        number = str(phone_num).strip()
        #number_array = number.split()
        #print(number_array)
        #number = number_array[3]
        #number=number.split("=")[1]
            #to_email_address=to_email_address.strip(")
        #number=number.replace('"', '')
        print("that is what I see " + number )
            #emailaddr = str(form["email"])

            # Add  Subscribers
        try:
                response = sns.subscribe(
                            TopicArn=topic_arn,
                            Protocol='SMS',
                            Endpoint=number
                           )
            # Display an error if something goes wrong.
        except ClientError as e:
                print(e.response['Error']['Message'])
        else:
                print("Subscription done!")
                subscription_arn = response["SubscriptionArn"]
                return subscription_arn
                #obj.sms = "Phone Number Subscribed On " + str(datetime.date.today())



    def TextEmployeeObj(self, subscription_arn):

        context = {}

        sns = boto3.client('sns')

        topic_arn = 'arn:aws:sns:us-east-1:321504535921:intellidata-employee-communication-topic'

        message = "Your data has been processed by the IntelliData platform. We will let you know when your enrollment becomes 100% complete!"
        messageJSON = json.dumps({"message":message})

        #obj = get_object_or_404(Member, pk = pk)

        try:
                response=sns.publish(
                            TopicArn=topic_arn,
                            Message=message
                         )

            # Display an error if something goes wrong.
        except ClientError as e:
                print(e.response['Error']['Message'])
        else:
                print("SMS sent!")
                # Delete subscription
                sns.unsubscribe(SubscriptionArn=subscription_arn)

                #obj.sms = "SMS Notification Sent on " + str(datetime.date.today())



    def EmailEmployeeObj(self, email_addr):

        context = {}

        message = "Member enrollment"
        messageJSON = json.dumps({"message":message})

        #obj = get_object_or_404(Member, pk = pk)

        to_email_address = str(email_addr).strip()
        #print(to_email)
        #to_email_array = to_email.split()
        #to_email_value = to_email_array[3]
        #to_email_address=to_email_value.split("=")[1]
            #to_email_address=to_email_address.strip(")
        #to_email_address=to_email_address.replace('"', '')
            #to_email_address = "'{}'".format(to_email_address)

            #print("what we see is " + to_email_address)
            #to_email = 'svjt78@gmail.com'
        from_email = 'suvojit.dt@gmail.com'
                # Replace sender@example.com with your "From" address.
            # This address must be verified with Amazon SES.

        SENDER = from_email

            # Replace recipient@example.com with a "To" address. If your account
            # is still in the sandbox, this address must be verified.
        RECIPIENT = to_email_address
        print("email address In am seeing " +  to_email_address)

            # Specify a configuration set. If you do not want to use a configuration
            # set, comment the following variable, and the
            # ConfigurationSetName=CONFIGURATION_SET argument below.
            #CONFIGURATION_SET = "ConfigSet"

            # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
        AWS_REGION = "us-east-1"

            # The subject line for the email.
        SUBJECT = "Enrollment"

            # The email body for recipients with non-HTML email clients.
        BODY_TEXT = ("Your data has been processed by the IntelliData platform. We will let you know when your enrollment becomes 100% complete!\r\n"
                         "Your data has been processed by the IntelliData platform. "
                         "We will let you know when your enrollment becomes 100% complete!"
                        )

            # The HTML body of the email.
        BODY_HTML = """<html>
            <head></head>
            <body>
              <h1>Your data has been processed by the IntelliData platform. We will let you know when your enrollment becomes 100% complete!</h1>
              <p>This email was sent with
                <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
                <a href='https://aws.amazon.com/sdk-for-python/'>
                  AWS SDK for Python (Boto)</a>.</p>
            </body>
            </html>
                        """

            # The character encoding for the email.
        CHARSET = "UTF-8"

            # Create a new SES resource and specify a region.
        client = boto3.client('ses',region_name=AWS_REGION)

            # Try to send the email.
        try:
                #Provide the contents of the email.
                response = client.send_email(
                    Destination={
                        'ToAddresses': [
                            RECIPIENT,
                        ],
                    },
                    Message={
                        'Body': {
                            'Html': {
                                'Charset': CHARSET,
                                'Data': BODY_HTML,
                            },
                            'Text': {
                                'Charset': CHARSET,
                                'Data': BODY_TEXT,
                            },
                        },
                        'Subject': {
                            'Charset': CHARSET,
                            'Data': SUBJECT,
                        },
                    },
                    Source=SENDER,
                    # If you are not using a configuration set, comment or delete the
                    # following line
                    #ConfigurationSetName=CONFIGURATION_SET,
                )
            # Display an error if something goes wrong.
        except ClientError as e:
                print(e.response['Error']['Message'])
        else:
                print("Email sent! Message ID:"),
                print(response['MessageId'])
                #obj.emailer = "Email Notification Sent on " + str(datetime.date.today())


#class built to contain the different API domain names
class ApiDomains:

    product='https://em6hzw5v68.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI'
    employee='https://em6hzw5v68.execute-api.us-east-1.amazonaws.com/Prod/intellidataEmployeeAPI'
    employer='https://em6hzw5v68.execute-api.us-east-1.amazonaws.com/Prod/intellidataEmployerAPI'
    transmission='https://em6hzw5v68.execute-api.us-east-1.amazonaws.com/Prod/intellidataTransmissionAPI'
