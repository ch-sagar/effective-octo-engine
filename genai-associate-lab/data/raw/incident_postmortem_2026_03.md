# Incident Postmortem 2026-03

## Summary
On 12 March 2026 the query API returned elevated 503 errors for 47 minutes between 09:14 and 10:01 UTC.

## Root cause
A configuration change reduced the connection pool size on the gateway tier from 400 to 40. Traffic spikes exhausted the pool.

## Customer impact
About 3% of requests failed. Customers on the Enterprise plan received service credits of 10% of their monthly fee.

## Contacts (internal)
Incident commander: Priya Raman, priya.raman@nimbuscloud.example, +91 98765 43210.
Customer liaison: Daniel Ortiz, daniel.ortiz@nimbuscloud.example, +1 415 555 0134.
Bridge host: 10.24.8.17

## Follow-ups
Add a canary stage for gateway configuration changes. Add an alert on pool saturation above 80%.
