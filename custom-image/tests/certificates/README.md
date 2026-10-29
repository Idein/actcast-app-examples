# Public CA test fixtures

Copied from Idein/actcast-accounting `tests/certificates` at commit
`9042862e76f97574f498cce2595364af9a1bd0f8` (PBI-3365).
These are public certificates only, with no compromised private keys or generated
leaf certificates. The six intermediate certificates originate from
[Mozilla attachment 9664067](https://bugzilla.mozilla.org/attachment.cgi?id=9664067).

The test checks both the OS/Python and pip vendored stores, excludes the two
affected roots, and retains Amazon Root CA 1. Each cross-signed intermediate must
fail with OpenSSL error 20 (unknown issuer), rather than an unrelated expiry error.
Fixtures are mounted read-only for testing and are not copied into published images.
