package middleware

import (
	"net/http"
)

const defaultMaxBodyBytes = 1 << 20 // 1 MiB — tune per endpoint if needed

// SecurityMiddleware applies defence-in-depth HTTP protections required for
// banking-grade and PCI-DSS compliant services:
//
//   - Body size limit: prevents resource-exhaustion / DoS via large payloads.
//   - Security headers: standard set recommended by OWASP and financial regulators.
//     Adjust CSP and HSTS values to match your deployment (TLS termination, CDN, etc.).
func SecurityMiddleware(maxBodyBytes int64) func(http.Handler) http.Handler {
	if maxBodyBytes <= 0 {
		maxBodyBytes = defaultMaxBodyBytes
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// ── Body size limit ───────────────────────────────────────────────
			// Must be applied BEFORE any handler reads the body.
			// Without this, a malicious client can upload arbitrarily large payloads,
			// exhausting memory and causing service degradation.
			r.Body = http.MaxBytesReader(w, r.Body, maxBodyBytes)

			// ── Security response headers ─────────────────────────────────────
			h := w.Header()

			// Prevents MIME-type sniffing attacks (browsers must respect Content-Type).
			h.Set("X-Content-Type-Options", "nosniff")

			// Prevents the response from being loaded inside a <frame>/<iframe>,
			// mitigating clickjacking attacks.
			h.Set("X-Frame-Options", "DENY")

			// Tells browsers to use HTTPS for at least 1 year, including subdomains.
			// Only effective when the service is served over TLS.
			h.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

			// Restricts browser features (camera, microphone, etc.).
			h.Set("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

			// Referrer policy — do not leak URL info to third-party endpoints.
			h.Set("Referrer-Policy", "strict-origin-when-cross-origin")

			// Content-Security-Policy: restrict to same origin (APIs typically don't
			// serve HTML, but the header is still a defence against browsers
			// that might render a JSON-as-HTML edge case).
			h.Set("Content-Security-Policy", "default-src 'none'")

			// Remove the server banner to avoid fingerprinting.
			h.Set("Server", "")

			next.ServeHTTP(w, r)
		})
	}
}
