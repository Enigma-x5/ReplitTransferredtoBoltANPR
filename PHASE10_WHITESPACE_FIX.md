# Phase 10 Update: Remote Inference URL Whitespace Bug Fix

## Problem

The REMOTE_INFERENCE_URL in `.replit` had a trailing space:
```
REMOTE_INFERENCE_URL = "https://quick-institutions-assistance-write.trycloudflare.com "
                                                                                      ^
                                                                              trailing space!
```

This caused DNS lookup failures because the HTTP client tried to connect to a hostname with a trailing space, which is invalid.

## Solution

Applied defense-in-depth fixes at multiple layers:

### 1. Fixed `.replit` Configuration

**Before:**
```toml
REMOTE_INFERENCE_URL = "https://quick-institutions-assistance-write.trycloudflare.com "
```

**After:**
```toml
REMOTE_INFERENCE_URL = "https://declined-giants-covers-frederick.trycloudflare.com"
```

Changes:
- Removed trailing space
- Updated to new CloudFlare tunnel URL

### 2. Added Defensive Validation in `src/config.py`

Added a Pydantic field validator to automatically strip whitespace:

```python
from pydantic import field_validator

@field_validator('REMOTE_INFERENCE_URL', mode='before')
@classmethod
def strip_remote_inference_url(cls, v):
    """Strip whitespace from REMOTE_INFERENCE_URL to prevent DNS lookup failures."""
    if isinstance(v, str):
        return v.strip()
    return v
```

**Why this helps:**
- Protects against copy-paste errors
- Handles environment variables with accidental whitespace
- Future-proof against manual edits
- No performance impact (runs once at startup)

### 3. Added Whitespace Visibility in `src/detectors/remote_inference.py`

Added `url_repr` to all URL logging statements:

```python
logger.info(
    "REMOTE_DETECTOR_INIT",
    url=self.inference_url,
    url_repr=repr(self.inference_url),  # <-- Shows quotes and whitespace
    auth_configured=bool(self.auth_token)
)
```

**Before (hidden whitespace):**
```json
{"url": "https://example.com ", "event": "REMOTE_DETECTOR_INIT"}
```

**After (visible whitespace):**
```json
{"url": "https://example.com ", "url_repr": "'https://example.com '", "event": "REMOTE_DETECTOR_INIT"}
```

The `url_repr` field shows the Python representation with quotes, making trailing/leading spaces immediately visible in logs.

## Testing

### Verify .replit has no trailing space
```bash
grep "REMOTE_INFERENCE_URL" .replit | cat -A
# Should show: REMOTE_INFERENCE_URL = "https://declined-giants-covers-frederick.trycloudflare.com"$
# The $ at the end confirms no trailing space
```

### Verify config validator strips whitespace
```python
# In Python REPL or worker startup:
from src.config import settings
print(f"URL: [{settings.REMOTE_INFERENCE_URL}]")
print(f"Repr: {repr(settings.REMOTE_INFERENCE_URL)}")
# Should show no spaces in brackets
```

### Verify logging exposes whitespace
```bash
# In worker logs, look for:
REMOTE_DETECTOR_INIT url=https://... url_repr='https://...'
# If there's a trailing space, url_repr will show: 'https://... '
```

## Log Examples

### Correct (No Whitespace)
```json
{
  "event": "REMOTE_DETECTOR_INIT",
  "url": "https://declined-giants-covers-frederick.trycloudflare.com",
  "url_repr": "'https://declined-giants-covers-frederick.trycloudflare.com'",
  "auth_configured": false
}
```

### Bug (With Whitespace) - Now Prevented
```json
{
  "event": "REMOTE_DETECTOR_INIT",
  "url": "https://declined-giants-covers-frederick.trycloudflare.com ",
  "url_repr": "'https://declined-giants-covers-frederick.trycloudflare.com '",
  "auth_configured": false
}
```

Notice how `url_repr` shows the trailing space inside the quotes.

## Defense Layers

1. **Prevention**: Fixed .replit to not have whitespace
2. **Detection**: Added repr() logging to expose whitespace if it occurs
3. **Mitigation**: Added validator to automatically strip whitespace

This triple-layer approach ensures:
- The bug is fixed immediately
- Future whitespace issues are caught in logs
- Automatic recovery if whitespace sneaks in

## Files Modified

1. `.replit` - Fixed URL, removed trailing space
2. `src/config.py` - Added field_validator to strip REMOTE_INFERENCE_URL
3. `src/detectors/remote_inference.py` - Added url_repr to all URL logging

## Migration Notes

**No action required for existing deployments** - all changes are backward compatible:
- The validator only strips whitespace (doesn't change valid URLs)
- The url_repr field is additional logging (doesn't break anything)
- The .replit change is env-specific (doesn't affect Docker/production)

## Related Issues

This fix addresses:
- DNS lookup failures with "Name or service not known"
- Timeout errors due to invalid hostname
- Silent failures from trailing whitespace
- Debugging difficulty when whitespace is invisible

## Prevention Tips

1. **When editing .replit**: Use an editor that shows trailing spaces (VS Code, vim with :set list)
2. **When copying URLs**: Always copy without selecting trailing whitespace
3. **When debugging**: Check url_repr in logs first if seeing DNS errors
4. **When adding new URL configs**: Consider adding similar validators

## Verification Checklist

After deploying this fix, verify:
- [ ] `.replit` has REMOTE_INFERENCE_URL without trailing space
- [ ] Worker logs show `url_repr` matching `url` exactly (no extra spaces in quotes)
- [ ] Health check passes (confirms URL is valid)
- [ ] Video uploads succeed (confirms inference endpoint is reachable)

If url_repr shows extra spaces, the validator should strip them automatically, but investigate why they're present in the environment.
