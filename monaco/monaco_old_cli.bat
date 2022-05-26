set $tenant1$-token=$monaco_token1$
set $tenant3$-token=$monaco_token3$
set $tenant2$-token=$monaco_token2$

set MONACO_REQUEST_LOG=request.log 
set MONACO_RESPONSE_LOG=response.log 

monaco-windows-4.0-386.exe %*

