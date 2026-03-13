import json
import urllib3
import re

# Backend webhook URL
BACKEND_URL = "http://18.236.97.111:8000/announcements/webhook/email"

http = urllib3.PoolManager()

def extract_course_id(subject, body):
    """Extract course ID from subject or body"""
    text = f"{subject} {body}".upper()
    
    # Look for patterns like ECE101, CS101, MATH201, etc.
    match = re.search(r'\b([A-Z]{2,4}\s?\d{3})\b', text)
    if match:
        return match.group(1).replace(' ', '')
    
    return "INBOX"

def lambda_handler(event, context):
    """
    Receives email from Microsoft Graph webhook via Extension
    Forwards to backend for storage and display in dashboard
    """
    
    try:
        # Parse the event body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        # Handle Microsoft Graph validation request
        if 'validationToken' in body:
            return {
                'statusCode': 200,
                'body': body['validationToken'],
                'headers': {'Content-Type': 'text/plain'}
            }
        
        # Process email notifications
        notifications = body.get('value', [])
        
        for notification in notifications:
            resource_data = notification.get('resourceData', {})
            
            # Extract email details
            sender = 'unknown@email.com'
            if 'from' in resource_data:
                sender = resource_data['from'].get('emailAddress', {}).get('address', 'unknown@email.com')
            
            subject = resource_data.get('subject', 'No Subject')
            
            # Get body content
            body_content = ''
            if 'body' in resource_data:
                body_content = resource_data['body'].get('content', '')
            
            # Extract course ID
            course_id = extract_course_id(subject, body_content)
            
            # Get recipients
            recipients = []
            for recipient in resource_data.get('toRecipients', []):
                email = recipient.get('emailAddress', {}).get('address')
                if email:
                    recipients.append(email)
            
            # Prepare payload for backend
            payload = {
                "sender": sender,
                "subject": subject,
                "body": body_content,
                "course_id": course_id,
                "message_id": resource_data.get('id'),
                "recipients": recipients,
                "received_at": resource_data.get('receivedDateTime')
            }
            
            # Send to backend
            encoded_data = json.dumps(payload).encode('utf-8')
            
            response = http.request(
                'POST',
                BACKEND_URL,
                body=encoded_data,
                headers={'Content-Type': 'application/json'},
                timeout=10.0
            )
            
            print(f"Forwarded email to backend: {subject} from {sender}")
            print(f"Backend response: {response.status}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {len(notifications)} email(s)',
                'forwarded_to': BACKEND_URL
            })
        }
        
    except Exception as e:
        print(f"Error processing email: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
