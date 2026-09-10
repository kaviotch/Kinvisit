supabase-js v2.45.4, MIT licence, vendored from cdn.jsdelivr.net so that
script-src can stay 'self'. Portal pages hold a session; a third party script
host is a third party who can take it. Replace by refetching the same pinned
version, never by pointing a script tag at a CDN.
