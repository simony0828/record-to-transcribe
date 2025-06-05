import boto3
import json
import time
import os

# Initialize AWS clients
transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')
job_name = f"transcription-job-{int(time.time())}"

def _transcribe(event, context):
    # Extract S3 object details from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Start transcription job
    job_uri = f"s3://{bucket_name}/{key}"

    filename_with_ext = os.path.basename(key)
    filename_no_ext = os.path.splitext(filename_with_ext)[0]
    file_name = f"transcribe/{filename_no_ext}.json"
    
    # Start transcription job using AWS Transcribe
    print("Started transcribing...")
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        #MediaFormat='wav',  # Adjust based on your audio format
        MediaFormat='mp4',  # Adjust based on your audio format
        LanguageCode='en-US',  # Adjust based on the language of the audio
        OutputBucketName=bucket_name,  # Save the transcription result to the same bucket
        OutputKey=file_name,
    )
    print("Completed transcribing!")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Transcription job started successfully')
    }

def lambda_handler(event, context):
    _transcribe(event, context)
