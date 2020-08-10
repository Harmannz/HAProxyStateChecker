# HAProxy Check Server State

![.github/workflows/test.yml](https://github.com/Harmannz/HAProxyStateChecker/workflows/.github/workflows/test.yml/badge.svg)

Helper script to verify state of HAProxy backend servers.
Use this to verify the state of HAProxy backends after you drain or enable it in your pipeline.

HAProxy typically has multiple backends which contain pool of servers to load-balance requests. 
![Haproxy Stats Page](https://cdn.haproxy.com/wp-content/uploads/2019/05/haproxy_stats.png)

To deploy to a particular server, sysadmins need to drain the server of incoming requests before deploy the changes (applicable if you are not on k8s yet).
This manual step can be automated by enabling Unix socket commands or through rest api in recent HAProxy versions.

This repo relies on Unix socket commands being enable, it can easily be refactored to work with REST API.

A typical workflow would look like the following:

You are deploying to ServerX

Step 1.
    Drain ServerX in haproxy via socat command/rest api
    
Step 2. 
    Verify ServerX backend server is drained
    
Step 3. 
    Tear down and/or deploy ServerX
    
Step 4. 
    Enable ServiceX in haproxy via socat command/rest api
    

The check server state script is intented to live in the same place that has HAProxy and is called by CI/CD pipeline e.g. Jenkins to validate servers are drained/enabled.

The script can live elsewhere if REST API is used to communicate with HAPRoxy. The design depends on the nature of your project and deployment patterns. Socat works nicely if you use CHEF as chef-client runs directly on the target node.    
 
