import boto3
import json
import time
import os

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name="us-west-2")
ses = boto3.client('ses', region_name="us-west-2")
s3 = boto3.client('s3')
job_name = f"transcription-job-{int(time.time())}"
email = "<email>"

def _send_email(summary_text, recipient, subject="Your Audio Summary"):
    response = ses.send_email(
        Source=email,
        Destination={'ToAddresses': [recipient]},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {
                    'Data': summary_text
                }
            }
        }
    )
    print("Email sent! Message ID:", response['MessageId'])

def _summarize(event, context):
    # Extract S3 object details from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    filename_with_ext = os.path.basename(key)
    filename_no_ext = os.path.splitext(filename_with_ext)[0]
    file_name = f"summary/{filename_no_ext}.json"

    # Extract transcript text
    response = s3.get_object(Bucket=bucket_name, Key=key)
    json_data = json.loads(response['Body'].read().decode('utf-8'))
    transcription_text = json_data['results']['transcripts'][0]['transcript']
    #print(transcription_text)
    
    # Build summarization prompt for DeepSeek
    print("Started summarizing...")
    prompt = f"Summarize the following transcription:\n\n{transcription_text}\n\nSummary:"

    # Invoke DeepSeek R1 model
    payload = {
        "prompt": prompt,
        "temperature": 0.7, 
        "top_p": 0.9,
        "max_tokens": 200,
        #"stop": string array
    }
    model_id = "us.deepseek.r1-v1:0"
    try:
        bedrock_response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )

        # Parse and print summar
        model_response = json.loads(bedrock_response["body"].read())
        print("Completed summarizing!")

        choices = model_response["choices"]
        summary = None
        for index, choice in enumerate(choices):
            summary = f"{choice['text']}"
        #print(summary)
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
    
    # Store the summary back to S3 or take other actions
    summary_key = f"{file_name}"
    s3.put_object(Bucket=bucket_name, Key=summary_key, Body=summary)
    
    # Send email
    _send_email(summary, email)
    print(f"Email sent to {email}")

    return {
        'statusCode': 200,
        'body': json.dumps(f"Summary generated and saved: {summary_key}")
    }

def lambda_handler(event, context):
    _summarize(event, context)
