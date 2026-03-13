An authentication service issues and validates signed tokens. Implement a token validator with strict security requirements. The authentication specification is in `/app/input_files/auth_spec.txt` and sample configuration in `/app/input_files/sample_config.json`.

A scaffold file is provided at `/app/input_files/auth_validator.py`. Complete the implementation and place the finished file at `/app/auth_validator.py`.

Requirements:
- Use HMAC-SHA256 for signing
- Support `exp`, `nbf`, `iss`, `aud`, and `sub` standard claims
- `exp` and `nbf` are time-based claims: validate them only if they are present in the payload; do not raise an error if they are absent
- `iss`, `aud`, and `sub` are always required: raise the appropriate error if any of them is missing or invalid
- The `sub` claim must be a non-empty string with no null (`\x00`) characters
- Implement 5-second clock skew tolerance for `exp` and `nbf`
- Use constant-time comparison to prevent timing attacks