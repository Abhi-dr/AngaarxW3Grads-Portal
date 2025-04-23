"""
Async utilities for code execution system.
This module provides asynchronous functions for interacting with Judge0 API.
"""
import asyncio
import json
import time
import base64
from typing import Dict, List, Any, Optional, Union

# Use standard library for async HTTP requests to avoid additional dependencies
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor

# Constants
JUDGE0_URL = "https://theangaarbatch.in/judge0/submissions"
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def encode_base64(text: str) -> str:
    """Encode text to base64."""
    if not text:
        return ""
    return base64.b64encode(text.encode()).decode()

def decode_base64(encoded: str) -> str:
    """Decode base64 to text."""
    if not encoded:
        return ""
    try:
        return base64.b64decode(encoded.encode()).decode()
    except Exception as e:
        print(f"Error decoding base64: {e}")
        return f"[Error decoding: {e}]"

async def make_async_request(url: str, method: str = "GET", data: Optional[Dict] = None, 
                           headers: Optional[Dict] = None, timeout: int = REQUEST_TIMEOUT) -> Dict:
    """
    Make an asynchronous HTTP request using ThreadPoolExecutor.
    
    This function uses the standard library to make HTTP requests,
    but wraps them in a ThreadPoolExecutor to make them non-blocking.
    """
    headers = headers or {"Content-Type": "application/json"}
    
    def _make_request():
        try:
            if data and method == "POST":
                data_bytes = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                return {
                    "status_code": response.status,
                    "data": json.loads(response_data) if response_data else {},
                    "ok": True
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {
                "status_code": e.code,
                "error": f"HTTP Error: {e.code} {e.reason}",
                "data": json.loads(error_body) if error_body else {},
                "ok": False
            }
        except urllib.error.URLError as e:
            return {
                "status_code": 0,
                "error": f"URL Error: {str(e.reason)}",
                "data": {},
                "ok": False
            }
        except Exception as e:
            return {
                "status_code": 0,
                "error": f"Request failed: {str(e)}",
                "data": {},
                "ok": False
            }
    
    # Run the blocking HTTP request in a separate thread
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, _make_request)

async def submit_code_async(source_code: str, language_id: int, input_data: str = "") -> Dict:
    """
    Submit code to Judge0 API asynchronously.
    """
    data = {
        "source_code": encode_base64(source_code),
        "language_id": language_id,
        "stdin": encode_base64(input_data),
        "redirect_stderr_to_stdout": False
    }
    
    response = await make_async_request(JUDGE0_URL, method="POST", data=data)
    
    if not response["ok"]:
        return {"error": response.get("error", "Failed to submit code"), "token": None}
    
    return {"token": response["data"].get("token"), "error": None}

async def get_result_async(token: str) -> Dict:
    """
    Get execution result from Judge0 API asynchronously.
    """
    result_url = f"{JUDGE0_URL}/{token}?base64_encoded=true"
    
    retries = 0
    while retries < MAX_RETRIES:
        response = await make_async_request(result_url)
        
        if not response["ok"]:
            retries += 1
            await asyncio.sleep(RETRY_DELAY * retries)
            continue
        
        result = response["data"]
        
        # Check if the submission is still processing
        status_id = result.get("status", {}).get("id")
        if status_id in [1, 2]:  # In queue or processing
            retries += 1
            await asyncio.sleep(RETRY_DELAY * retries)
            continue
            
        # Process the result
        result_dict = {"token": token}
        
        # Add status information
        if result.get("status"):
            result_dict["status_id"] = result["status"]["id"]
            result_dict["status_description"] = result["status"]["description"]
        
        # Add error messages if available
        if result.get("stderr"):
            result_dict["stderr"] = decode_base64(result["stderr"])
            
        if result.get("compile_output"):
            result_dict["compile_output"] = decode_base64(result["compile_output"])
            
        if result.get("message"):
            result_dict["error"] = decode_base64(result["message"])
            
        # Add execution metrics
        if result.get("time"):
            result_dict["execution_time"] = result["time"]
            
        if result.get("memory"):
            result_dict["memory_used"] = result["memory"]
            
        # Check for specific error conditions
        if status_id == 3:  # Accepted
            if result.get("stdout"):
                output = decode_base64(result["stdout"])
                result_dict["outputs"] = [output]
        else:
            # Handle various error cases
            if status_id == 5:  # Time Limit Exceeded
                result_dict["time_limit_exceeded"] = True
                result_dict["error"] = "Time limit exceeded"
                
            elif status_id == 6:  # Compilation Error
                result_dict["error"] = "Compilation failed"
                
            elif status_id in [7, 8, 9, 10, 11, 12]:  # Runtime errors
                result_dict["error"] = f"Runtime error: {result_dict.get('status_description', 'Unknown error')}"
                
            else:
                result_dict["error"] = f"Execution failed: {result_dict.get('status_description', 'Unknown error')}"
        
        return result_dict
        
    # If we've exhausted retries
    return {
        "error": "Timed out waiting for results", 
        "token": token,
        "error_details": "The Judge0 API did not return a result in time."
    }

# This function implements parallel test case processing
async def process_test_cases_async(source_code: str, language_id: int, test_cases: List[Dict]) -> Dict:
    """
    Process multiple test cases in parallel using asyncio.
    
    Args:
        source_code: The source code to execute
        language_id: The language ID for Judge0
        test_cases: List of test case dictionaries with input_data and expected_output
        
    Returns:
        Dictionary with results for all test cases
    """
    # Submit all test cases concurrently
    submission_tasks = []
    for test_case in test_cases:
        task = submit_code_async(source_code, language_id, test_case.get("input_data", ""))
        submission_tasks.append(task)
    
    # Wait for all submissions to complete
    submissions = await asyncio.gather(*submission_tasks)
    
    # Get results for all submissions concurrently
    result_tasks = []
    for submission, test_case in zip(submissions, test_cases):
        if submission.get("error") or not submission.get("token"):
            # If submission failed, create a failed result
            result = {
                "status": "Failed",
                "passed": False,
                "input": test_case.get("input_data", ""),
                "expected_output": test_case.get("expected_output", ""),
                "user_output": "",
                "error": submission.get("error", "Failed to submit code"),
            }
            result_tasks.append(asyncio.create_task(asyncio.sleep(0, result)))
        else:
            # Otherwise, get the result from Judge0
            task = get_result_async(submission["token"])
            result_tasks.append(task)
    
    # Wait for all results
    results = await asyncio.gather(*result_tasks)
    
    # Process the results
    test_case_results = []
    for result, test_case in zip(results, test_cases):
        if isinstance(result, tuple) and len(result) == 2:
            # This is a result from asyncio.sleep() that carries a pre-made result
            test_case_results.append(result[1])
            continue
            
        # Process normal result from Judge0
        user_output = result.get("outputs", [""])[0] if result.get("outputs") else ""
        expected = test_case.get("expected_output", "").strip()
        
        test_result = {
            "passed": user_output.strip() == expected,
            "status": "Passed" if user_output.strip() == expected else "Failed",
            "input": test_case.get("input_data", ""),
            "expected_output": expected,
            "user_output": user_output,
        }
        
        # Add error information if available
        if result.get("stderr"):
            test_result["stderr"] = result["stderr"]
        if result.get("compile_output"):
            test_result["compile_output"] = result["compile_output"]
        if result.get("error"):
            test_result["error"] = result["error"]
            
        test_case_results.append(test_result)
    
    # Prepare the aggregate result
    all_passed = all(result.get("passed", False) for result in test_case_results)
    
    return {
        "test_case_results": test_case_results,
        "all_passed": all_passed,
        "passed_count": sum(1 for result in test_case_results if result.get("passed", False)),
        "total_count": len(test_case_results)
    }
