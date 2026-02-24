"""
In-memory rate limiter and account lockout for security hardening.
No external dependencies (no Redis needed).

- Login rate limit: max 5 attempts per IP per 15 minutes
- Account lockout: lock after 5 failed attempts for 15 minutes
- General API rate limit: max 100 requests per minute per IP
"""
import time
import logging
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Configuration
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 900  # 15 minutes
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes
API_MAX_REQUESTS = 100
API_WINDOW_SECONDS = 60  # 1 minute


class RateLimiter:
    """Thread-safe in-memory rate limiter."""

    def __init__(self):
        # {ip: [(timestamp, ...),]} for login attempts
        self._login_attempts: dict[str, list[float]] = defaultdict(list)
        # {username: [(timestamp, ...),]} for failed login tracking
        self._failed_logins: dict[str, list[float]] = defaultdict(list)
        # {username: lockout_until_timestamp}
        self._locked_accounts: dict[str, float] = {}
        # {ip: [(timestamp, ...),]} for general API rate limiting
        self._api_requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _cleanup_old_entries(self, entries: list[float], window: int) -> list[float]:
        """Remove entries older than the window."""
        cutoff = time.time() - window
        return [t for t in entries if t > cutoff]

    # ==========================================
    # Login Rate Limiting (by IP)
    # ==========================================

    def check_login_rate_limit(self, ip: str) -> tuple[bool, int]:
        """
        Check if an IP is within login rate limits.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        with self._lock:
            now = time.time()
            self._login_attempts[ip] = self._cleanup_old_entries(
                self._login_attempts[ip], LOGIN_WINDOW_SECONDS
            )

            if len(self._login_attempts[ip]) >= LOGIN_MAX_ATTEMPTS:
                oldest = self._login_attempts[ip][0]
                retry_after = int(oldest + LOGIN_WINDOW_SECONDS - now)
                logger.warning(
                    "Rate limit exceeded for IP %s (%d attempts in %ds)",
                    ip, len(self._login_attempts[ip]), LOGIN_WINDOW_SECONDS
                )
                return False, max(retry_after, 1)

            return True, 0

    def record_login_attempt(self, ip: str):
        """Record a login attempt for rate limiting."""
        with self._lock:
            self._login_attempts[ip].append(time.time())

    # ==========================================
    # Account Lockout (by username)
    # ==========================================

    def is_account_locked(self, username: str) -> tuple[bool, int]:
        """
        Check if an account is locked out.
        Returns: (locked: bool, retry_after_seconds: int)
        """
        with self._lock:
            lockout_until = self._locked_accounts.get(username)
            if lockout_until and time.time() < lockout_until:
                retry_after = int(lockout_until - time.time())
                return True, max(retry_after, 1)

            # Clean up expired lockout
            if lockout_until:
                del self._locked_accounts[username]

            return False, 0

    def record_failed_login(self, username: str):
        """Record a failed login attempt. Locks account after threshold."""
        with self._lock:
            now = time.time()
            self._failed_logins[username] = self._cleanup_old_entries(
                self._failed_logins[username], LOGIN_WINDOW_SECONDS
            )
            self._failed_logins[username].append(now)

            if len(self._failed_logins[username]) >= LOGIN_MAX_ATTEMPTS:
                self._locked_accounts[username] = now + LOCKOUT_DURATION_SECONDS
                self._failed_logins[username] = []
                logger.warning(
                    "Account '%s' locked for %d seconds after %d failed attempts",
                    username, LOCKOUT_DURATION_SECONDS, LOGIN_MAX_ATTEMPTS
                )

    def clear_failed_logins(self, username: str):
        """Clear failed login history on successful login."""
        with self._lock:
            self._failed_logins.pop(username, None)
            self._locked_accounts.pop(username, None)

    # ==========================================
    # General API Rate Limiting (by IP)
    # ==========================================

    def check_api_rate_limit(self, ip: str) -> tuple[bool, int]:
        """
        Check if an IP is within general API rate limits.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        with self._lock:
            now = time.time()
            self._api_requests[ip] = self._cleanup_old_entries(
                self._api_requests[ip], API_WINDOW_SECONDS
            )

            if len(self._api_requests[ip]) >= API_MAX_REQUESTS:
                oldest = self._api_requests[ip][0]
                retry_after = int(oldest + API_WINDOW_SECONDS - now)
                return False, max(retry_after, 1)

            self._api_requests[ip].append(now)
            return True, 0


# Singleton instance
rate_limiter = RateLimiter()
