# Methods of query 

All functions to query have a parameter `method` that can be `sync` or `async`. You should choose the method according to the query you want to perform.


## sync
Synchronous (sync) queries block execution until the query completes and returns the result immediately. This mode is best for quick queries with small datasets where you expect an almost instantaneous response.

## async
Asynchronous (async) queries submit the query and immediately return a job identifier. You can then poll or wait for the query to finish and retrieve the results later. This mode is ideal for long-running or resource-intensive queries, large datasets, or when you want to avoid blocking your application.