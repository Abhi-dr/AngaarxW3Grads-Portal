from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
# import google.generativeai as genai


prompt = """You are a question HTML generator. I will provide you with the title of a programming question, and you will return the corresponding HTML code that can be used to display the question on my website. The generated HTML should focus on the problem statement only and must exclude sample input and output sections, as I will be adding those later.

Requirements:
Begin with a scenario that sets the context for the question and should be very easy.
Follow the scenario with a clear problem description.
Include any other important information as necessary.
Description should be in 200 to 300 words.
Give a clear and concise problem statement.
Use only the following HTML tags: <p>, <strong>, <h4>, <pre>, <code>, and <span> to format the content clearly.
Use of <code> and <pre> tags is encouraged for code snippets.
Output Specifications:
The response should consist solely of the HTML code, without any additional text or wrapping HTML tags.
Ensure the code is well-structured and detailed to facilitate easy integration into the existing system.

My question is: """

# Configure the Gemini API
# genai.configure(api_key="AIzaSyAwHHtOW05g-QldECq5x-6fDMNESXpM_ZA")
# model = genai.GenerativeModel('gemini-1.0-pro-latest')

@csrf_exempt  # Disable CSRF just for testing; use appropriate security in production
def generate_description(request):
        
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query = data.get("title")
            print("Query: ", query)
            if not query:
                return JsonResponse({"error": "No query provided"}, status=400)
            # Generate response from the Gemini API
            # response = model.generate_content(prompt + query)
            # return JsonResponse({"response": response.text})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
