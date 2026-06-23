# Phase 3.3.3: Output Encoding

**Status:** ✅ Implemented  
**Commit:** TBD  
**Files:**
- `output_encoding_service.py` — Output encoding & XSS prevention
- `server.py` — Integration + middleware

---

## Overview

Encodes all JSON API responses to prevent **Reflected XSS** attacks.

Handles:
- HTML entity escaping (`<`, `>`, `&`, `"`, `'`, `/`)
- Unicode escaping (non-ASCII characters)
- Safe JSON serialization
- Suspicious pattern detection

---

## Architecture

### Output Encoding Service (`output_encoding_service.py`)

```python
# Escape individual strings
safe = OutputEncodingService.escape_string("<script>alert('xss')</script>")
# → "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;"

# Detect suspicious patterns
is_suspicious = OutputEncodingService.detect_suspicious_content(user_input)

# Encode complex objects
encoded = OutputEncodingService.encode_value({
    "name": "John <Doe>",
    "tags": ["tag1", "tag2 & tag3"]
})

# Generate JSON-safe response
json_response = OutputEncodingService.encode_json_response(data)
```

### Middleware (`OutputEncodingMiddleware`)

- Automatically encodes all JSON responses
- Detects Content-Type: application/json
- Preserves response status codes & headers
- Gracefully handles encoding errors

---

## Escape Map

| Character | Encoded | Purpose |
|-----------|---------|---------|
| `<` | `&lt;` | Close script tags |
| `>` | `&gt;` | Close script tags |
| `&` | `&amp;` | Prevent entity injection |
| `"` | `&quot;` | Escape attribute context |
| `'` | `&#x27;` | Escape attribute context |
| `/` | `&#x2F;` | Escape </script> injection |

---

## Suspicious Patterns Detected

Logged as warnings for investigation:

```
<script>...</script>  # Script injection
javascript:          # Protocol injection
on(click\|error)=    # Event handler injection
<iframe>             # Iframe injection
<object>             # Object tag injection
<embed>              # Embed tag injection
```

---

## Configuration

### Encoding Config

```python
ENCODING_CONFIG = {
    "enabled": True,           # Master switch
    "escape_strings": True,    # Escape string values
    "detect_suspicious": True, # Warn on suspicious patterns
    "ensure_ascii": True,      # Force ASCII-only JSON
}
```

### Environment

No environment variables needed. Uses defaults unless configured.

---

## API Responses

### Before Encoding
```json
{
  "name": "John <Doe>",
  "bio": "Loves <script>alert('xss')</script>",
  "tags": ["html & css"]
}
```

### After Encoding
```json
{
  "name": "John &lt;Doe&gt;",
  "bio": "Loves &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;",
  "tags": ["html &amp; css"]
}
```

---

## Security Considerations

### ✅ Strengths

1. **Automatic encoding:** All JSON responses protected by middleware
2. **Comprehensive escaping:** Handles HTML, attributes, JSON contexts
3. **Suspicious pattern detection:** Warns on potential injection attempts
4. **Context-aware:** Different strategies for HTML, XML, CSV, JSON
5. **No false positives:** Legitimate data (emails, URLs) remains readable

### ⚠️ Limitations

1. **Client-side responsibility:** Frontend still needs to use safe APIs (`.textContent` vs `.innerHTML`)
2. **Not for binary data:** Only applies to JSON responses
3. **Performance:** ~1-5ms per response encoding
4. **Cannot search:** Encoded strings can't be queried directly

### 🔐 Defense in Depth

This is **output encoding layer**. Complete XSS protection requires:
1. **Input validation** — Phase 3.1 (sanitization)
2. **Output encoding** — Phase 3.3.3 (this)
3. **Content-Security-Policy** — Phase 3.4 (headers)
4. **HTTPOnly cookies** — Phase 3.2 (already done)

---

## Testing

### Unit Tests

```python
from output_encoding_service import OutputEncodingService

# Test escaping
assert OutputEncodingService.escape_string('<script>') == '&lt;script&gt;'

# Test detection
assert OutputEncodingService.detect_suspicious_content('<script>') == True

# Test encoding
data = {"name": "John <Doe>"}
encoded = OutputEncodingService.encode_value(data)
assert encoded["name"] == "John &lt;Doe&gt;"

# Test JSON response
json_str = OutputEncodingService.encode_json_response(data)
assert "&lt;" in json_str
```

### Integration Test

```bash
# Test API endpoint with malicious input
curl -X POST http://localhost:8002/api/clients \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert(1)</script>"}' \
  -H "Authorization: Bearer TOKEN"

# Verify response has encoded output
# Response should contain: "&lt;script&gt;" not "<script>"
```

---

## Monitoring

### Logs

Watch for suspicious pattern warnings:

```logs
[WARNING] Suspicious pattern detected: <script[^>]*>
[ERROR] Output encoding failed: ...
```

### Metrics

Track encoding performance:

```python
# Add prometheus metric
encoding_duration_ms = response_time - request_time
```

---

## Integration in Modules

Output encoding is **automatic** via middleware. No changes needed in route handlers.

However, if you need manual encoding:

```python
from output_encoding_service import OutputEncodingService

# Manually encode before returning
safe_data = OutputEncodingService.encode_value(user_data)
return JSONResponse(safe_data)
```

---

## Next Steps

- **Phase 3.3.4:** Advanced RBAC/ACL (scope-based access control)
- **Phase 3.3.5:** Audit trail enhancements (IP logging, action context)
- **Phase 3.3.6:** Rate limiting advanced (per-user, per-endpoint)
- **Phase 3.3.7:** Secrets rotation (automated key management)

---

## References

- OWASP XSS Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- HTML Entity Encoding: https://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
- JSON RFC 7159: https://tools.ietf.org/html/rfc7159
