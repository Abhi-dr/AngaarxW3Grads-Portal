from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time, json
import requests
import asyncio
import aiohttp
import random
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import re
from accounts.models import Student
from .models import RecommendedQuestions
from .models import Sheet, Question, TestCase, Submission, DriverCode, Streak
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# Import Django's asynchronous utilities
from asgiref.sync import sync_to_async, async_to_sync

# Constants
JUDGE0_URL = "https://theangaarbatch.in/judge0/submissions"
HEADERS = {
    
    "Content-Type": "application/json"
}
DRIVER_CODE_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours (increased from previous value)

# For backward compatibility - keep this but we'll use aiohttp for async operations
judge0_session = requests.Session()
retries = Retry(
    total=3,  # Maximum number of retries
    backoff_factor=0.5,  # Backoff factor for retries
    status_forcelist=[502, 503, 504],  # Retry on these HTTP status codes
    
)
judge0_session.mount('https://', HTTPAdapter(
    max_retries=retries,
    pool_connections=20,  # Keep 20 connections in the pool
    pool_maxsize=50  # Allow up to 50 total connections
))

# Global aiohttp session for connection pooling
_aiohttp_session = None

# Fixed connection settings for aiohttp (reused across sessions)
AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=60)
AIOHTTP_CONNECTOR_PARAMS = {
    "limit": 100,  # Max connections overall
    "limit_per_host": 20,  # Max connections per host
    "ttl_dns_cache": 300,  # DNS cache TTL in seconds
    "enable_cleanup_closed": True
}

# Event loop management
def run_async_safely(coroutine):
    """
    Safely run an async coroutine in sync context, handling event loop issues.
    This is particularly important in Django/Windows environments where
    event loop handling can be problematic.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        
        # If the loop is closed, create a new one
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
        # Run the coroutine in the loop and return the result
        return loop.run_until_complete(coroutine)
    except RuntimeError as e:
        # This handles "no running event loop" and other runtime errors
        if str(e).startswith("There is no current event loop in thread"):
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Run the coroutine in the new loop
            return loop.run_until_complete(coroutine)
        else:
            # Reraise any other runtime errors
            raise

async def get_aiohttp_session():
    """Get or create a shared aiohttp session with connection pooling"""
    global _aiohttp_session
    if _aiohttp_session is None or _aiohttp_session.closed:
        conn = aiohttp.TCPConnector(**AIOHTTP_CONNECTOR_PARAMS)
        _aiohttp_session = aiohttp.ClientSession(
            connector=conn,
            timeout=AIOHTTP_TIMEOUT,
            headers=HEADERS
        )
    return _aiohttp_session

async def close_aiohttp_session():
    """Properly close the aiohttp session"""
    global _aiohttp_session
    if _aiohttp_session and not _aiohttp_session.closed:
        await _aiohttp_session.close()
        _aiohttp_session = None

# Cache timeout settings (in seconds)
TEST_CASE_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
QUESTION_CACHE_TIMEOUT = 60 * 60 * 6  # 6 hours


@login_required(login_url="login")
def problem(request, slug):
    """
    Render the problem page with question details and sample test cases, with Redis caching.
    """
    # Create a cache key for the question
    cache_key = f"question:{slug}"
    
    # Try to get from cache first
    cached_question_data = cache.get(cache_key)
    
    if cached_question_data:
        # Since we can't serialize the entire Question object, we'll cache components
        # and reassemble on retrieval
        question = get_object_or_404(Question, slug=slug)
        sample_test_cases = cached_question_data.get('sample_test_cases')
        sheet = cached_question_data.get('sheet')
        
        # Apply cached properties to question object
        if cached_question_data.get('scenario'):
            question.scenario = cached_question_data.get('scenario')
            
        question.description = cached_question_data.get('description')
        
        return render(request, 'practice/problem.html', {
            'question': question,
            'sample_test_cases': sample_test_cases,
            'sheet': sheet
        })
    
    try:
        question = get_object_or_404(Question, slug=slug)
        
        sheet = Sheet.objects.filter(questions=question, is_approved=True).first()

        if sheet and not sheet.is_enabled:
            messages.info(request, "This question is in the sheet which is disabled now. Try Later.")
            return redirect('problem_set')
        
        if sheet and sheet.is_sequential:
            # Get all enabled questions for the user
            enabled_questions = sheet.get_enabled_questions_for_user(request.user)
            
            # Check if the question is enabled for the user
            if question not in enabled_questions:
                messages.info(request, "Beta jb tu paida nhi hua tha tb m URL se khelta tha. Mehnt kr 🙂")
                return redirect('sheet', slug=sheet.slug)
                
        if question.scenario:
            question.scenario = convert_backticks_to_code(question.scenario)
        question.description = convert_backticks_to_code(question.description)
        
        sample_test_cases = list(TestCase.objects.filter(question=question, is_sample=True))
        
        # Cache the question data
        cache_data = {
            'scenario': question.scenario,
            'description': question.description,
            'sample_test_cases': sample_test_cases,
            'sheet': sheet
        }
        
        cache.set(cache_key, cache_data, timeout=QUESTION_CACHE_TIMEOUT)
        
        return render(request, 'practice/problem.html', {
            'question': question,
            'sample_test_cases': sample_test_cases,
            'sheet': sheet
        })
    except Exception as e:
        print(f"Error loading problem page: {e}")
        return JsonResponse({"error": "Error from backend: {e}" + str(e)}, status=500)


@login_required(login_url="login")
def execute_code(request):
    print("🛠️ execute_code called")
    
    if request.method == 'POST':
        
        language_id = request.POST.get('language_id')
        source_code = request.POST.get('source_code')
        input_data = request.POST.get('input_data')  # Get input data from the request
        
        # Ensure required fields are provided
        if not (language_id and source_code):
            return JsonResponse({"error": "Missing required fields (language_id, source_code)"}, status=400)

        # Encode source code and input data
        encoded_code = base64.b64encode(source_code.encode('utf-8')).decode('utf-8')
        encoded_input = base64.b64encode(input_data.encode('utf-8')).decode('utf-8') if input_data else None

        # Prepare submission payload
        data = {
            "source_code": encoded_code,
            "language_id": language_id,
            "cpu_time_limit": 1,
            "cpu_extra_time": 1,
            "base64_encoded": True,
            "stdin": encoded_input  # Add input data to the payload
        }

        try:
            response = requests.post(f"{JUDGE0_URL}?base64_encoded=true", json=data, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)

        if response.status_code == 201:
            token = response.json().get('token')
            
            if not token:
                return JsonResponse({"error": "Failed to retrieve submission token"}, status=500)

            for i in range(10):  # Maximum of 10 attempts
                try:
                    result_response = requests.get(f"{JUDGE0_URL}/{token}?base64_encoded=true", headers=HEADERS, timeout=10)
                    result_response.raise_for_status()
                    result = result_response.json()
                except requests.exceptions.RequestException as e:
                    return JsonResponse({"error": f"Polling failed: {str(e)}"}, status=500)

                status_id = result.get('status', {}).get('id')
                status_description = result.get('status', {}).get('description', 'Unknown Status')

                if status_id == 3:  # ✅ Accepted (Successful Execution)
                    output = result.get('stdout')
                    if output:
                        decoded_output = base64.b64decode(output).decode('utf-8')
                        return JsonResponse({"output": decoded_output, "status": status_description})

                elif status_id in [5, 6, 7, 11]:  # ❌ Error Cases
                    error_output = (
                        result.get('stderr') or
                        result.get('compile_output') or
                        result.get('message')
                    )
                    if error_output:
                        decoded_error = base64.b64decode(error_output).decode('utf-8', errors='replace')
                        return JsonResponse({"error": decoded_error, "status": status_description})
    
                time.sleep(1)  # Poll every 1 second

            return JsonResponse({"error": "Timeout while waiting for the result"}, status=408)

        return JsonResponse({"error": "Failed to submit code to Judge0"}, status=response.status_code)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# =====================================================================================================
# ========================================= HELPER FUNCTIONS ==========================================
# =====================================================================================================

def normalize_output(output):
    """
    Normalize output for consistent comparison by stripping extra spaces
    and normalizing newline characters.
    """
    
    # print("\nOUTPUT IN NORMALIZE FUNCTION:", output)
        
    if not output:
        return ""
    return output.replace("\r\n", "\n").strip()


# Helper functions for async database operations
@sync_to_async
def get_question_by_id(question_id):
    return Question.objects.get(id=question_id)

@sync_to_async
def get_test_cases_for_question(question, is_sample=False):
    return list(TestCase.objects.filter(question=question, is_sample=is_sample))

# In-memory cache for test cases with LRU cache decorator
# Use a regular dict for caching instead of lru_cache to avoid coroutine reuse issues
_test_cases_cache = {}

async def get_test_cases_async(question_id):
    """
    Get test cases for a question using async operations with improved in-memory caching.
    Uses Django's sync_to_async for database operations.
    """
    # Check cache first
    if question_id in _test_cases_cache:
        return _test_cases_cache[question_id]
        
    # Get the question using Django's sync_to_async utility
    question = await get_question_by_id(question_id)
    
    # Try to get non-sample test cases first
    test_cases = await get_test_cases_for_question(question, is_sample=False)
    
    # If no test cases found, check if we have any sample test cases to use
    if not test_cases:
        test_cases = await get_test_cases_for_question(question, is_sample=True)
    
    # Cache the result
    if len(_test_cases_cache) > 100:  # Limit cache size
        _test_cases_cache.clear()
    _test_cases_cache[question_id] = test_cases
    
    return test_cases

# Get test cases for a question with improved caching strategy.
# Uses both Redis cache and in-memory LRU cache for optimal performance.
def get_test_cases(question):
    """
    Get test cases for a question with improved caching strategy.
    Uses both Redis cache and in-memory LRU cache for optimal performance.
    """
    # Try to get from Redis cache first
    cache_key = f"test_cases:{question.id}"
    cached_test_cases = cache.get(cache_key)
    
    if cached_test_cases:
        # Deserialize JSON to Python dictionary
        test_cases_data = json.loads(cached_test_cases)
        
        # Create TestCase objects from the cached data
        test_cases = []
        for tc_data in test_cases_data:
            tc = TestCase(
                id=tc_data.get('id'),
                question_id=tc_data.get('question_id'),
                input_data=tc_data.get('input_data'),
                expected_output=tc_data.get('expected_output'),
                is_sample=tc_data.get('is_sample', False),
                weight=tc_data.get('weight', 1.0)
            )
            test_cases.append(tc)
            
        return test_cases
    
    # Try to get from in-memory cache
    try:
        # Run the async function in a synchronous context
        test_cases = asyncio.run(get_test_cases_async(question.id))
        
        # If we have test cases from memory cache, also store in Redis cache for cross-process usage
        if test_cases:
            # Prepare data for caching
            test_cases_data = []
            for tc in test_cases:
                tc_data = {
                    'id': tc.id,
                    'question_id': tc.question_id,
                    'input_data': tc.input_data,
                    'expected_output': tc.expected_output,
                    'is_sample': tc.is_sample,
                    'weight': tc.weight
                }
                test_cases_data.append(tc_data)
            
            # Cache the serialized test cases in Redis
            cache.set(cache_key, json.dumps(test_cases_data), timeout=TEST_CASE_CACHE_TIMEOUT)
            
            return test_cases
    except Exception as e:
        print(f"Error accessing in-memory cache for test cases: {e}")
    
    # If not in any cache, query the database directly
    test_cases = list(TestCase.objects.filter(question=question, is_sample=False))
    
    # If no test cases found, check if we have any sample test cases to use
    if not test_cases:
        test_cases = list(TestCase.objects.filter(question=question, is_sample=True))
    
    # If still no test cases, return empty list
    if not test_cases:
        return []
    
    # Prepare data for caching
    test_cases_data = []
    for tc in test_cases:
        tc_data = {
            'id': tc.id,
            'question_id': tc.question_id,
            'input_data': tc.input_data,
            'expected_output': tc.expected_output,
            'is_sample': tc.is_sample,
            'weight': tc.weight
        }
        test_cases_data.append(tc_data)
    
    # Cache the serialized test cases
    cache.set(cache_key, json.dumps(test_cases_data), timeout=TEST_CASE_CACHE_TIMEOUT)
    
    return test_cases

def get_driver_code(request, question_id, language_id):
    question = get_object_or_404(Question, id=question_id)
    driver_code = DriverCode.objects.filter(question_id=question_id, language_id=language_id).first()    
    if driver_code:
        
        if question.show_complete_driver_code:
            code = driver_code.complete_driver_code.replace("#USER_CODE#", driver_code.visible_driver_code)
            return JsonResponse({"success": True, "code": code})
        
        elif driver_code.visible_driver_code == "1":
            return JsonResponse({"success": True, "code": driver_code.complete_driver_code})
        
        else:
            return JsonResponse({"success": True, "code": driver_code.visible_driver_code})
        
    return JsonResponse({"success": False, "message": "Driver code not found.", "language id": language_id, "question id": question_id}, status=404)


def create_submission(user, question, source_code, language_id):
    """
    Create a new submission entry in the database.
    """
    try:
        return Submission.objects.create(
            user=user,
            question=question,
            code=source_code,
            language=language_id,
            status='Pending'
        )
    except Exception as e:
        print(f"Error creating submission: {e}")
        raise Exception("Could not create submission.")


def process_test_case_result(inputs, outputs, expected_outputs):
    """
    Compare outputs against expected outputs and prepare detailed results.
    Enhanced to support better UI display with all-passed status.
    """
    results = []
    all_passed = True
    passed_count = 0
    total_count = min(len(inputs), len(outputs), len(expected_outputs))
    
    for i in range(total_count):
        input_data = inputs[i] if i < len(inputs) else "No input"
        expected_output = expected_outputs[i] if i < len(expected_outputs) else "No expected output"
        output = outputs[i] if i < len(outputs) else "No output"
        
        # Normalize whitespace for comparison
        normalized_output = output.strip() if isinstance(output, str) else output
        normalized_expected = expected_output.strip() if isinstance(expected_output, str) else expected_output
        
        # Compare the output with the expected output
        passed = normalized_output == normalized_expected
        
        if passed:
            passed_count += 1
        else:
            all_passed = False
        
        result = {
            "input": input_data,
            "expected_output": expected_output,
            "user_output": output,
            "passed": passed,
            "status": "Passed" if passed else "Wrong Answer",
            "test_number": i + 1  # 1-based index for display
        }
        results.append(result)
    
    # Return both detailed results and summary information
    return {
        "test_cases": results,
        "all_passed": all_passed,
        "total": total_count,
        "passed_count": passed_count
    }


def update_submission_status(submission, passed, total, total_submission_count, status=None):
    """
    Update the submission status and score in the database.
    """
    
    try:
        if not status:
            submission.status = 'Accepted' if passed == total else 'Wrong Answer'
        else:
            submission.status = status
        
        # update streaks
        if submission.status == 'Accepted':
            update_user_streak(submission.user)
        
        score = int(((passed / total) * 100) * (1 - 0.1 * (total_submission_count - 1)))
        
        # past_submissions = Submission.objects.filter(user=user, question=question).count()
        
        if score < 0:
            score = 0
        
        submission.score = score
        submission.save()
        
        return score
                
    except Exception as e:
        print(f"Error updating submission: {e}")
        raise Exception("Could not update submission status.")

# =========================================== UPDATE COINS =========================================

def update_coin(user, score, question):
    
    # update the coins only if the user has submitted the code for the first time successfully
    if Submission.objects.filter(user=user, question=question, status="Accepted").count() > 1:
        return
    
    if score == 100:
        user.coins += 5
    elif score >= 75:
        user.coins += 4
    elif score >= 50:
        user.coins += 3
    elif score >= 25:
        user.coins += 2
    else:
        user.coins += 1
    user.save()

# =========================================== UPDATE STREAKS =======================================

def update_user_streak(user):
    # Fetch or create the user's streak record
    streak, created = Streak.objects.get_or_create(user=user)

    # Update the streak
    streak.update_streak()

# ============================================ SUBMIT CODE =========================================

# Helper for retrieving driver code
@sync_to_async
def get_driver_code_from_db(question_id, language_id):
    """
    Synchronous function to get driver code that can be safely called with sync_to_async
    """
    question = Question.objects.get(id=question_id)
    driver_code = DriverCode.objects.filter(question=question, language_id=language_id).first()
    if driver_code:
        return driver_code.complete_driver_code
    return None

# Use a regular dict for caching instead of lru_cache to avoid coroutine reuse issues
_driver_code_cache = {}

async def get_driver_code_async(question_id, language_id):
    """
    Async function to get driver code with in-memory caching
    Uses Django's sync_to_async for database operations
    """
    cache_key = f"{question_id}:{language_id}"
    
    # Check cache first
    if cache_key in _driver_code_cache:
        return _driver_code_cache[cache_key]
    
    # Get from database
    driver_code = await get_driver_code_from_db(question_id, language_id)
    
    # Cache the result
    if len(_driver_code_cache) > 100:  # Limit cache size
        _driver_code_cache.clear()
    _driver_code_cache[cache_key] = driver_code
    
    return driver_code

# Helper function to safely run async code in a synchronous context
def run_async_safely(coroutine):
    """
    Safely run an async coroutine in a synchronous context, handling event loop properly.
    This avoids the 'Event loop is closed' error on Windows with ProactorEventLoop.
    """
    try:
        # Get the current event loop
        loop = asyncio.get_event_loop()
        
        # If the loop is closed, create a new one
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
        # Run the coroutine and return the result
        return loop.run_until_complete(coroutine)
    except RuntimeError as e:
        if 'There is no current event loop in thread' in str(e):
            # Create a new event loop if there isn't one in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coroutine)
        else:
            raise

# Sync version wrapper for backward compatibility
def run_code_on_judge0(question, source_code, language_id, test_cases, cpu_time_limit, memory_limit):
    """
    Synchronous wrapper around async run_code_on_judge0_async function.
    For backward compatibility with existing code.
    """
    return run_async_safely(run_code_on_judge0_async(
        question, source_code, language_id, test_cases, cpu_time_limit, memory_limit
    ))

async def run_code_on_judge0_async(question, source_code, language_id, test_cases, cpu_time_limit, memory_limit):
    """
    Send the code to Judge0 API for execution against multiple test cases.
    Asynchronous version with connection pooling and exponential backoff.
    """
    cache_key = f"driver_code:{question.id}:{language_id}"
    complete_source_code = source_code
    
    if not question.show_complete_driver_code:  # User ko complete code dikh rha h
        # Try to get driver code from cache (Redis)
        cached_driver_code = await get_cache_value(cache_key)
        
        if cached_driver_code and 'code' in cached_driver_code:
            driver_code_complete = cached_driver_code['code']
            complete_source_code = driver_code_complete.replace("#USER_CODE#", source_code)
        else:
            # Try in-memory cache first
            try:
                driver_code_complete = await get_driver_code_async(question.id, language_id)
                if driver_code_complete:
                    complete_source_code = driver_code_complete.replace("#USER_CODE#", source_code)
                    # Also set in Redis cache for cross-process caching
                    await set_cache_value(
                        cache_key, 
                        {"success": True, "code": driver_code_complete},
                        DRIVER_CODE_CACHE_TIMEOUT
                    )
            except Exception as e:
                print(f"Error accessing in-memory cache: {e}")
                # Use sync_to_async for database operations
                get_driver_code_fallback = sync_to_async(lambda q, lid: DriverCode.objects.filter(question=q, language_id=lid).first())
                driver_code = await get_driver_code_fallback(question, language_id)
                
                if driver_code:
                    complete_source_code = driver_code.complete_driver_code.replace("#USER_CODE#", source_code)
                    # Cache the driver code
                    await set_cache_value(
                        cache_key,
                        {"success": True, "code": driver_code.complete_driver_code},
                        DRIVER_CODE_CACHE_TIMEOUT
                    )

    # Prepare single stdin batch input for Judge0
    stdin = f"{len(test_cases)}~"
    for test_case in test_cases:
        stdin += f"{test_case.input_data}~"

    # Convert "~" to newline "\n" before encoding
    stdin = stdin.replace("~", "\n")  
    
    encoded_code = base64.b64encode(complete_source_code.encode('utf-8')).decode('utf-8')
    encoded_stdin = base64.b64encode(stdin.encode('utf-8')).decode('utf-8')

    submission_data = {
        "source_code": encoded_code,
        "language_id": language_id,
        "stdin": encoded_stdin,
        "cpu_time_limit": cpu_time_limit,
        "wall_time_limit": cpu_time_limit,
        "memory_limit": memory_limit * 1000,
        "enable_per_process_and_thread_time_limit": True,
        "base64_encoded": True
    }

    try:
        # Create a fresh session for each request to avoid session reuse issues
        # This is safer than reusing a global session in a Django environment
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            # Submit Code to Judge0 using connection pool
            async with session.post(
                JUDGE0_URL + "?base64_encoded=true", 
                json=submission_data, 
                timeout=10
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
                
                token = response_data.get("token")
                if not token:
                    return {"error": "No token received from Judge0.", "outputs": None, "token": None}

                print("✅ TOKEN:", token)
            
            # Poll Until Completion with improved exponential backoff
            max_retries = 15  # Increased max retries
            backoff = 0.5  # Start with a smaller backoff
            jitter = 0.1  # Add jitter to avoid thundering herd problem
            
            result = None
            for retry in range(max_retries):
                async with session.get(
                    f"{JUDGE0_URL}/{token}?base64_encoded=true", 
                    timeout=10
                ) as result_response:
                    result_response.raise_for_status()
                    result = await result_response.json()
                    status_id = result.get("status", {}).get("id")
                    
                    if status_id not in [1, 2]:  # Finished processing
                        break
                        
                    # Enhanced exponential backoff with jitter
                    sleep_time = min(backoff * (1.0 + random.uniform(-jitter, jitter)), 10.0)  # Cap at 10 seconds
                    await asyncio.sleep(sleep_time)
                    backoff = min(backoff * 2.0, 10.0)  # Double the backoff but capped
        
        # Handle Errors
        if result.get("stderr"):
            stderr = base64.b64decode(result['stderr']).decode('utf-8', errors='replace')
            print("❌ STDERR:", stderr)
            return {"error": f"Runtime Error: {stderr}", "token": token}

        if result.get("compile_output"):
            compile_output = base64.b64decode(result['compile_output']).decode('utf-8', errors='replace')
            print("❌ COMPILE OUTPUT:", compile_output)
            return {"error": f"Compile Error: {compile_output}", "token": token}

        if result.get("status", {}).get("id") == 5:
            return {"error": "Time Limit Exceeded (TLE)", "token": token}

        if result.get("status", {}).get("id") == 6:
            return {"error": "Compilation Error", "token": token}

        # Decode Outputs
        outputs = result.get("stdout", "")
        
        if outputs:
            # decode the output from base64
            outputs = base64.b64decode(outputs).decode('utf-8', errors='replace')
            
            # getting the list of output (separated by ~)
            outputs = [output.strip() for output in outputs.split("~") if output.strip()]
            
        else:
            outputs = ["No output generated."]

        return {"outputs": outputs, "token": token}

    except aiohttp.ClientError as e:
        return {"error": f"AIOHTTP Request Error: {str(e)}", "outputs": None, "token": None}
    except Exception as e:
        return {"error": f"Unexpected Error: {str(e)}", "outputs": None, "token": None}


@csrf_exempt
def submit_code(request, slug):
    """
    Handle user code submission for a problem with asyncio support.
    This is a synchronous wrapper around the async implementation for backward compatibility.
    """
    if request.method == 'POST':
        return run_async_safely(submit_code_async(request, slug))
    return JsonResponse({"error": "Method not allowed"}, status=405)

# Additional helper functions for database operations in async context
@sync_to_async
def get_question_by_slug(slug):
    return get_object_or_404(Question, slug=slug)

@sync_to_async
def get_sheet_for_question(question):
    return Sheet.objects.filter(questions=question, is_approved=True).first()

@sync_to_async
def get_student_from_user(user):
    """Safely get student profile from user in async context"""
    return user.student

@sync_to_async
def create_submission_async(user, question, source_code, language_id):
    return create_submission(user, question, source_code, language_id)

@sync_to_async
def get_submission_count(user, question):
    return Submission.objects.filter(user=user, question=question).count()

@sync_to_async
def update_submission_status_async(submission, passed, total, total_submission_count, status=None):
    return update_submission_status(submission, passed, total, total_submission_count, status)

@sync_to_async
def update_coin_async(user, score, question):
    return update_coin(user, score, question)

@sync_to_async
def get_cache_value(key):
    return cache.get(key)

@sync_to_async
def set_cache_value(key, value, timeout=None):
    return cache.set(key, value, timeout=timeout)

@sync_to_async
def get_post_data(request, key):
    """Safely get POST data in async context"""
    return request.POST.get(key)

@sync_to_async
def parse_json_body(request):
    """Safely parse JSON body in async context"""
    return json.loads(request.body)

async def submit_code_async(request, slug):
    """
    Asynchronous implementation of code submission with improved performance.
    Uses Django's sync_to_async for all database operations.
    """
    start_time = time.time()
    try:
        # Validate inputs
        question = await get_question_by_slug(slug)
        # Safely get student in async context
        user = await get_student_from_user(request.user)            

        # Safely get POST data in async context
        language_id = await get_post_data(request, 'language_id')
        source_code = await get_post_data(request, 'submission_code')
        
        if not language_id or not source_code:
            return JsonResponse({"error": "Missing language ID or source code."}, status=400)

        # Use async test case fetching via in-memory cache when possible
        test_cases = await get_test_cases_async(question.id)
        if not test_cases:
            # Fallback to synchronous get_test_cases if async version returns nothing
            # Use thread executor for this CPU-bound operation
            test_cases_sync = sync_to_async(get_test_cases)
            test_cases = await test_cases_sync(question)
        
        if not test_cases:
            return JsonResponse({"error": "No test cases available for this question."}, status=400)

        sheet = await get_sheet_for_question(question)

        if sheet and not sheet.is_enabled:
            return JsonResponse({"sheet_disabled": "Sheet not enabled."}, status=400)

        # Record operation time for fetching dependencies
        dependencies_time = time.time() - start_time
        
        # Create a submission record asynchronously
        submission_start = time.time()
        submission = await create_submission_async(user, question, source_code, language_id)
        submission_time = time.time() - submission_start

        # Run the code using the async version and process results
        judge0_start = time.time()
        judge0_response = await run_code_on_judge0_async(question, source_code, language_id, test_cases, question.cpu_time_limit, question.memory_limit)
        judge0_time = time.time() - judge0_start
        
        if judge0_response.get("error") or judge0_response.get("compile_output"):  # Any Kind of Error
            result = {
                "error": judge0_response.get("error"),
                "token": judge0_response.get("token")
            }
            
            await update_submission_status_async(submission, 0, len(test_cases), 0, status="Compilation Error")
            
            if judge0_response.get("compile_output"):
                result["compile_output"] = judge0_response.get("compile_output")
            
            end_time = time.time()
            print(f"PERFORMANCE: Error submission took {end_time - start_time:.2f}s (Dependencies: {dependencies_time:.2f}s, Submission: {submission_time:.2f}s, Judge0: {judge0_time:.2f}s)")
            
            return JsonResponse(result, status=400)

        # Process successful outputs
        processing_start = time.time()
        outputs = judge0_response["outputs"]
        
        # Use thread to run CPU-bound operations concurrently
        normalize_async = sync_to_async(normalize_output)
        expected_outputs = await asyncio.gather(*[
            normalize_async(tc.expected_output) for tc in test_cases
        ])
        inputs = [tc.input_data for tc in test_cases]
        
        # Process test case results with sync_to_async
        process_results_async = sync_to_async(process_test_case_result)
        result_data = await process_results_async(inputs, outputs, expected_outputs)
        
        # Extract test case results and summary information
        test_case_results = result_data["test_cases"]
        all_passed = result_data["all_passed"]
        passed_test_cases = result_data["passed_count"]
        total_test_cases = result_data["total"]
        
        # Use a cached query to get submission count with improved caching
        submission_count_key = f"submission_count:{user.id}:{question.id}"
        total_submission_count = await get_cache_value(submission_count_key)
        
        if total_submission_count is None:
            total_submission_count = await get_submission_count(user, question)
            await set_cache_value(submission_count_key, total_submission_count, 60*5)  # 5 minutes cache
        
        # Update submission status asynchronously
        score = await update_submission_status_async(submission, passed_test_cases, len(test_cases), total_submission_count)
        
        # Increment cached submission count
        await set_cache_value(submission_count_key, total_submission_count + 1, 60*5)
        
        # Update user coins asynchronously
        await update_coin_async(user, score, question)
        processing_time = time.time() - processing_start
        
        end_time = time.time()
        print(f"PERFORMANCE: Successful submission took {end_time - start_time:.2f}s (Dependencies: {dependencies_time:.2f}s, Submission: {submission_time:.2f}s, Judge0: {judge0_time:.2f}s, Processing: {processing_time:.2f}s)")

        # Prepare response with enhanced UI support
        response_data = {
            "test_case_results": test_case_results,
            "submission_id": submission.id,
            "status": submission.status,
            "score": submission.score,
            "compile_output": None,  # No compilation error
            "token": judge0_response.get("token"),
            "is_all_test_cases_passed": all_passed,
            "summary": {
                "all_passed": all_passed,
                "passed_count": passed_test_cases,
                "total": total_test_cases
            }
        }
        
        # Add display mode for UI enhancement - ALWAYS use success_badge when all tests pass
        if all_passed:
            # For all passed tests, use success_badge mode and don't need to include detailed results
            response_data["display_mode"] = "success_badge"
            # Keep only summary data to reduce response size
            response_data["test_case_results"] = []
        else:
            # Sort test cases to show failed ones first
            sorted_results = sorted(test_case_results, key=lambda x: (x["passed"], x.get("test_number", 1)))
            response_data["test_case_results"] = sorted_results
            response_data["display_mode"] = "detailed"
            
        return JsonResponse(response_data)

    except Question.DoesNotExist:
            end_time = time.time()
            print(f"PERFORMANCE: Question not found error took {end_time - start_time:.2f}s")
            return JsonResponse({
                "error": "Question not found.",
                "token": judge0_response.get("token") if 'judge0_response' in locals() else None
                }, status=404)
    except Exception as e:
        end_time = time.time()
        print(f"PERFORMANCE: Exception occurred, took {end_time - start_time:.2f}s")
        print(f"Error in submit code views: {e}")
        return JsonResponse({
            "error": "Error in submit code backend: " + str(e),
            "token": judge0_response.get("token") if 'judge0_response' in locals() else None
            }, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=400)

# =================================== RUN CODE AGAINST SAMPLE TEST CASES ===========================

@csrf_exempt
def run_code(request, slug):
    """
    Run code against sample test cases (synchronous wrapper).
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        source_code = data.get('code', '')
        language_id = data.get('language_id')
        sample_test_cases_only = data.get('sample_test_cases_only', True)
        
        if not source_code or not language_id:
            return JsonResponse({"error": "Missing source code or language."}, status=400)
        
        # Use run_async_safely to handle event loop issues
        return run_async_safely(
            run_code_async(slug, source_code, language_id, request.user, sample_test_cases_only)
        )
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        print(f"Error in run_code: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@sync_to_async
def get_sample_test_cases(question):
    """
    Retrieve only sample test cases for a question
    """
    return list(TestCase.objects.filter(question=question, is_sample=True))

async def run_code_async(slug, source_code, language_id, user, sample_test_cases_only=True):
    """
    Run code against sample test cases with async processing.
    Uses Django's sync_to_async for all database operations.
    """
    start_time = time.time()
    judge0_response = {}
    
    try:
        # Get question using sync_to_async
        get_question = sync_to_async(lambda s: Question.objects.get(slug=s))
        question = await get_question(slug)
        
        # Get sample test cases
        test_cases = await get_sample_test_cases(question)
        
        if not test_cases:
            return JsonResponse({"error": "No sample test cases found."}, status=400)
        
        # Log the time taken for setup
        setup_time = time.time() - start_time
        
        # Execute code with performance monitoring using async version
        judge0_start = time.time()
        judge0_response = await run_code_on_judge0_async(question, source_code, language_id, test_cases, question.cpu_time_limit, question.memory_limit)
        judge0_time = time.time() - judge0_start
        
        # Handle execution errors
        if judge0_response.get("error") or judge0_response.get("compile_output"):
            result = {
                "error": judge0_response.get("error"),
                "token": judge0_response.get("token")
            }
            
            if judge0_response.get("compile_output"):
                result["compile_output"] = judge0_response.get("compile_output")
            
            end_time = time.time()
            print(f"PERFORMANCE: Run code error took {end_time - start_time:.2f}s (Setup: {setup_time:.2f}s, Judge0: {judge0_time:.2f}s)")
            return JsonResponse(result, status=400)
        
        # Process results with concurrent operations
        processing_start = time.time()
        outputs = judge0_response["outputs"]
        
        # Get expected outputs
        loop = asyncio.get_running_loop()
        expected_outputs = await asyncio.gather(*[
            loop.run_in_executor(None, normalize_output, tc.expected_output) for tc in test_cases
        ])

        inputs = [tc.input_data for tc in test_cases]
        
        # Process test case results
        process_results = sync_to_async(process_test_case_result)
        result_data = await process_results(inputs, outputs, expected_outputs)
        
        # Extract results and summary information
        test_case_results = result_data["test_cases"]
        all_passed = result_data["all_passed"]
        passed_count = result_data["passed_count"]
        total_count = result_data["total"]
        
        processing_time = time.time() - processing_start
        
        end_time = time.time()
        print(f"PERFORMANCE: Successful run took {end_time - start_time:.2f}s (Setup: {setup_time:.2f}s, Judge0: {judge0_time:.2f}s, Processing: {processing_time:.2f}s)")
        
        # When all tests pass, we'll only include a summary in the response
        # This will allow the UI to show a simple green badge instead of all test cases
        response_data = {
            "token": judge0_response.get("token"),
            "is_all_test_cases_passed": all_passed,
            "summary": {
                "all_passed": all_passed,
                "passed_count": passed_count,
                "total": total_count
            }
        }
        
        # Different UI display modes for run_code vs submit_code
        # Sort test cases to always show failed ones first
        sorted_results = sorted(test_case_results, key=lambda x: (x["passed"], x["test_number"]))
        
        # Check if this is a run_code or submit_code operation
        if not sample_test_cases_only:  # This is a submit_code operation
            if all_passed:
                # For all passed tests on submission, use success_badge mode
                response_data["display_mode"] = "success_badge"
                response_data["test_case_results"] = []  # Reduce response size for submissions
            else:
                response_data["test_case_results"] = sorted_results
                response_data["display_mode"] = "detailed"
        else:  # This is a run_code operation
            # For run_code, always show detailed results regardless of pass/fail status
            response_data["test_case_results"] = sorted_results
            response_data["display_mode"] = "detailed"
            
        return JsonResponse(response_data)
        
    except Exception as e:
        end_time = time.time()
        print(f"PERFORMANCE: Run code exception took {end_time - start_time:.2f}s")
        print(f"Error in run_code_async: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "error": str(e),
            "token": judge0_response.get("token") if 'judge0_response' in locals() else None
        }, status=400)

# ============================================= CUSTOM INPUT =======================================

@csrf_exempt
def custom_input(request, slug):
    """
    Handle custom input code execution (synchronous wrapper).
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        source_code = data.get('code', '')
        language_id = data.get('language_id')
        custom_input_data = data.get('custom_input', '')
        
        if not source_code or not language_id:
            return JsonResponse({"error": "Missing source code or language."}, status=400)
        
        # Use run_async_safely to handle event loop issues
        return run_async_safely(
            custom_input_async(slug, source_code, language_id, custom_input_data, request.user)
        )
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        print(f"Error in custom_input: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

async def custom_input_async(slug, source_code, language_id, custom_input_data, user):
    """
    Handle custom input code execution with async processing.
    """
    start_time = time.time()
    judge0_response = {}
    
    try:
        # Get question using sync_to_async
        get_question = sync_to_async(lambda s: Question.objects.get(slug=s))
        question = await get_question(slug)
        
        if not language_id or not source_code or not custom_input_data:
            return JsonResponse({"error": "Missing language ID, source code, or input data."}, status=400)
        
        # Split the input into lines
        input_lines = custom_input_data.strip().split('\n')
        
        try:
            num_test_cases = int(input_lines[0])
            test_case_inputs = input_lines[1:num_test_cases + 1]
        except (ValueError, IndexError):
            return JsonResponse({"error": "Invalid input format. The first line should indicate the number of test cases."}, status=400)
        
        if len(test_case_inputs) != num_test_cases:
            return JsonResponse({"error": "Number of provided inputs does not match the specified number of test cases."}, status=400)
        
        # Create test cases - this is just in-memory operation, no DB access
        test_cases = [
            TestCase(question=question, input_data=tc_input, expected_output="")
            for tc_input in test_case_inputs
        ]
        
        # Run code on Judge0 with async processing
        judge0_start = time.time()
        judge0_response = await run_code_on_judge0_async(
            question,
            source_code,
            language_id,
            test_cases,
            question.cpu_time_limit,
            question.memory_limit
        )
        judge0_time = time.time() - judge0_start
        
        if judge0_response.get("error") or judge0_response.get("compile_output"):  # Any Kind of Error
            result = {
                "error": judge0_response.get("error"),
                "token": judge0_response.get("token")
            }
            if judge0_response.get("compile_output"):
                result["compile_output"] = judge0_response.get("compile_output")
                
            end_time = time.time()
            print(f"PERFORMANCE: Custom input error took {end_time - start_time:.2f}s (Judge0: {judge0_time:.2f}s)")
            return JsonResponse(result, status=400)
        
        # Process results
        processing_start = time.time()
        outputs = judge0_response["outputs"]
        
        # Set expected outputs if not already set - can be done in parallel for performance
        test_cases_with_output = []
        passed_count = len(test_cases)  # For custom input, all are considered passed
        
        for i, test_case in enumerate(test_cases):
            output = outputs[i] if i < len(outputs) else "No output"
            if test_case.expected_output == "":
                test_case.expected_output = output
            
            # For custom input, we consider all outputs as correct
            test_cases_with_output.append({
                "input": test_case.input_data,
                "expected_output": test_case.expected_output,
                "user_output": output,
                "passed": True,
                "status": "Passed",
                "test_number": i + 1
            })
            
        processing_time = time.time() - processing_start
        end_time = time.time()
        print(f"PERFORMANCE: Custom input success took {end_time - start_time:.2f}s (Judge0: {judge0_time:.2f}s, Processing: {processing_time:.2f}s)")
        
        # Return with the enhanced UI format - consistent with other endpoints
        return JsonResponse({
            "status": "Success",
            "test_case_results": [],  # Don't include detailed results for success badge mode
            "is_all_test_cases_passed": True,
            "summary": {
                "all_passed": True,
                "passed_count": passed_count,
                "total": len(test_cases_with_output)
            },
            "display_mode": "success_badge"  # Signal for frontend to show a success badge
        })
        
    except Exception as e:
        end_time = time.time()
        print(f"PERFORMANCE: Custom input exception took {end_time - start_time:.2f}s")
        print(f"Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)

# ============================================= UNLOCK HINT ========================================

def unlock_hint(request, question_id):
    if request.method == 'POST' and request.user.is_authenticated:
        question = get_object_or_404(Question, id=question_id)
        student = request.user.student

        if question.hint:  # Check if the question has a hint
            if student.coins > 0:  # Check if the user has enough coins
                student.coins -= 5  # Deduct a spark
                student.save()
                return JsonResponse({'status': 'success', 'hint': question.hint})
            else:
                return JsonResponse({'status': 'error', 'message': 'Not enough coins'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No hint available for this question'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# ========================================= RECOMMENDED QUESTIONS ==================================

@login_required(login_url="login")
def fetch_recommended_questions(request, slug):
    question = get_object_or_404(Question, slug=slug)
    recommended_questions = RecommendedQuestions.objects.filter(question=question)

    data = [
        {
            "id": rq.id,
            "title": rq.title,
            "link": rq.link,
            "platform": rq.platform
        } for rq in recommended_questions
    ]
    
    return JsonResponse({"status": "success", "questions": data})


# ==================================================================================================
# Resource management and cleanup
# ==================================================================================================

# Hook into Django's startup and shutdown signals to manage resources properly
from django.apps import AppConfig
from django.dispatch import receiver
from django.db.models.signals import post_migrate
import atexit
import asyncio
import signal
import sys

# Register the atexit handler to properly close aiohttp session
@atexit.register
def cleanup_resources():
    """Ensure all resources are properly closed when the application exits"""
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            # Run the async cleanup function in the event loop
            if _aiohttp_session and not _aiohttp_session.closed:
                loop.run_until_complete(close_aiohttp_session())
    except Exception as e:
        print(f"Error during resource cleanup: {e}")

# Register signal handlers for graceful shutdown
def signal_handler(sig, frame):
    """Handle termination signals by cleaning up resources before exit"""
    print(f"Received signal {sig}, cleaning up resources...")
    cleanup_resources()
    sys.exit(0)

# Register common termination signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# This ensures our cleanup happens even when Django auto-reloads during development
def reload_handler():
    """Clean up resources during development server reload"""
    cleanup_resources()

# If in Django development server, hook into its reload mechanism
if 'runserver' in sys.argv:
    try:
        from django.utils.autoreload import autoreload_started
        @receiver(autoreload_started)
        def on_autoreload(sender, **kwargs):
            atexit.register(reload_handler)
    except ImportError:
        # Older Django versions
        pass

# ==================================================================================================

def convert_backticks_to_code(text):
    pattern = r"`(.*?)`"
    result = re.sub(pattern, r"<code style='font-size: 110%'>\1</code>", text)
    return result

