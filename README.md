TA Copilot
TA Copilot is an AI-powered teaching support platform that helps instructors and teaching assistants manage course communication at scale. It integrates directly with Outlook, Canvas, and AWS to automatically process student emails, generate grounded draft responses, surface regrade cases, organize inbox workflows, and provide actionable insights about student confusion, sentiment, and communication patterns.

The system is designed to reduce repetitive email overhead while preserving instructor control. Routine questions are answered with AI-generated drafts grounded in official course materials, while sensitive, ambiguous, or high-risk messages are escalated to a TA or instructor for review.

What the platform does
TA Copilot turns incoming course email into structured, actionable workflows.

It can:

ingest student emails from Outlook through a browser extension and webhook pipeline
classify messages into routine, regrade, or escalation categories
generate suggested responses using course announcements, assignments, rubrics, FAQs, and prior approved responses
detect regrade-related messages and route them into a structured review flow
surface live course context from Canvas, including announcements, assignments, and grade information
store all processed email records and workflow states in DynamoDB
provide dashboard insights such as weekly question volume, unanswered emails, common confusion topics, sentiment trends, and regrade patterns
expose clean backend APIs for the extension, dashboard, and future integrations
Core idea
The project solves a common instructional bottleneck: course staff spend too much time answering repetitive emails, searching through announcements, checking grading context, and triaging regrade requests.

TA Copilot addresses that by combining:

Microsoft Graph and an Outlook-side extension for inbox access
AWS Lambda and API Gateway for event ingestion
FastAPI for backend orchestration and application APIs
Amazon Bedrock for classification and response generation
DynamoDB for persistent workflow storage
Canvas MCP for real-time academic context
The result is a teaching copilot that is fast, grounded, and workflow-aware.

System architecture
The complete system consists of four major layers.

1. Outlook ingestion layer
A Chrome extension authenticates with Microsoft and accesses Outlook inbox data through the Microsoft Graph API. It monitors incoming email activity and forwards normalized message payloads to a webhook endpoint.

This layer is responsible for:

Microsoft authentication
inbox polling or event subscription handling
fetching full email details
forwarding email payloads to the backend ingestion path
2. AWS event and processing layer
Incoming webhook events are received through API Gateway and processed by AWS Lambda. Lambda normalizes the payload, validates required fields, enriches metadata where needed, and passes the email into the backend.

This layer is responsible for:

receiving webhook traffic
converting provider-specific payloads into a standard email record
triggering downstream processing
serving as the secure bridge between Outlook events and backend storage
3. AI backend layer
The FastAPI backend is the core orchestration layer of the system. It stores emails, runs classification and reply generation, manages regrade records, exposes data for review tools, and aggregates insights.

This layer is responsible for:

email persistence
AI classification
suggested reply generation
regrade workflow management
insights generation
Canvas context retrieval
API access for frontend and extension clients
4. Academic context layer
Canvas MCP provides real-time access to course information such as announcements, assignments, and grade-related data. This context is injected into the AI workflow so responses are grounded in the actual state of the course.

This layer is responsible for:

retrieving course details
retrieving announcements
retrieving assignments and due dates
retrieving relevant grade context
giving the AI trusted course data before it generates a response
AWS services used
Amazon Bedrock
Amazon Bedrock powers the intelligence layer of the system. It is used to classify incoming emails, determine escalation requirements, assign routing targets, extract insight tags, and generate suggested replies.

The AI output is structured and normalized into fields such as:

classification
sentiment
escalation requirement
assignment target
insight tags
suggested reply
Amazon DynamoDB
DynamoDB stores the structured backend state.

Primary tables include:

Emails
RegradeRequests
The Emails table stores:

sender
subject
body
received timestamp
classification
sentiment
escalation state
insight tags
assigned reviewer
suggested reply
source metadata such as webhook message identifiers
The RegradeRequests table stores:

request id
linked email id
student email
course id
assignment name
reason
workflow status
AWS Lambda
Lambda serves as the event-processing layer between the incoming webhook and the backend. It receives email events, normalizes provider payloads, and forwards them into the application flow.

Amazon API Gateway
API Gateway provides the public webhook entry point used by the Outlook extension and future external integrations.

Amazon EC2
EC2 is used to host the deployed application stack, including the AI agent environment and backend services.

Backend API
The backend exposes a set of REST endpoints for ingestion, workflow management, and analytics.

Key endpoints include:

GET /health
GET /emails
POST /emails
GET /emails/{email_id}
POST /emails/{email_id}/classify
POST /emails/{email_id}/generate-reply
GET /insights/summary
GET /regrade
POST /regrade
GET /canvas/tools
POST /canvas/call
GET /canvas/course-context/{course_identifier}
These APIs allow the platform to:

ingest new messages
retrieve inbox records
classify messages
generate draft responses
manage regrade requests
inspect Canvas context
support dashboards and future administrative tools
AI workflow
When a new email arrives, TA Copilot performs the following sequence:

The email is received from Outlook and normalized into a standard record.
The email is stored in DynamoDB.
The backend retrieves relevant course context from Canvas.
Amazon Bedrock analyzes the email using both the message content and trusted course data.
The system returns:
a classification
a sentiment label
an escalation decision
routing guidance
insight tags
a suggested reply draft
The backend updates the stored email record.
The extension or dashboard displays the result to course staff.
Routine emails are marked as ready for review. Regrade and escalation cases are routed to human staff.

Canvas integration
The Canvas integration is one of the most important parts of the system because it grounds the AI in actual course data.

TA Copilot uses Canvas MCP to retrieve:

course details
announcements
assignment information
grade-related context
This allows the model to answer questions such as:

when is the assignment due
was this already announced
what does the current rubric or assignment say
what grade-related context is available for this student
Instead of producing generic answers, the AI responds with course-specific, up-to-date context.

Extension
The browser extension acts as the Outlook-side interface for instructors or TAs.

Its responsibilities include:

authenticating with Microsoft
polling or subscribing to inbox activity
retrieving email details using Microsoft Graph
forwarding normalized messages to the webhook/backend pipeline
serving as the foundation for future UI enhancements such as suggested reply overlays and inbox controls
Dashboard and insights
TA Copilot also functions as an analytics layer for course communication.

The insights workflow summarizes:

weekly question volume
unanswered emails
common confusion topics
sentiment distribution
regrade frequency
communication patterns across the course
This gives instructors a course-level view of what students are struggling with and what content may need clarification.

Regrade support
Regrade messages are treated as a dedicated workflow, not just another email.

The system can:

detect regrade intent
extract the reason
link the request to the source email
create a structured regrade record
route the case to the appropriate reviewer
This helps instructors separate normal inbox traffic from grading disputes and academic review requests.

Design principles
TA Copilot was built around five principles:

grounded responses over hallucinated ones
instructor review over blind automation
structured workflows over raw email chaos
real course context over generic chatbot behavior
scalable APIs over one-off scripts
The goal is not to replace instructors. The goal is to remove repetitive friction so instructors can spend more time on high-value student interactions.

Deployment
The backend is designed to run cleanly in AWS and supports EC2-based deployment. It includes deployment assets for:

environment-based configuration
Nginx reverse proxy
systemd service management
DynamoDB-backed persistence
Bedrock integration
This makes it suitable for both hackathon demonstration and continued iteration after the event.

End-to-end summary
TA Copilot is a full-stack teaching support system that connects Outlook, Canvas, and AWS into a single AI-assisted workflow. It receives student emails, enriches them with live course context, uses Bedrock to classify and draft responses, stores structured records in DynamoDB, routes complex cases to humans, and provides a high-level view of communication trends across the course.

It transforms the instructor inbox from a passive message queue into an intelligent operational system.
