"""
HTTP client for Chess.com API interactions.

This module provides a polite HTTP client that respects Chess.com's API guidelines:
- Serial access (no parallel requests)
- Proper User-Agent identification
- Rate limiting and backoff strategies
- Retry logic for transient failures
"""

import sys
import time
from typing import Optional

import requests

from config import DEFAULT_SLEEP, DEFAULT_TIMEOUT, DEFAULT_RETRIES


class ChessComHttpClient:
    """
    HTTP client specifically designed for Chess.com Public API interactions.
    
    Features:
    - Serial request processing (no parallel requests)
    - Automatic rate limiting with configurable delays
    - Exponential backoff for rate-limited responses (429)
    - Retry logic for transient failures
    - Proper error handling and logging
    """
    
    def __init__(
        self, 
        user_agent: str, 
        sleep_s: float = DEFAULT_SLEEP,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES
    ):
        """
        Initialize the HTTP client.
        
        Args:
            user_agent: User-Agent string identifying your application and contact info
            sleep_s: Seconds to sleep between requests (default: 0.25)
            timeout: Request timeout in seconds (default: 20)
            retries: Number of retry attempts for failed requests (default: 3)
        """
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip"
        })
        self.sleep_s = sleep_s
        self.timeout = timeout
        self.retries = retries

    def get_json(self, url: str) -> Optional[dict]:
        """
        Perform a GET request and return parsed JSON data.
        
        This method implements the Chess.com API best practices:
        - Serial access only
        - Polite delays between requests
        - Proper handling of rate limits (429 responses)
        - Retry logic for transient failures
        
        Args:
            url: The URL to fetch
            
        Returns:
            Parsed JSON data as a dictionary, or None if the request failed
            
        Note:
            This method will always sleep for `sleep_s` seconds after each request
            to maintain serial access and be respectful to the API.
        """
        attempt = 0
        
        while True:
            attempt += 1
            
            try:
                response = self.sess.get(url, timeout=self.timeout)
            except requests.RequestException as e:
                if attempt <= self.retries:
                    wait_time = min(5 * attempt, 20)
                    print(f"[WARN] Request exception for {url}: {e}. Retrying in {wait_time}s...", 
                          file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                print(f"[ERROR] GET failed after {self.retries} attempts for {url}: {e}", 
                      file=sys.stderr)
                return None

            # Handle successful response
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as e:
                    print(f"[WARN] Invalid JSON response from {url}: {e}", file=sys.stderr)
                    data = None
                
                # Always sleep to maintain serial access
                time.sleep(self.sleep_s)
                return data

            # Handle not modified (if using conditional requests)
            if response.status_code == 304:
                time.sleep(self.sleep_s)
                return None

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                wait_time = min(10 * attempt, 60)
                print(f"[INFO] Rate limited (429) for {url}. Backing off {wait_time}s...", 
                      file=sys.stderr)
                time.sleep(wait_time)
                continue

            # Handle not found / gone
            if response.status_code in (404, 410):
                time.sleep(self.sleep_s)
                return None

            # Handle other errors with retry
            if attempt <= self.retries:
                wait_time = min(5 * attempt, 20)
                print(f"[INFO] HTTP {response.status_code} for {url}. Retrying in {wait_time}s...", 
                      file=sys.stderr)
                time.sleep(wait_time)
                continue

            # Final failure after all retries
            print(f"[ERROR] HTTP {response.status_code} for {url} after {self.retries} attempts: "
                  f"{response.text[:120]}", file=sys.stderr)
            time.sleep(self.sleep_s)
            return None
