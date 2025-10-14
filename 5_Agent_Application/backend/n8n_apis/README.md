# n8n API Workflows for AI Agent Mastery

This folder houses all the n8n workflows built in module 5 of the AI Agent Mastery course as well as the versions of the cloud and local AI prototypes (built in module 3) turnd into API endpoints to work with the frontend we build in this module.

## Available Workflows

### Basic Iterations
Each workflow builds upon the previous one, adding new functionality:

1. **Basic_Agent_API_Endpoint.json**
   - A simple implementation showing how to exposes an agent as an API endpoint for frontend integration

2. **Auth_Agent_API_Endpoint.json**
   - Builds on the basic endpoint by adding authentication
   - Secures your agent API with proper Supabase auth
   - Ensures only authorized users can access your agent

3. **Rate_Limit_Agent_API_Endpoint.json**
   - Further enhances the authenticated endpoint with rate limiting
   - Prevents API abuse and manages resource consumption
   - Implements best practices for production-ready APIs

### Full Implementations
These workflows provide complete implementations from Module 3 of the course:

4. **Full_Prototype_Cloud_With_API.json**
   - Complete agent implementation using cloud-based AI services
   - Ready-to-use API endpoint for production applications
   - Includes all features from the iterative versions

5. **Full_Prototype_Local_With_API.json**
   - Complete agent implementation using local AI models
   - Self-contained solution for privacy-focused applications
   - Includes all features from the iterative versions

## How to Use

1. Open your n8n instance
2. Create a new workflow
3. Click on the three dots and then "Import from File" in the top right
4. Select the desired JSON file from this directory
5. Configure any credentials or settings as needed
6. Activate the workflow for the production API URL

These workflows can be used as direct replacements for the Python-based agent API implementation in Module 5 of the AI Agent Mastery course if you don't want to move past no-code tools!

## Course Integration

If you're following along with Module 5 of the AI Agent Mastery course and prefer to use n8n instead of Python for your agent backend:

1. Import one of the full implementation workflows (cloud or local)
2. Configure the workflow with your API keys and settings
3. Update your frontend environment variables to point to your n8n API endpoint
   
   a. VITE_AGENT_ENDPOINT -> set to your n8n production URL (and make sure your workflow is active)

   b. VITE_ENABLE_STREAMING -> set this to false since n8n doesn't support streaming
   
4. Continue with the course material using n8n as your agent backend

This approach allows you to leverage your existing work from Module 3 while still following the course material for building complete agentic applications.
