# Onboarding Guide

## Create your workspace
Sign up with a work email, verify it, and choose a region. The region cannot be changed later because data residency is fixed at creation time.

## Create an API key
Open Settings > API Keys and click New Key. Keys are shown once. Store them in a secret manager. Keys can be scoped to read-only or read-write.

## First request
Send a POST request to /v1/query with your key in the Authorization header. A successful call returns HTTP 200 and a JSON body with a request_id.

## Team roles
There are three roles. Owner can manage billing and delete the workspace. Admin can manage members and keys. Member can use keys but not create them.

## Single sign-on
SSO via SAML 2.0 is available on the Enterprise plan only. SCIM user provisioning is also Enterprise only.

## Getting help
Free plan users get community support. Pro users get email support with a 24 hour response target. Enterprise users get a 1 hour response target for severity 1 issues and a named engineer.
