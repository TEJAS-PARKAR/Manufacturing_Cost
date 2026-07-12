"""
Utility module for OpenAI API calls and response parsing.
Handles communication with GPT-4o and extracts structured data from responses.
"""

import json
import re
import time
from openai import OpenAI


def call_openai(api_key: str, messages: list, model: str = "gpt-4o", max_retries: int = 3) -> str:
    """
    Send messages to OpenAI Chat Completions API and return the response content.
    Includes automatic retry with exponential backoff for rate limit errors.

    Args:
        api_key: OpenAI API key
        messages: List of message dicts with 'role' and 'content'
        model: Model name to use (default: gpt-4o)
        max_retries: Maximum number of retries on rate limit errors

    Returns:
        Raw response content string from the LLM

    Raises:
        Exception: On API errors with descriptive messages
    """
    client = OpenAI(api_key=api_key)
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,  # Low temperature for consistent extraction
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            last_error = error_msg

            if "401" in error_msg or "invalid_api_key" in error_msg:
                raise Exception("Invalid API key. Please check your OpenAI API key and try again.")
            elif "insufficient_quota" in error_msg:
                raise Exception(
                    "API quota exceeded. Please check your OpenAI billing at https://platform.openai.com/usage"
                )
            elif "429" in error_msg:
                if attempt < max_retries:
                    wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(
                        "Rate limit exceeded after multiple retries. "
                        "Your OpenAI account may be on a free tier or out of credits. "
                        "Check your plan at https://platform.openai.com/usage"
                    )
            else:
                raise Exception(f"OpenAI API error: {error_msg}")

    raise Exception(f"OpenAI API error after {max_retries} retries: {last_error}")


def parse_response(raw_response: str) -> dict:
    """
    Parse the LLM response into structured components.

    Expects the response to contain ---SUMMARY--- and ---JSON--- markers.
    Falls back to regex JSON extraction if markers are missing.

    Args:
        raw_response: Raw string response from the LLM

    Returns:
        Dict with keys: summary, extracted_data, missing_fields, is_complete, raw_response
    """
    result = {
        "summary": "",
        "extracted_data": None,
        "missing_fields": [],
        "is_complete": False,
        "raw_response": raw_response,
    }

    # Extract summary
    summary = _extract_section(raw_response, "---SUMMARY---", "---JSON---")
    if summary:
        result["summary"] = summary.strip()
    else:
        # If no markers, use everything before the JSON as summary
        json_match = re.search(r'\{[\s\S]*"part_name"[\s\S]*\}', raw_response)
        if json_match:
            result["summary"] = raw_response[:json_match.start()].strip()
        else:
            result["summary"] = raw_response.strip()

    # Extract JSON
    json_data = _extract_json(raw_response)
    if json_data:
        result["extracted_data"] = json_data
        result["missing_fields"] = json_data.get("missing_information", [])
        result["is_complete"] = len(result["missing_fields"]) == 0
    else:
        result["summary"] = raw_response.strip()

    return result


def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    """Extract text between two markers."""
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx == -1:
        return ""

    start_idx += len(start_marker)

    if end_idx == -1:
        return text[start_idx:]

    return text[start_idx:end_idx]


def _extract_json(text: str) -> dict | None:
    """
    Extract JSON object from text. Tries multiple strategies:
    1. Between ---JSON--- and ---END--- markers
    2. Between ```json and ``` code fences
    3. First { ... } block containing "part_name"
    """
    # Strategy 1: Between markers
    json_str = _extract_section(text, "---JSON---", "---END---").strip()
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Strategy 2: Code fence
    code_fence_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if code_fence_match:
        try:
            return json.loads(code_fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Raw JSON block
    json_match = re.search(r'(\{[\s\S]*"part_name"[\s\S]*\})', text)
    if json_match:
        json_str = json_match.group(1)
        # Find the matching closing brace
        brace_count = 0
        end_idx = 0
        for i, char in enumerate(json_str):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        if end_idx > 0:
            try:
                return json.loads(json_str[:end_idx])
            except json.JSONDecodeError:
                pass

    return None


def get_default_extracted_data() -> dict:
    """Return the default empty extracted data structure."""
    return {
        "part_name": "",
        "material": "",
        "thickness_mm": None,
        "length_mm": None,
        "width_mm": None,
        "operations": {
            "shearing": 0,
            "blanking": 0,
            "piercing": 0,
            "forming": 0,
            "bending": 0,
            "welding": 0,
            "machining": 0,
            "cutting": 0,
        },
        "surface_treatment": "",
        "quantity": None,
        "missing_information": [],
    }
