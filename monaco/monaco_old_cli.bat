set $tenant1$-token=$entity_token1$
set $tenant2$-token=$entity_token2$
set $tenant3$-token=$entity_token3$

set MONACO_REQUEST_LOG=request.log 
set MONACO_RESPONSE_LOG=response.log 

monaco-windows-4.0-386.exe %*

