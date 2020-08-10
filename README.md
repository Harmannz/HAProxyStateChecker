# HAProxy Check Server State

Helper script to verify state of HAProxy backends

use this to verify the state of HAProxy backends after you drain or enable it in your pipeline.


E.g.
You are deploying servicex

Step 1.
drain servicex in haproxy via socat command

step 2. verify servicex backend is drained

step 3. tear down then deploy servicex

step 4. enable servicex in haproxy 
