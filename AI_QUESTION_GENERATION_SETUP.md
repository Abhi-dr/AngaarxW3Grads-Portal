# AI-Powered Question Generation Setup Guide

## Overview

This feature allows instructors to automatically generate coding questions using Google's Gemini AI. Instead of manually creating JSON files or copying them from external sources, instructors can simply enter a question title and let AI generate a complete question with test cases and driver codes.

## Features

✅ **Simple Input**: Just enter a question title or brief description  
✅ **Automatic Generation**: AI creates complete question JSON with all required fields  
✅ **Editable Output**: Review and modify generated JSON before adding to sheet  
✅ **Professional UI**: Step-by-step modal interface with loading states  
✅ **Error Handling**: Comprehensive validation and user-friendly error messages  
✅ **AJAX-Based**: Seamless experience without page reloads

## Setup Instructions

### 1. Install Dependencies

```bash
pip install google-generativeai==0.8.3
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 3. Configure Settings

Add the following to your Django settings file (e.g., `angaar_hai/settings.py`):

```python
# Gemini AI Configuration
GEMINI_API_KEY = 'your-gemini-api-key-here'
```

**Important**: For production, use environment variables:

```python
import os
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
```

And set the environment variable:

```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

### 4. Run Migrations (if needed)

```bash
python manage.py migrate
```

### 5. Restart Server

```bash
python manage.py runserver
```

## How to Use

### For Instructors:

1. **Navigate to a Sheet**
   - Go to your instructor dashboard
   - Open any sheet where you want to add questions

2. **Click "AI Generate Question"**
   - Look for the green button with sparkle icon (✨)
   - A modal will open

3. **Enter Question Details**
   - Type a question title or brief description
   - Examples:
     - "Two Sum Problem"
     - "Write a function to reverse a string"
     - "Find the maximum element in an array"
   - Be as specific as possible for better results

4. **Generate with AI**
   - Click "Generate with AI" button
   - Wait a few seconds while AI processes your request
   - A loading spinner will show progress

5. **Review Generated JSON**
   - AI will generate a complete question with:
     - Title
     - Description
     - Input/Output format
     - Constraints
     - Test cases
     - Driver codes (Python, C, C++, Java)
   - Review the JSON in the text editor

6. **Edit if Needed**
   - You can modify any part of the JSON
   - Use the "Copy JSON" button to copy to clipboard
   - Fix any issues or add more details

7. **Add to Sheet**
   - Click "Add Question to Sheet"
   - Question will be validated and added
   - You'll be redirected to the sheet page

## JSON Format

The AI generates questions in this format with **EXACTLY 10 test cases** and **ALL 4 driver codes**:

```json
{
    "title": "Question Title",
    "scenario": "Optional scenario description",
    "description": "Problem description...",
    "input_format": "Input format details...",
    "output_format": "Output format details...",
    "constraints": "Constraints details...",
    "hint": "Optional hint",
    "difficulty_level": "Easy|Medium|Hard",
    "test_cases": [
        {"input": "...", "output": "...", "is_sample": true},
        {"input": "...", "output": "...", "is_sample": true},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false},
        {"input": "...", "output": "...", "is_sample": false}
    ],
    "driver_codes": [
        {
            "language_id": 71,
            "visible_driver_code": "def solution():\n    # Python code here\n    pass",
            "complete_driver_code": "t = int(input())\nfor _ in range(t):\n    # input reading\n    #USER_CODE#\n    # call function and print result\n    print('~')"
        },
        {
            "language_id": 50,
            "visible_driver_code": "// C function",
            "complete_driver_code": "// C complete code with #USER_CODE#"
        },
        {
            "language_id": 54,
            "visible_driver_code": "// C++ function",
            "complete_driver_code": "// C++ complete code with #USER_CODE#"
        },
        {
            "language_id": 62,
            "visible_driver_code": "class Solution {\n    // Java code\n}",
            "complete_driver_code": "import java.io.*;\nimport java.util.*;\n\n#USER_CODE#\n\npublic class Main {\n    public static void main(String[] args) {\n        // driver code\n        System.out.println(\"~\");\n    }\n}"
        }
    ]
}
```

### Language IDs:
- **Python**: 71
- **C**: 50
- **C++**: 54
- **Java**: 62

### Key Requirements:
✅ **Exactly 10 test cases** (at least 2 sample, 8 hidden)  
✅ **All 4 driver codes** (Python, C, C++, Java)  
✅ **#USER_CODE# placeholder** in complete driver codes  
✅ **Print "~" after each test case** execution  
✅ **Functions must PRINT results**, not return them  
✅ **Clean input/output** in test cases (no extra text)

## Troubleshooting

### Issue: "Gemini API key not configured"

**Solution**: Make sure you've added `GEMINI_API_KEY` to your settings file and restarted the server.

### Issue: "Failed to generate question"

**Possible causes**:
- Invalid API key
- API quota exceeded
- Network connectivity issues
- AI service temporarily unavailable

**Solutions**:
- Check your API key is correct
- Verify your Google Cloud billing is active
- Try again after a few minutes
- Check your internet connection

### Issue: "Invalid JSON format"

**Solution**: The AI sometimes generates malformed JSON. Click "Back" and try again with a more specific question description, or manually edit the JSON to fix syntax errors.

### Issue: Generated question is not relevant

**Solution**: Be more specific in your question description. Instead of "array problem", try "write a function to find the maximum element in an array of integers".

### Issue: "Expected exactly 10 test cases but got X"

**Solution**: The AI didn't generate exactly 10 test cases. Click "Back" and try again. The system automatically validates and will reject any response without exactly 10 test cases.

### Issue: "Expected at least 2 sample test cases but found X"

**Solution**: Not enough sample test cases marked with `is_sample: true`. Try generating again - the AI should include at least 2 sample cases.

### Issue: "Expected 4 driver codes but got X"

**Solution**: The AI didn't generate all 4 required driver codes. Try again to get Python, C, C++, and Java implementations.

### Issue: "Missing driver codes for: [languages]"

**Solution**: Some language driver codes are missing. The system requires all 4 languages (Python, C, C++, Java). Try generating again.

### Issue: "Driver code for language_id X is missing #USER_CODE# placeholder"

**Solution**: The complete driver code doesn't include the required `#USER_CODE#` placeholder. This is needed to inject student code. Try generating again or manually add the placeholder in the correct location.

## API Limits

Google Gemini API has the following limits (as of 2024):

- **Free tier**: 60 requests per minute
- **Paid tier**: Higher limits based on your billing plan

If you're generating many questions, consider:
- Adding rate limiting in your code
- Using a paid tier
- Caching common questions

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for production
3. **Rotate keys regularly** for security
4. **Monitor API usage** to detect unauthorized access
5. **Set up billing alerts** to avoid unexpected charges

## Technical Details

### Backend (`instructor/sheet_views.py`):
- `generate_question_json()`: Handles AI generation requests
- Uses Google's `gemini-pro` model
- Validates and sanitizes AI output
- Returns structured JSON response

### Frontend (`templates/instructor/sheet/sheet.html`):
- Step-by-step modal interface
- AJAX calls for seamless experience
- Real-time validation and feedback
- Loading states and error handling

### URL Configuration (`instructor/urls.py`):
- Endpoint: `/instructor/generate_question_json/`
- Method: POST
- AJAX-only requests

## Future Enhancements

Potential improvements:
- Support for different AI models
- Batch question generation
- Question difficulty customization
- Multi-language support
- Question history and favorites
- AI-powered question improvement suggestions

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs for detailed error messages
3. Verify API key and network connectivity
4. Contact system administrator

## License

This feature is part of the Angaar Batch portal system.

---

**Last Updated**: January 2025  
**Version**: 1.0.0
