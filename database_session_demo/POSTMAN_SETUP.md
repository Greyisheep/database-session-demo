# Postman Collection for Multimodal API

This collection provides comprehensive testing for the Multimodal Database Session Demo API.

## 🚀 Quick Setup

### 1. Import the Collection
1. Open Postman
2. Click **Import** → **Upload Files**
3. Select `Multimodal_API_Postman_Collection.json`
4. Click **Import**

### 2. Start the API Server
```bash
cd /Users/claret/Documents/code/database-session-demo/database_session_demo
docker compose up -d
```

### 3. Verify API is Running
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## 📋 Collection Structure

### **Health & Info**
- **Health Check** - Verify API is running
- **API Info** - Get endpoint information

### **Chat Endpoints**
- **Text Chat - Simple** - Basic text conversation
- **Text Chat - Continue Session** - Continue existing session
- **Text Chat - Force New Session** - Create new session

### **File Upload**
- **Upload Text File** - Upload and analyze text files
- **Upload Image File** - Upload and analyze images
- **Upload PDF File** - Upload and analyze PDFs

### **Base64 Data URI**
- **Base64 Text** - Send base64 encoded text
- **Base64 Image** - Send base64 encoded images

### **Session Management**
- **List User Sessions** - View all sessions for a user
- **Delete Session** - Remove a specific session

### **Advanced Scenarios**
- **Multimodal Conversation** - Text + file upload
- **Session Continuity Test** - Test conversation memory

## 🔧 Variables

The collection uses these variables:
- `base_url`: http://localhost:8000
- `user_id`: postman_test_user
- `session_id`: Auto-captured from responses

## 🎯 Testing Workflow

### **Basic Testing**
1. Start with **Health Check**
2. Try **Text Chat - Simple**
3. Check **List User Sessions** to see the session
4. Test **Text Chat - Continue Session**

### **File Upload Testing**
1. Use **Upload Image File** with any image
2. Try **Upload Text File** with a text document
3. Test **Multimodal Conversation** with text + file

### **Session Management**
1. Create multiple sessions with different user IDs
2. Use **List User Sessions** to see all sessions
3. Test **Delete Session** to clean up

## 🐛 Troubleshooting

### **Connection Issues**
- Ensure Docker containers are running: `docker compose ps`
- Check API health: http://localhost:8000/health

### **File Upload Issues**
- Supported formats: PNG, JPG, PDF, TXT, JSON
- Max file size: 10MB
- Use proper MIME types

### **Session Issues**
- Sessions auto-capture from responses
- Use **List User Sessions** to see all sessions
- Delete old sessions to clean up

## 📊 Expected Responses

### **Successful Chat Response**
```json
{
  "success": true,
  "message": "Agent response generated successfully",
  "data": {
    "response": "Agent's response text here",
    "session_id": "uuid-here",
    "user_id": "your-user-id",
    "message_count": 1,
    "has_files": false
  }
}
```

### **Session List Response**
```json
{
  "success": true,
  "message": "Found X sessions for user",
  "data": [
    {
      "id": "session-uuid",
      "user_id": "user-id",
      "last_update": 1234567890.123,
      "event_count": 5,
      "state": {
        "has_files": true,
        "message_count": 3,
        "conversation_started": true
      }
    }
  ]
}
```

## 🎉 Tips

- **Auto-capture**: Session IDs are automatically captured from responses
- **File Testing**: Use the provided test files or upload your own
- **Session Continuity**: Test conversation memory across multiple requests
- **Error Handling**: Check the console for detailed error messages

Happy testing! 🚀
